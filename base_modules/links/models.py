from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


# Keep labels explicit and stable for integrations/filters.
LINK_LABEL_CHOICES = (
    ("google_drive", "Google Drive"),
    ("figma", "Figma"),
    ("google_doc", "Google Doc"),
    ("google_spreadsheet", "Google Spreadsheet"),
    ("github", "GitHub"),
    ("wetransfer", "WeTransfer"),
    ("altro", "Altro"),
)


class Link(models.Model):
    """
    Generic link attachable to any model via GenericForeignKey.
    Example targets: Project, Ticket, Task, Workspace, ...
    """

    # Business fields
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    url = models.URLField(max_length=1000)
    label = models.CharField(max_length=50, choices=LINK_LABEL_CHOICES, default="altro", db_index=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="links")
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Link"
        verbose_name_plural = "Links"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["label"]),
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} · {self.get_label_display()}"

    def short_target(self) -> str:
        return f"{self.content_type.app_label}.{self.content_type.model}#{self.object_id}"
