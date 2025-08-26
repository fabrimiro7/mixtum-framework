"""
Settings loader (modular).
Loads base modules, then optional blocks, then environment overlay (local/production).
"""

import os

# 1) Core blocks (order matters a bit: base first)
from .base import *               # Base, paths, i18n, defaults
from .db import *                 # DATABASES
from .static_media import *       # STATIC/MEDIA
from .celery_conf import *        # Celery/Beat/Results
from .email import *              # Email/TurboSMTP
from .logging_conf import *       # Logging
from .auth import *               # AUTH_USER_MODEL, DRF default auth, Allauth

# 2) Optional blocks (loaded conditionally by env flags)
# S3 storage (enable if USE_S3=1)
try:
    from .storage_s3 import *
except Exception:
    pass

# OIDC (only if AUTH_MODE=keycloak)
if AUTH_MODE == "keycloak":
    from .oidc import *

# 3) Project integrations (placeholders you can grow)
from .bedrock import *

# 4) Environment overlay
SETTINGS_ENV = os.getenv("SETTINGS_ENV", "local").lower()
if SETTINGS_ENV == "production":
    from .envs.productions import *
else:
    from .envs.local import *
