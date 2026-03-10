import json
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mixtum_core.settings.base import REMOTE_API
from base_modules.user_manager.authentication import JWTAuthentication

from .models import Site, SiteSitemap, Run, Page, PageIssue
from .permissions import IsAdminOrSuperAdmin
from .serializers import (
    SiteCreateSerializer,
    SitemapCreateSerializer,
    CrawlRequestSerializer,
    RerunRequestSerializer,
    SiteSerializer,
    SiteSitemapSerializer,
    RunSerializer,
    PageSerializer,
    PageIssueSerializer,
    PageIssueDetailSerializer,
)
from .tasks import run_site_crawl
from .config import load_config


def _get_pagination_params(request, default_page_size=10):
    def _to_int(value, fallback):
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    page = _to_int(request.query_params.get("page"), 1)
    per_page = request.query_params.get("per_page")
    page_size = request.query_params.get("page_size")

    size = _to_int(page_size or per_page, default_page_size)
    if page < 1:
        page = 1
    if size < 1:
        size = default_page_size
    return page, size


def _paginate_queryset(queryset, page, page_size):
    offset = (page - 1) * page_size
    total = queryset.count()
    return queryset[offset : offset + page_size], total


class BasePerSeoView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrSuperAdmin]
    if REMOTE_API == True:
        authentication_classes = [JWTAuthentication]


class DashboardView(BasePerSeoView):
    def get(self, request):
        sites_total = Site.objects.count()
        sitemaps_total = SiteSitemap.objects.count()
        recent_sites = Site.objects.order_by("-created_at")[:10]
        return Response(
            {
                "sites_total": sites_total,
                "sitemaps_total": sitemaps_total,
                "recent_sites": SiteSerializer(recent_sites, many=True).data,
            }
        )


class SitesListView(BasePerSeoView):
    def get(self, request):
        page, page_size = _get_pagination_params(request, default_page_size=10)
        queryset = Site.objects.order_by("created_at")
        items, total = _paginate_queryset(queryset, page, page_size)
        return Response(
            {
                "items": SiteSerializer(items, many=True).data,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        )

    def post(self, request):
        serializer = SiteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        now_iso = timezone.now().isoformat()
        site = Site.objects.create(
            name=serializer.validated_data["name"],
            base_url=str(serializer.validated_data["base_url"]),
            notes=serializer.validated_data.get("notes") or "",
            owner=serializer.validated_data.get("owner") or "",
            tags=serializer.validated_data.get("tags") or "",
            status="active",
            created_at=now_iso,
        )
        return Response(SiteSerializer(site).data, status=201)


class SiteDetailView(BasePerSeoView):
    def get(self, request, site_id):
        site = get_object_or_404(Site, pk=site_id)
        sitemaps = SiteSitemap.objects.filter(site=site)
        latest_run = Run.objects.filter(site=site).order_by("-started_at").first()
        return Response(
            {
                "site": SiteSerializer(site).data,
                "sitemaps": SiteSitemapSerializer(sitemaps, many=True).data,
                "latest_run": RunSerializer(latest_run).data if latest_run else None,
            }
        )


class SiteSitemapsCreateView(BasePerSeoView):
    def post(self, request, site_id):
        site = get_object_or_404(Site, pk=site_id)
        serializer = SitemapCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sitemap = SiteSitemap.objects.create(
            site=site,
            sitemap_url=str(serializer.validated_data["sitemap_url"]),
            created_at=timezone.now().isoformat(),
        )
        return Response(SiteSitemapSerializer(sitemap).data, status=201)


class SiteCrawlView(BasePerSeoView):
    def post(self, request, site_id):
        site = get_object_or_404(Site, pk=site_id)
        if Run.objects.filter(site=site, status="running").exists():
            return Response({"detail": "Crawl already in progress"}, status=409)

        sitemaps = SiteSitemap.objects.filter(site=site)
        if not sitemaps.exists():
            return Response({"detail": "Add at least one sitemap before running a crawl"}, status=400)

        serializer = CrawlRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        overrides = serializer.validated_data or {}

        config = load_config().override(**overrides)
        root_url = site.base_url or sitemaps.first().sitemap_url
        run = Run.objects.create(
            site=site,
            started_at=timezone.now().isoformat(),
            finished_at=None,
            root_url=root_url,
            config_json=json.dumps(config.serialize()),
            schedule=None,
            status="running",
            total_urls=0,
            issues_summary="{}",
        )
        run_site_crawl.delay(run.id, site.id, None, overrides)
        return Response({"run_id": run.id}, status=201)


class SiteRerunView(BasePerSeoView):
    def post(self, request, site_id):
        site = get_object_or_404(Site, pk=site_id)
        serializer = RerunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sitemap_url = str(serializer.validated_data["sitemap_url"])

        config = load_config()
        run = Run.objects.create(
            site=site,
            started_at=timezone.now().isoformat(),
            finished_at=None,
            root_url=sitemap_url,
            config_json=json.dumps(config.serialize()),
            schedule=None,
            status="running",
            total_urls=0,
            issues_summary="{}",
        )
        run_site_crawl.delay(run.id, site.id, sitemap_url, None)
        return Response({"run_id": run.id}, status=201)

class SiteRunsView(BasePerSeoView):
    def get(self, request, site_id):
        site = get_object_or_404(Site, pk=site_id)
        limit = int(request.query_params.get("limit", 5))
        offset = int(request.query_params.get("offset", 0))
        queryset = Run.objects.filter(site=site).order_by("-started_at")
        runs_slice = queryset[offset : offset + limit]
        return Response(RunSerializer(runs_slice, many=True).data)


class SitePagesView(BasePerSeoView):
    def get(self, request, site_id):
        site = get_object_or_404(Site, pk=site_id)
        page, page_size = _get_pagination_params(request, default_page_size=10)
        queryset = Page.objects.filter(site=site)
        sitemap_url = request.query_params.get("sitemap_url")
        if sitemap_url:
            queryset = queryset.filter(sitemap_url=sitemap_url)
        queryset = queryset.order_by("-updated_at")
        items, total = _paginate_queryset(queryset, page, page_size)
        return Response(
            {
                "items": PageSerializer(items, many=True).data,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        )


class SiteIssuesView(BasePerSeoView):
    def get(self, request, site_id):
        site = get_object_or_404(Site, pk=site_id)
        page, page_size = _get_pagination_params(request, default_page_size=10)
        grouped = request.query_params.get("grouped") == "true"
        if grouped:
            category = request.query_params.get("category")
            category_counts = (
                PageIssue.objects.filter(site=site)
                .values("issue_code")
                .annotate(count=models.Count("id"))
                .order_by("-count")
            )
            category_counts_map = {row["issue_code"]: row["count"] for row in category_counts}
            queryset = PageIssue.objects.filter(site=site)
            if category:
                queryset = queryset.filter(issue_code=category)
            queryset = queryset.order_by("-detected_at")
            items, total = _paginate_queryset(queryset, page, page_size)
            return Response(
                {
                    "items": PageIssueSerializer(items, many=True).data,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "category_counts": category_counts_map,
                }
            )
        else:
            queryset = PageIssue.objects.filter(site=site).order_by("-detected_at")
            items, total = _paginate_queryset(queryset, page, page_size)
            return Response(
                {
                    "items": PageIssueSerializer(items, many=True).data,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                }
            )


class PageDetailView(BasePerSeoView):
    def get(self, request, page_id):
        page = get_object_or_404(Page, pk=page_id)
        issues = PageIssue.objects.filter(page=page).order_by("-detected_at")
        data = PageSerializer(page).data
        data["issues"] = PageIssueDetailSerializer(issues, many=True).data
        return Response(data)


class SiteStatusView(BasePerSeoView):
    def get(self, request, site_id):
        site = get_object_or_404(Site, pk=site_id)
        latest_run = Run.objects.filter(site=site).order_by("-started_at").first()
        running = bool(latest_run and latest_run.status == "running")
        return Response(
            {
                "site_id": site.id,
                "running": running,
                "latest_run": RunSerializer(latest_run).data if latest_run else None,
            }
        )
