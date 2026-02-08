# integrations/n8n/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import N8nViewSet

router = DefaultRouter()
router.register(r"", N8nViewSet, basename="n8n")

urlpatterns = [
    path("", include(router.urls)),
]
