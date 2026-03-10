from django.urls import path

from .views import (
    DashboardView,
    SitesListView,
    SiteDetailView,
    SiteSitemapsCreateView,
    SiteCrawlView,
    SiteRerunView,
    SiteRunsView,
    SitePagesView,
    SiteIssuesView,
    PageDetailView,
    SiteStatusView,
)

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("sites/", SitesListView.as_view(), name="sites_list"),
    path("sites/<int:site_id>/", SiteDetailView.as_view(), name="site_detail"),
    path("sites/<int:site_id>/sitemaps/", SiteSitemapsCreateView.as_view(), name="site_sitemaps_create"),
    path("sites/<int:site_id>/crawl/", SiteCrawlView.as_view(), name="site_crawl"),
    path("sites/<int:site_id>/rerun/", SiteRerunView.as_view(), name="site_rerun"),
    path("sites/<int:site_id>/runs/", SiteRunsView.as_view(), name="site_runs"),
    path("sites/<int:site_id>/pages/", SitePagesView.as_view(), name="site_pages"),
    path("sites/<int:site_id>/issues/", SiteIssuesView.as_view(), name="site_issues"),
    path("sites/<int:site_id>/status/", SiteStatusView.as_view(), name="site_status"),
    path("pages/<int:page_id>/", PageDetailView.as_view(), name="page_detail"),
]
