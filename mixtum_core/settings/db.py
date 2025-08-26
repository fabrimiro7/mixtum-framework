import os

if os.getenv("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "mixtumdb"),
            "USER": os.getenv("POSTGRES_USER", "mixtumuser"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "mixtumpassword"),
            "HOST": os.getenv("POSTGRES_HOST", "db"),
            "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    from .base import BASE_DIR  # local fallback
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
