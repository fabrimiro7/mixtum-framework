from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Set

import httpx
from asgiref.sync import sync_to_async
from django.db import transaction

from plugins.per_seo.config import load_config
from plugins.per_seo.scraper.analyzer import analyze_page
from plugins.per_seo.scraper.sitemap import collect_urls
from plugins.per_seo.models import Page, PageIssue, Run, Site, SiteSitemap


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _count_severity(issues: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"critical": 0, "warning": 0, "info": 0}
    for issue in issues:
        severity = issue.get("severity")
        if severity in counts:
            counts[severity] += 1
    return counts


@sync_to_async
@transaction.atomic
def _record_page(
    run_id: int,
    site_id: int,
    url: str,
    lastmod: Optional[str],
    metrics: Dict[str, Any],
    sitemap_url: Optional[str],
) -> None:
    issues = metrics.get("issues", [])
    diagnostics_json = json.dumps(issues)
    issues_count = len(issues)
    page = Page.objects.create(
        run_id=run_id,
        site_id=site_id,
        url=url,
        lastmod=lastmod,
        status_code=metrics.get("status_code"),
        word_count=metrics.get("word_count"),
        response_time_ms=metrics.get("response_time_ms"),
        issues_count=issues_count,
        diagnostics_json=diagnostics_json,
        sitemap_url=sitemap_url,
        updated_at=_now_iso(),
    )

    now = _now_iso()
    previous_issues = PageIssue.objects.filter(
        site_id=site_id,
        page_url=url,
        resolved_at__isnull=True,
    ).values_list("issue_code", flat=True).distinct()
    previous_issue_codes = set(previous_issues)

    new_issue_codes = {issue.get("code") for issue in issues if issue.get("code")}
    resolved_codes = previous_issue_codes - new_issue_codes
    for code in resolved_codes:
        latest = PageIssue.objects.filter(
            site_id=site_id,
            page_url=url,
            issue_code=code,
            resolved_at__isnull=True,
        ).order_by("-detected_at").first()
        if latest:
            latest.resolved_at = now
            latest.save(update_fields=["resolved_at"])

    for issue in issues:
        PageIssue.objects.create(
            run_id=run_id,
            site_id=site_id,
            page_id=page.id,
            page_url=url,
            issue_code=issue.get("code") or "",
            severity=issue.get("severity") or "info",
            message=issue.get("message") or "",
            detected_at=now,
            resolved_at=None,
        )


@sync_to_async
def _finish_run(run_id: int, status: str, total_urls: int, issues_summary: Dict[str, int]) -> None:
    Run.objects.filter(id=run_id).update(
        finished_at=_now_iso(),
        status=status,
        total_urls=total_urls,
        issues_summary=json.dumps(issues_summary),
    )


async def _collect_urls(
    sitemaps: List[str],
    client: httpx.AsyncClient,
    depth: int,
) -> List[Dict[str, Any]]:
    collected: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for sitemap_url in sitemaps:
        try:
            urls = await collect_urls(sitemap_url, client, depth)
        except Exception:
            continue
        for url in urls:
            loc = url.get("loc")
            if not loc or loc in seen:
                continue
            seen.add(loc)
            collected.append(url)
    return collected


async def run_crawl(
    run_id: int,
    site_id: int,
    sitemap_url: Optional[str] = None,
    overrides: Optional[Dict[str, Any]] = None,
) -> None:
    config = load_config().override(**(overrides or {}))
    site = await sync_to_async(Site.objects.filter(id=site_id).first)()
    if site is None:
        await _finish_run(run_id, "error", 0, {})
        return

    if sitemap_url:
        sitemaps = [sitemap_url]
    else:
        sitemaps_qs = SiteSitemap.objects.filter(site_id=site_id).values_list("sitemap_url", flat=True)
        sitemaps = list(await sync_to_async(list)(sitemaps_qs))

    if not sitemaps:
        await _finish_run(run_id, "error", 0, {})
        return

    issues_summary: Dict[str, int] = {"critical": 0, "warning": 0, "info": 0}

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(config.timeout, read=config.timeout),
            headers={"User-Agent": config.user_agent},
        ) as client:
            urls = await _collect_urls(sitemaps, client, config.sitemap_depth)
            semaphore = asyncio.Semaphore(config.concurrency)
            summary_lock = asyncio.Lock()

            async def process(entry: Dict[str, Any]) -> None:
                async with semaphore:
                    metrics = await analyze_page(entry["loc"], client, config.retries)
                    async with summary_lock:
                        for sev, count in (metrics.get("severity_counts") or {}).items():
                            if sev in issues_summary:
                                issues_summary[sev] += count
                    await _record_page(
                        run_id,
                        site_id,
                        entry["loc"],
                        entry.get("lastmod"),
                        metrics,
                        entry.get("sitemap_url"),
                    )

            tasks = [process(entry) for entry in urls]
            if tasks:
                await asyncio.gather(*tasks)
            await _finish_run(run_id, "completed", len(urls), issues_summary)
    except Exception:
        await _finish_run(run_id, "error", 0, issues_summary)
