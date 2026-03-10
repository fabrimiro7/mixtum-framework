from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup


def _safe_text(element: Optional[BeautifulSoup]) -> str:
    return element.get_text(strip=True) if element else ""


def _count_words(text: str) -> int:
    return len([token for token in text.split() if token])


def _add_issue(
    issues: List[Dict[str, Any]],
    severity: str,
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    issue = {"severity": severity, "code": code, "message": message}
    if details:
        issue["details"] = details
    issues.append(issue)


def _build_severity_counts(issues: List[Dict[str, Any]]) -> Dict[str, int]:
    palette: Dict[str, int] = {"critical": 0, "warning": 0, "info": 0}
    for issue in issues:
        sev = issue.get("severity")
        if sev in palette:
            palette[sev] += 1
    return palette


async def analyze_page(
    url: str,
    client: httpx.AsyncClient,
    retries: int,
) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    status_code = None
    html = ""
    start = time.perf_counter()
    for attempt in range(retries + 1):
        try:
            resp = await client.get(url, follow_redirects=True)
            status_code = resp.status_code
            html = resp.text or ""
            break
        except httpx.RequestError as exc:
            if attempt == retries:
                _add_issue(
                    issues,
                    "critical",
                    "request-failed",
                    f"Unable to fetch page: {exc}",
                )
            await asyncio.sleep(0)
    elapsed_ms = (time.perf_counter() - start) * 1000
    soup = BeautifulSoup(html, "html.parser") if html else None

    if status_code and status_code != 200:
        _add_issue(
            issues,
            "critical",
            "status-not-200",
            f"Unexpected status code {status_code}",
        )

    title = soup.title.string.strip() if soup and soup.title and soup.title.string else ""
    if not title:
        _add_issue(
            issues,
            "critical",
            "missing-title",
            "Page is missing a title tag",
        )
    elif len(title) < 30:
        _add_issue(
            issues,
            "warning",
            "short-title",
            "Title is shorter than 30 characters",
        )
    elif len(title) > 60:
        _add_issue(
            issues,
            "warning",
            "long-title",
            "Title exceeds 60 characters",
        )

    meta_desc = soup.find("meta", attrs={"name": "description"}) if soup else None
    desc = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else ""
    if not desc:
        _add_issue(
            issues,
            "warning",
            "missing-description",
            "Meta description is missing",
        )
    elif len(desc) < 50:
        _add_issue(
            issues,
            "info",
            "short-description",
            "Meta description is shorter than 50 characters",
        )
    elif len(desc) > 160:
        _add_issue(
            issues,
            "warning",
            "long-description",
            "Meta description exceeds 160 characters",
        )

    canonical = soup.find("link", rel="canonical") if soup else None
    if not (canonical and canonical.get("href")):
        _add_issue(
            issues,
            "warning",
            "missing-canonical",
            "Canonical link missing",
        )

    headings = soup.find_all("h1") if soup else []
    if not headings:
        _add_issue(
            issues,
            "warning",
            "missing-h1",
            "No H1 heading present",
        )
    elif len(headings) > 1:
        _add_issue(
            issues,
            "info",
            "multiple-h1",
            "Multiple H1 headings found",
        )

    robots = soup.find("meta", attrs={"name": "robots"}) if soup else None
    if robots and "noindex" in (robots.get("content", "") or "").lower():
        _add_issue(
            issues,
            "info",
            "noindex-flag",
            "Page is marked as noindex",
        )

    images = soup.find_all("img") if soup else []
    images_without_alt = []
    for img in images:
        if not img.get("alt"):
            img_url = img.get("src") or img.get("data-src") or ""
            if img_url:
                if img_url.startswith("//"):
                    img_url = f"https:{img_url}"
                elif img_url.startswith("/"):
                    from urllib.parse import urljoin
                    img_url = urljoin(url, img_url)
                images_without_alt.append(img_url)

    if images_without_alt:
        _add_issue(
            issues,
            "warning",
            "images-without-alt",
            f"{len(images_without_alt)} image(s) missing alt text",
            details={"image_urls": images_without_alt},
        )

    text = _safe_text(soup.body if soup and soup.body else soup)
    word_count = _count_words(text)
    if word_count < 300:
        _add_issue(
            issues,
            "warning",
            "low-word-count",
            "Page contains fewer than 300 words",
        )

    structured_data = bool(
        soup.find_all("script", attrs={"type": "application/ld+json"}) if soup else False
    )
    if not structured_data:
        _add_issue(
            issues,
            "info",
            "missing-structured-data",
            "No JSON-LD structured-data scripts detected",
        )

    if elapsed_ms > 1500:
        _add_issue(
            issues,
            "warning",
            "slow-page",
            "Page load took longer than 1.5s",
        )

    severity_counts = _build_severity_counts(issues)
    return {
        "url": url,
        "status_code": status_code,
        "word_count": word_count,
        "response_time_ms": round(elapsed_ms, 2),
        "issues": issues,
        "severity_counts": severity_counts,
    }
