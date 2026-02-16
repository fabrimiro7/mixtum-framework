from django.urls import path
from .views import GlobalBrandingView, WorkspaceBrandingView, EffectiveBrandingView

urlpatterns = [
    path("global/", GlobalBrandingView.as_view(), name="branding-global"),
    path("workspace/<int:workspace_id>/", WorkspaceBrandingView.as_view(), name="branding-workspace"),
    path("effective/", EffectiveBrandingView.as_view(), name="branding-effective"),
]
