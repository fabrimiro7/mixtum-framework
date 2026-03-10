from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Set, Tuple

import httpx


async def _fetch_xml(url: str, client: httpx.AsyncClient) -> Tuple[bytes, str]:
    resp = await client.get(url, follow_redirects=True)
    resp.raise_for_status()
    return resp.content, resp.encoding or "utf-8"


def _parse_sitemap(content: bytes) -> Tuple[List[Dict[str, Any]], bool]:
    tree = ET.fromstring(content)
    is_index = tree.tag.endswith("sitemapindex")
    items: List[Dict[str, Any]] = []
    if is_index:
        for sitemap in tree.findall(".//{*}sitemap"):
            loc = sitemap.find("{*}loc")
            if loc is None or not loc.text:
                continue
            items.append({"loc": loc.text.strip()})
    else:
        for url in tree.findall(".//{*}url"):
            loc = url.find("{*}loc")
            if loc is None or not loc.text:
                continue
            lastmod = url.find("{*}lastmod")
            item: Dict[str, Any] = {"loc": loc.text.strip()}
            if lastmod is not None and lastmod.text:
                item["lastmod"] = lastmod.text.strip()
            items.append(item)
    return items, is_index


async def collect_urls(
    root_sitemap: str,
    client: httpx.AsyncClient,
    max_depth: int = 3,
) -> List[Dict[str, Any]]:
    queue: List[Tuple[str, int]] = [(root_sitemap, 0)]
    seen_sitemaps: Set[str] = set()
    collected: List[Dict[str, Any]] = []

    while queue:
        target, depth = queue.pop(0)
        if depth > max_depth or target in seen_sitemaps:
            continue
        seen_sitemaps.add(target)
        try:
            content, _ = await _fetch_xml(target, client)
        except Exception:
            continue
        entries, is_index = _parse_sitemap(content)
        if is_index:
            for entry in entries:
                queue.append((entry["loc"], depth + 1))
            await asyncio.sleep(0)
            continue
        for entry in entries:
            entry["sitemap_url"] = target
            collected.append(entry)
    return collected
