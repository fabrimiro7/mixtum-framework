# cat_client.py
import json
import time
import threading
from queue import Queue, Empty
from typing import Optional, Dict, Any, Generator, List

import websocket  # pip install websocket-client


class CatWSClient:
    """
    Client WebSocket per Cheshire Cat lato server (Django).
    Offre:
      - connect()/close()
      - chat_once(message): restituisce il finale (type == 'chat')
      - chat_stream(message): generator che emette eventi (frammenti/partial e poi 'chat' finale)
    """

    def __init__(
        self,
        url: str,
        token: Optional[str] = None,
        connect_timeout: int = 30,
        ping_interval: int = 20,
        ping_timeout: int = 10,
    ):
        self.url = url
        self.token = token
        self.connect_timeout = connect_timeout
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        self.ws: Optional[websocket.WebSocketApp] = None
        self._opened = threading.Event()
        self._closed = threading.Event()
        self._last_error: Optional[Exception] = None
        self.recv_queue: "Queue[Dict[str, Any]]" = Queue()

    # --- callbacks ---
    def _on_open(self, _ws):
        self._opened.set()

    def _on_message(self, _ws, message: str):
        try:
            data = json.loads(message)
        except Exception:
            data = {"type": "raw", "content": message}
        self.recv_queue.put(data)

    def _on_error(self, _ws, error: Exception):
        self._last_error = error
        self.recv_queue.put({"type": "error", "content": str(error)})

    def _on_close(self, _ws, _status_code, _msg):
        self._closed.set()

    # --- API ---
    def connect(self):
        headers = []
        if self.token:
            headers.append(f"Authorization: Bearer {self.token}")

        self.ws = websocket.WebSocketApp(
            self.url,
            header=headers,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        t = threading.Thread(
            target=self.ws.run_forever,
            kwargs={"ping_interval": self.ping_interval, "ping_timeout": self.ping_timeout},
            daemon=True,
        )
        t.start()

        # Attendi apertura o errore
        start = time.time()
        while not self._opened.is_set():
            if self._last_error:
                raise self._last_error
            if time.time() - start > self.connect_timeout:
                raise TimeoutError(f"Connessione a {self.url} scaduta.")
            time.sleep(0.02)

    def close(self):
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass

    def send_human(self, text: str):
        if not self.ws:
            raise RuntimeError("WebSocket non inizializzato.")
        self.ws.send(json.dumps({"text": text}))

    def chat_once(self, message: str, drain_seconds: float = 0.15) -> Dict[str, Any]:
        """
        Invia 'message' e attende l'evento finale (type == 'chat').
        Restituisce un dict con:
            {
              "final": "<testo finale>",
              "events": [<tutti gli eventi ricevuti>]
            }
        """
        self.send_human(message)
        events: List[Dict[str, Any]] = []
        final_text: str = ""

        # Consuma finché non arriva 'chat'
        while True:
            item = self._next_event(timeout=30)
            if item is None:  # timeout
                break
            events.append(item)

            if item.get("type") == "chat":
                final_text = str(item.get("content") or "")
                break

        # piccolo drain
        end = time.time() + drain_seconds
        while time.time() < end:
            item = self._next_event(timeout=drain_seconds)
            if item is None:
                break
            events.append(item)

        return {"final": final_text, "events": events}

    def chat_stream(self, message: str, drain_seconds: float = 0.15) -> Generator[Dict[str, Any], None, None]:
        """
        Generator che emette gli eventi come dict:
          - frammenti: type in {"stream","partial","token","chunk",None}
          - finale: type == "chat"
          - eventuali 'error'/'info'
        """
        self.send_human(message)

        end_seen = False
        while True:
            item = self._next_event(timeout=30)
            if item is None:
                break
            yield item
            if item.get("type") == "chat":
                end_seen = True
                break

        # drain finale
        if end_seen:
            end = time.time() + drain_seconds
            while time.time() < end:
                item = self._next_event(timeout=drain_seconds)
                if item is None:
                    break
                yield item

    def _next_event(self, timeout: float) -> Optional[Dict[str, Any]]:
        try:
            return self.recv_queue.get(timeout=timeout)
        except Empty:
            return None
