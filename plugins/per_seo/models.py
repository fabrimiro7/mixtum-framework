import json
from django.db import models


def _parse_json(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}


class Site(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    base_url = models.TextField()
    notes = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    status = models.TextField()
    created_at = models.TextField()

    class Meta:
        db_table = "sites"


class SiteSitemap(models.Model):
    id = models.AutoField(primary_key=True)
    site = models.ForeignKey(Site, db_column="site_id", on_delete=models.DO_NOTHING, related_name="sitemaps")
    sitemap_url = models.TextField()
    created_at = models.TextField()

    class Meta:
        db_table = "site_sitemaps"


class Run(models.Model):
    id = models.AutoField(primary_key=True)
    site = models.ForeignKey(Site, db_column="site_id", on_delete=models.DO_NOTHING, related_name="runs")
    started_at = models.TextField()
    finished_at = models.TextField(blank=True, null=True)
    root_url = models.TextField(blank=True, null=True)
    config_json = models.TextField()
    schedule = models.TextField(blank=True, null=True)
    status = models.TextField()
    total_urls = models.IntegerField(default=0)
    issues_summary = models.TextField(default="{}")

    class Meta:
        db_table = "runs"

    def config(self):
        return _parse_json(self.config_json)

    def summary(self):
        return _parse_json(self.issues_summary)


class Page(models.Model):
    id = models.AutoField(primary_key=True)
    run = models.ForeignKey(Run, db_column="run_id", on_delete=models.DO_NOTHING, related_name="pages")
    site = models.ForeignKey(Site, db_column="site_id", on_delete=models.DO_NOTHING, related_name="pages")
    url = models.TextField()
    lastmod = models.TextField(blank=True, null=True)
    status_code = models.IntegerField(blank=True, null=True)
    word_count = models.IntegerField(blank=True, null=True)
    response_time_ms = models.FloatField(blank=True, null=True)
    issues_count = models.IntegerField(blank=True, null=True)
    diagnostics_json = models.TextField(blank=True, null=True)
    sitemap_url = models.TextField(blank=True, null=True)
    updated_at = models.TextField()

    class Meta:
        db_table = "pages"

    def diagnostics(self):
        return _parse_json(self.diagnostics_json)


class PageIssue(models.Model):
    id = models.AutoField(primary_key=True)
    run = models.ForeignKey(Run, db_column="run_id", on_delete=models.DO_NOTHING)
    site = models.ForeignKey(Site, db_column="site_id", on_delete=models.DO_NOTHING)
    page = models.ForeignKey(Page, db_column="page_id", on_delete=models.DO_NOTHING, related_name="issues")
    page_url = models.TextField()
    issue_code = models.TextField()
    severity = models.TextField()
    message = models.TextField()
    detected_at = models.TextField()
    resolved_at = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "page_issues"
