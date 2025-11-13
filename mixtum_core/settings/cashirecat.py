import os

# === Cheshire Cat config ===
CAT_WS_URL = os.getenv("CAT_WS_URL",default="ws://localhost:1865/ws")   # es. wss://cat.example.com/ws
CAT_TOKEN  = os.getenv("CAT_TOKEN", default=None)                        # opzionale: bearer token
CAT_CONNECT_TIMEOUT = int(os.getenv("CAT_CONNECT_TIMEOUT", default="30"))
CAT_STREAM_DRAIN_SECONDS = float(os.getenv("CAT_STREAM_DRAIN_SECONDS", default="0.15"))