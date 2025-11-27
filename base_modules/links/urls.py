from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LinkViewSet, ContentTypeLookupView

router = DefaultRouter()
router.register(r"links", LinkViewSet, basename="link")

urlpatterns = [
    path("content-type/", ContentTypeLookupView.as_view(), name="link-content-type"),
    path("", include(router.urls)),
]
