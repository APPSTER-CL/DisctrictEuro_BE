import django_filters
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.utils.translation import get_language
from rest_framework import filters

from core import models


def modify_upper_date(querydict, date_field='date_to'):
    data = querydict.copy()
    if data:
        date_to = data.get(date_field, None)
        if date_to:
            data[date_field] = '%s 23:59:59' % date_to
    return data


class OrderFilter(filters.FilterSet):
    date_from = django_filters.DateTimeFilter(name='created', lookup_type='gte')
    date_to = django_filters.DateTimeFilter(name='created', lookup_type='lte')
    status = django_filters.CharFilter(name='status', lookup_type='exact')

    class Meta:
        model = models.Order
        fields = ('date_from', 'date_to', 'status',)

    def __init__(self, *args, **kwargs):
        data = modify_upper_date(args[0]) if len(args) else None
        super(OrderFilter, self).__init__(data, **kwargs)


class ProductFilter(filters.FilterSet):
    store = django_filters.CharFilter(name='store')
    country = django_filters.MethodFilter(action='filter_country')
    search = django_filters.MethodFilter(action='do_search')

    class Meta:
        model = models.Product
        fields = ('store', 'country', 'search')

    def filter_country(self, queryset, value):
        return queryset.filter(
            store__countries__pk=value
        )

    def do_search(self, queryset, value):
        query = reduce(lambda x, y: y | x, map(SearchQuery, value.split()))

        search_fields = [
            # (field_name, field_weight, field_translated?)
            ('name', 'A', True),
            ('description', 'B', True),
            ('store__name', 'C', True),
            ('category__name', 'C', True)
        ]
        vector = None
        lang = get_language()
        for s in search_fields:
            if s[2]:
                field_name = '%s_%s' % (s[0], lang)
            else:
                field_name = s[0]
            if vector:
                vector += SearchVector(field_name, weight=s[1])
            else:
                vector = SearchVector(field_name, weight=s[1])

        return queryset.annotate(rank=SearchRank(vector, query)).filter(rank__gt=0.1).order_by('-rank')


class SampleDispatchFilter(filters.FilterSet):
    store = django_filters.MethodFilter(action='filter_store')
    tracking_number = django_filters.CharFilter(lookup_type="icontains")
    shipping_company = django_filters.CharFilter(lookup_type="icontains")

    class Meta:
        model = models.SampleDispatch
        fields = ('store', 'tracking_number', 'shipping_company')

    def filter_store(self, queryset, value):
        return queryset.filter(store_id=value)
