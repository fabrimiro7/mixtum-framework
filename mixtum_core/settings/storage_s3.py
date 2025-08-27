import os


USE_S3 = os.getenv("USE_S3", "1").lower() in ("1", "true", "yes")

if USE_S3:

    AWS_S3_ACCESS_KEY_ID = os.getenv("AWS_S3_ACCESS_KEY_ID", "")
    AWS_S3_SECRET_ACCESS_KEY = os.getenv("AWS_S3_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "eu-south-1")
    AWS_S3_SIGNATURE_VERSION = os.getenv("AWS_S3_SIGNATURE_VERSION", "s3v4")
    AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", "virtual")
    AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN", "").strip()
    AWS_MEDIA_LOCATION = os.getenv("AWS_MEDIA_LOCATION", "media")
    AWS_STATIC_LOCATION = os.getenv("AWS_STATIC_LOCATION", "static")
    _endpoint = os.getenv("AWS_S3_ENDPOINT_URL", "").strip() or None

    if _endpoint:
        AWS_S3_ENDPOINT_URL = _endpoint

    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = os.getenv("AWS_QUERYSTRING_AUTH", "0").lower() in ("1", "true", "yes")
    AWS_QUERYSTRING_EXPIRE = 3600
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": os.getenv("AWS_S3_CACHE_CONTROL", "max-age=86400, s-maxage=86400, must-revalidate"),
    }

    # Merge with existing STORAGES
    STORAGES = dict(globals().get("STORAGES", {}))

    # Media -> S3
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {"location": AWS_MEDIA_LOCATION},
    }

    # MEDIA_URL
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_MEDIA_LOCATION}/"
    else:
        if _endpoint:
            MEDIA_URL = f"{_endpoint.rstrip('/')}/{AWS_STORAGE_BUCKET_NAME}/{AWS_MEDIA_LOCATION}/"
        elif AWS_S3_REGION_NAME:
            MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{AWS_MEDIA_LOCATION}/"
        else:
            MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{AWS_MEDIA_LOCATION}/"

    # Optional: static files on S3
    if os.getenv("STATIC_ON_S3", "0").lower() in ("1", "true", "yes"):
        STORAGES["staticfiles"] = {
            "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
            "OPTIONS": {"location": AWS_STATIC_LOCATION},
        }
        if AWS_S3_CUSTOM_DOMAIN:
            STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_STATIC_LOCATION}/"
        else:
            if _endpoint:
                STATIC_URL = f"{_endpoint.rstrip('/')}/{AWS_STORAGE_BUCKET_NAME}/{AWS_STATIC_LOCATION}/"
            elif AWS_S3_REGION_NAME:
                STATIC_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{AWS_STATIC_LOCATION}/"
            else:
                STATIC_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{AWS_STATIC_LOCATION}/"

    # Safety fallback if STATIC_ON_S3=0 and no staticfiles storage defined
    if "staticfiles" not in STORAGES:
        STORAGES["staticfiles"] = {
            "BACKEND": (
                "django.contrib.staticfiles.storage.StaticFilesStorage"
                if os.getenv("DEBUG", "1").lower() in ("1", "true", "yes")
                else "whitenoise.storage.CompressedManifestStaticFilesStorage"
            )
        }
