from django.db import models
from base_modules.workspace.models import Workspace


class BrandingSettings(models.Model):
    workspace = models.OneToOneField(
        Workspace,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="branding_settings",
    )
    colors = models.JSONField(blank=True, null=True, default=dict)
    logo_full = models.ImageField(upload_to="branding/logos/", blank=True, null=True)
    logo_compact = models.ImageField(upload_to="branding/logos/", blank=True, null=True)
    favicon = models.ImageField(upload_to="branding/favicons/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.workspace_id:
            return f"Branding for workspace {self.workspace_id}"
        return "Global branding"

    class Meta:
        verbose_name = "Branding Settings"
        verbose_name_plural = "Branding Settings"
        ordering = ["-updated_at"]
