import os
from dataclasses import asdict, dataclass, replace
from typing import Any, Dict


@dataclass(frozen=True)
class CrawlConfig:
    concurrency: int
    timeout: float
    retries: int
    user_agent: str
    sitemap_depth: int

    def override(self, **values: Any) -> "CrawlConfig":
        filtered = {k: v for k, v in values.items() if v is not None}
        if not filtered:
            return self
        return replace(self, **filtered)

    def serialize(self) -> Dict[str, Any]:
        return asdict(self)


def load_config() -> CrawlConfig:
    return CrawlConfig(
        concurrency=int(os.getenv("CRAWL_CONCURRENCY", "5")),
        timeout=float(os.getenv("CRAWL_TIMEOUT", "12.0")),
        retries=int(os.getenv("CRAWL_RETRIES", "2")),
        user_agent=os.getenv("CRAWL_USER_AGENT", "OpenCode Scraper/1.0"),
        sitemap_depth=int(os.getenv("SITEMAP_MAX_DEPTH", "3")),
    )
