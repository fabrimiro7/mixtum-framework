from rest_framework import serializers
from .models import Site, SiteSitemap, Run, Page, PageIssue


class SiteCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    base_url = serializers.URLField()
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    owner = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    tags = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class SitemapCreateSerializer(serializers.Serializer):
    sitemap_url = serializers.URLField()


class CrawlRequestSerializer(serializers.Serializer):
    concurrency = serializers.IntegerField(required=False, min_value=1)
    timeout = serializers.FloatField(required=False, min_value=1)
    retries = serializers.IntegerField(required=False, min_value=0)
    sitemap_depth = serializers.IntegerField(required=False, min_value=1)
    user_agent = serializers.CharField(required=False, allow_blank=True)


class RerunRequestSerializer(serializers.Serializer):
    sitemap_url = serializers.URLField()


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = [
            "id",
            "name",
            "base_url",
            "notes",
            "owner",
            "tags",
            "status",
            "created_at",
        ]
        read_only_fields = fields


class SiteSitemapSerializer(serializers.ModelSerializer):
    site_id = serializers.IntegerField(source="site.id", read_only=True)

    class Meta:
        model = SiteSitemap
        fields = [
            "id",
            "site_id",
            "sitemap_url",
            "created_at",
        ]
        read_only_fields = fields


class RunSerializer(serializers.ModelSerializer):
    site_id = serializers.IntegerField(source="site.id", read_only=True)
    config = serializers.SerializerMethodField()
    issues_summary = serializers.SerializerMethodField()

    class Meta:
        model = Run
        fields = [
            "id",
            "site_id",
            "started_at",
            "finished_at",
            "root_url",
            "config",
            "schedule",
            "status",
            "total_urls",
            "issues_summary",
        ]
        read_only_fields = fields

    def get_config(self, obj):
        return obj.config()

    def get_issues_summary(self, obj):
        return obj.summary()


class PageSerializer(serializers.ModelSerializer):
    run_id = serializers.IntegerField(source="run.id", read_only=True)
    site_id = serializers.IntegerField(source="site.id", read_only=True)
    diagnostics = serializers.SerializerMethodField()

    class Meta:
        model = Page
        fields = [
            "id",
            "run_id",
            "site_id",
            "url",
            "lastmod",
            "status_code",
            "word_count",
            "response_time_ms",
            "issues_count",
            "sitemap_url",
            "updated_at",
            "diagnostics",
        ]
        read_only_fields = fields

    def get_diagnostics(self, obj):
        return obj.diagnostics()


class PageIssueSerializer(serializers.ModelSerializer):
    run_id = serializers.IntegerField(source="run.id", read_only=True)
    site_id = serializers.IntegerField(source="site.id", read_only=True)
    page_id = serializers.IntegerField(source="page.id", read_only=True)

    class Meta:
        model = PageIssue
        fields = [
            "id",
            "run_id",
            "site_id",
            "page_id",
            "page_url",
            "issue_code",
            "severity",
            "message",
            "detected_at",
            "resolved_at",
        ]
        read_only_fields = fields


class PageIssueDetailSerializer(serializers.ModelSerializer):
    run_id = serializers.IntegerField(source="run.id", read_only=True)
    site_id = serializers.IntegerField(source="site.id", read_only=True)
    page_id = serializers.IntegerField(source="page.id", read_only=True)

    class Meta:
        model = PageIssue
        fields = [
            "id",
            "run_id",
            "site_id",
            "page_id",
            "page_url",
            "issue_code",
            "severity",
            "message",
            "detected_at",
            "resolved_at",
        ]
        read_only_fields = fields
