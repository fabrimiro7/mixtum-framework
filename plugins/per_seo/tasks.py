import asyncio
from celery import shared_task

from plugins.per_seo.crawler.runner import run_crawl


@shared_task
def run_site_crawl(run_id: int, site_id: int, sitemap_url: str | None = None, overrides: dict | None = None) -> None:
    asyncio.run(run_crawl(run_id=run_id, site_id=site_id, sitemap_url=sitemap_url, overrides=overrides))
