# Placeholders for external integrations you will wire in services
import os

# Example: AWS Bedrock
AWS_BEDROCK_REGION_NAME = os.getenv("AWS_BEDROCK_REGION_NAME", "")
BEDROCK_EMBEDDING_MODEL_ID = os.getenv("BEDROCK_EMBEDDING_MODEL_ID", "")

# Example: other providers (add your keys/endpoints here)
TURBOSMTP_ENABLED = os.getenv("TURBOSMTP_ENABLED", "0") in ("1", "true", "True")
