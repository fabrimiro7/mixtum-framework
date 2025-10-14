from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EmailTemplateViewSet, EmailViewSet

router = DefaultRouter()
router.register(r"email-templates", EmailTemplateViewSet, basename="emailtemplate")
router.register(r"emails", EmailViewSet, basename="email")

urlpatterns = [
    path("", include(router.urls)),
]
