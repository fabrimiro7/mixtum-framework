# base_modules/integrations/slack/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SlackViewSet

router = DefaultRouter()
router.register(r"", SlackViewSet, basename="slack")

urlpatterns = [
    path("", include(router.urls)),
]
