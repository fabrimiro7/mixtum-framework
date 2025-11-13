# urls.py
from django.urls import path
from .views import CatChatView, CatChatStreamView

urlpatterns = [
    path("chat", CatChatView.as_view(), name="cat_chat"),
    path("stream", CatChatStreamView.as_view(), name="cat_chat_stream"),
]
