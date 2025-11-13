import django_filters
from django.contrib.contenttypes.models import ContentType
from base_modules.links import models


class LinkFilter(django_filters.FilterSet):
    # Filter by target (content_type id + object_id) or by natural key.
    content_type = django_filters.ModelChoiceFilter(
        queryset=ContentType.objects.all()
    )
    app_label = django_filters.CharFilter(method="filter_app_label")
    model = django_filters.CharFilter(method="filter_model")
    object_id = django_filters.NumberFilter()

    label = django_filters.CharFilter(lookup_expr="exact")
    q = django_filters.CharFilter(method="filter_q")

    class Meta:
        model = Link
        fields = ["label", "content_type", "object_id"]

    def filter_q(self, queryset, name, value):
        return queryset.filter(
            models.Q(title__icontains=value)
            | models.Q(description__icontains=value)
            | models.Q(url__icontains=value)
        )

    def filter_app_label(self, queryset, name, value):
        return queryset.filter(content_type__app_label=value)

    def filter_model(self, queryset, name, value):
        return queryset.filter(content_type__model=value)
