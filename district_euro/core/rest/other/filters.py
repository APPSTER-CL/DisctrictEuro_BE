import django_filters
from rest_framework import filters

from core import models


class StoreFilter(filters.FilterSet):
    country = django_filters.MethodFilter(action='filter_country')

    class Meta:
        model = models.Store
        fields = ('country',)

    def filter_country(self, queryset, value):
        return queryset.filter(
            countries__pk=value
        )
