"""
URL configuration for the documents plugin.

All endpoints are registered under the ``/api/documents/`` prefix
(configured in ``mixtum_core/urls.py``).
"""

from rest_framework.routers import DefaultRouter

from .views import (
    BlockViewSet,
    DocumentCategoryViewSet,
    DocumentBlockViewSet,
    DocumentSignerViewSet,
    DocumentStatusViewSet,
    DocumentTemplateViewSet,
    DocumentTemplateBlockViewSet,
    DocumentTypeViewSet,
    DocumentViewSet,
    PartyViewSet,
)

router = DefaultRouter()
router.register(r"types", DocumentTypeViewSet, basename="document-type")
router.register(r"categories", DocumentCategoryViewSet, basename="document-category")
router.register(r"statuses", DocumentStatusViewSet, basename="document-status")
router.register(r"blocks", BlockViewSet, basename="block")
router.register(r"templates", DocumentTemplateViewSet, basename="document-template")
router.register(r"template-blocks", DocumentTemplateBlockViewSet, basename="document-template-block")
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"document-blocks", DocumentBlockViewSet, basename="document-block")
router.register(r"parties", PartyViewSet, basename="party")
router.register(r"document-signers", DocumentSignerViewSet, basename="document-signer")

urlpatterns = router.urls
