from pathlib import Path
import os

# Avoid importing base.py here to prevent circular imports
BASE_DIR = Path(__file__).resolve().parents[2]
DEBUG = os.environ.get("DEBUG", "1").lower() in ("1", "true", "yes")

# URLs and roots
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Ensure STORAGES dict exists
STORAGES = globals().get("STORAGES", {})

# Default local file storage (will be replaced by S3 if USE_S3=1)
STORAGES.setdefault("default", {"BACKEND": "django.core.files.storage.FileSystemStorage"})

# Mandatory staticfiles storage (Django 5+)
STORAGES.setdefault(
    "staticfiles",
    {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
)
