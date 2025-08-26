import os

USE_S3 = os.getenv("USE_S3", "0") in ("1", "true", "True")
if USE_S3:
    INSTALLED_APPS += ["storages"]  # noqa: F821
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME", "")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "")
    AWS_S3_SIGNATURE_VERSION = os.getenv("AWS_S3_SIGNATURE_VERSION", "s3v4")
    AWS_S3_ADDRESSING_STYLE = os.getenv("AWS_S3_ADDRESSING_STYLE", "virtual")

    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    # Per gli statici puoi restare su WhiteNoise o passare a S3,
    # se vuoi S3 per statici:
    # STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
