# views.py
import json
from typing import Dict, Any, Iterable

from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly  # adatta come preferisci
from rest_framework.authentication import SessionAuthentication, BasicAuthentication  # o JWT

from .cat_client import CatWSClient


def _get_cat_client() -> CatWSClient:
    return CatWSClient(
        url="ws://host.docker.internal:1865/ws",
        token=getattr(settings, "CAT_TOKEN", None),
        connect_timeout=getattr(settings, "CAT_CONNECT_TIMEOUT", 30),
    )


class CatChatView(APIView):
    """
    Endpoint REST "one-shot":
      POST /api/cat/chat
      body: {"message": "..."}
      resp: {"content": "<final_text>", "events": [<eventi grezzi>]}
    """

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        message = payload.get("message") or payload.get("text")
        if not message:
            return HttpResponseBadRequest("Missing 'message'")

        client = _get_cat_client()
        try:
            client.connect()
            result = client.chat_once(
                message=message,
                drain_seconds=getattr(settings, "CAT_STREAM_DRAIN_SECONDS", 0.15),
            )
        finally:
            client.close()

        return JsonResponse(
            {
                "content": result.get("final", ""),
                "events": result.get("events", []),  # utile per debug/telemetria
            }
        )


@method_decorator(csrf_exempt, name="dispatch")
class CatChatStreamView(APIView):
    """
    Endpoint SSE (Server-Sent Events):
      POST /api/cat/chat/stream
      body: {"message": "..."}
      response: text/event-stream
        data: {"type":"token","content":"C"}
        data: {"type":"token","content":"iao"}
        ...
        data: {"type":"chat","content":"<finale>"}
    """

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")

        message = payload.get("message") or payload.get("text")
        if not message:
            return HttpResponseBadRequest("Missing 'message'")

        client = _get_cat_client()
        client.connect()

        def event_stream() -> Iterable[bytes]:
            try:
                for evt in client.chat_stream(
                    message=message,
                    drain_seconds=getattr(settings, "CAT_STREAM_DRAIN_SECONDS", 0.15),
                ):
                    # Normalizza alcuni 'type' per il front-end
                    t = evt.get("type")
                    if t in (None, "stream", "partial", "token", "chunk"):
                        norm = "token"
                    else:
                        norm = t

                    data = {"type": norm, "content": evt.get("content", "")}
                    # SSE frame
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode("utf-8")

                # opzionale: evento 'done'
                yield b"data: {\"type\":\"done\"}\n\n"
            finally:
                client.close()

        # Nota: StreamingHttpResponse mantiene la connessione aperta finché il generator produce dati.
        resp = StreamingHttpResponse(
            streaming_content=event_stream(),
            content_type="text/event-stream; charset=utf-8",
        )
        # Headers utili per SSE
        resp["Cache-Control"] = "no-cache"
        resp["X-Accel-Buffering"] = "no"  # utile dietro Nginx per disabilitare buffering
        return resp
