# Keep root package minimal; do NOT import settings blocks here.
from .celery import app as celery_app  # noqa: F401

__all__ = ("celery_app",)
