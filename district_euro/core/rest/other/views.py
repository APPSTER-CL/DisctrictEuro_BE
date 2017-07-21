import random

import moneyed
from django.db.models import Count
from rest_framework.decorators import detail_route
from rest_framework.filters import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import models, throttling
from core.pagination import paginated_by
from core.rest.common import serializers as common_serializers
from core.rest.common import views as common_views
from core.rest.common.views import AbstractProductViewSet
from district_euro import settings
from .filters import StoreFilter
from .serializers import CategorySerializer, WarehouseSerializer, StoreSerializer, StoreDetailSerializer, \
    CountrySerializer, RegionSerializer, RegionDetailSerializer, CountryDetailSerializer, JoinRequestSerializer, \
    SignUpRequestSerializer


class ShippingStatusView(APIView):
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        """
        List posible shipping status
        ---
        type:
            id:
                type: string
                required: true
            name:
                type: string
                required: true
        """
        payload = [{'id': k, 'name': v} for k, v in models.ShippingStatusMixin.STATUS]
        return Response(payload)


class CurrencyListView(APIView):
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        """
        List supported currencies
        ---
        type:
            code:
                type: string
                required: true
                description: currency identifier
            name:
                type: string
                required: true
        """
        currencies = [
            {
                'code': c.code,
                'name': c.name,
            }
            for c in map(moneyed.get_currency, settings.CURRENCIES)
            ]
        return Response(currencies)


class LanguageListView(APIView):
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        """
        List supported languages
        ---

        type:
            code:
                type: string
                required: true
                description: language identifier
            name:
                type: string
                required: true
        """
        languages = [
            {
                'code': lang[0],
                'name': lang[1]
            } for lang in settings.LANGUAGES
            ]
        return Response(data=languages)


class ProductViewSet(AbstractProductViewSet):
    permission_classes = ()

    def get_queryset(self):
        return super(ProductViewSet, self).get_queryset().filter(is_approved=True)


class CategoryView(APIView):
    permission_classes = ()

    def get(self, request, *args, **kwargs):
        """
        List categories.
        ---
        """
        serialized = CategorySerializer(models.Category.objects.filter(super_category=None) \
                                        .prefetch_related('subcategories'), many=True)
        return Response(serialized.data)


class WarehouseViewSet(GenericViewSet, ListModelMixin):
    permission_classes = ()
    pagination_class = None

    def get_queryset(self):
        if self.action == 'showrooms':
            return models.Showroom.objects.filter(warehouse_id=self.kwargs.get('pk'))
        return models.Warehouse.objects.all()

    def get_serializer_class(self):
        if self.action == 'showrooms':
            return common_serializers.ShowroomSerializer
        return WarehouseSerializer

    def list(self, request, *args, **kwargs):
        """
        List warehouses
        ---
        response_serializer: core.rest.other.serializers.WarehouseSerializer
        """
        return super(WarehouseViewSet, self).list(request, *args, **kwargs)

    @detail_route(methods=['get'])
    def showrooms(self, request, *args, **kwargs):
        """
        List showrooms for warehouse.
        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        return super(WarehouseViewSet, self).list(request, *args, **kwargs)


class StoreViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    permission_classes = ()
    pagination_class = paginated_by(page_size=20)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = StoreFilter
    ordering_fields = ('popularity',)

    def get_queryset(self):
        queryset = models.Store.objects.prefetch_related('categories').all()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('store_location')
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return StoreDetailSerializer
        return StoreSerializer

    def list(self, request, *args, **kwargs):
        """
        List stores.
        Ordering is enabled for popularity only. If popularity is the value of ordering the order will be ascending.
        If -popularity is set then is descending. Recomending ordering is -popularity.
        ---
        response_serializer: core.rest.other.serializers.StoreSerializer

        parameters:
            - name: ordering
              required: false
              paramType: query
        """
        return super(StoreViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Full store information.
        ---
        response_serializer: core.rest.other.serializers.StoreDetailSerializer
        """
        return super(StoreViewSet, self).retrieve(request, *args, **kwargs)


class CountryViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    permission_classes = ()
    pagination_class = paginated_by(page_size=20)

    def get_queryset(self):
        if self.action == 'regions':
            country_id = self.kwargs.get('pk')
            queryset = models.Region.objects.annotate(number_of_stores=Count('region_stores')) \
                .filter(number_of_stores__gt=0)
            return queryset.filter(city__country_id=country_id).select_related('city')
        elif self.action == 'popular_products':
            country_id = self.kwargs.get('pk')
            product_pks = models.Product.objects.filter(popular_in=country_id).values_list('pk', flat=True)
            product_pks = random.sample(product_pks, min(20, len(product_pks)))
            # Just a sample of products are listed.
            self.pagination_class = None
            return models.Product.objects.filter(pk__in=product_pks).prefetch_related('images').order_by('?')

        queryset = models.Country.objects.filter(in_app=True).select_related('image').all()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('images')
        return queryset

    def get_serializer_class(self):
        if self.action == 'regions':
            return RegionSerializer
        elif self.action == 'retrieve':
            return CountryDetailSerializer
        elif self.action == 'popular_products':
            return common_serializers.ProductSerializer
        return CountrySerializer

    def list(self, request, *args, **kwargs):
        """
        List countries.
        ---
        response_serializer: core.rest.other.serializers.CountrySerializer
        """
        return super(CountryViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Detail country information.
        ---
        response_serializer: core.rest.other.serializers.CountryDetailSerializer
        """
        return super(CountryViewSet, self).retrieve(request, *args, **kwargs)

    @detail_route(methods=['get'])
    def regions(self, request, *args, **kwargs):
        """
        List regions for country.
        ---
        response_serializer: core.rest.other.serializers.RegionSerializer
        """
        return super(CountryViewSet, self).list(request, *args, **kwargs)

    @detail_route(methods=['get'], url_path='popular-products')
    def popular_products(self, request, *args, **kwargs):
        """
        List a sample of 20 popular products of a country. List is not paginated and its order is random.
        ---
        response_serializer: core.rest.common.serializers.ProductSerializer
        """
        return super(CountryViewSet, self).list(request, *args, **kwargs)


class RegionViewSet(GenericViewSet, RetrieveModelMixin):
    permission_classes = ()
    pagination_class = paginated_by(page_size=20)

    def get_queryset(self):
        city_id = self.kwargs.get('pk')
        return models.Region.objects.filter(pk=city_id).prefetch_related('region_stores', 'region_stores__store') \
            .select_related('city__country')

    def get_serializer_class(self):
        return RegionDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Get city details including stores its locations.
        ---
        response_serializer: core.rest.other.serializers.RegionDetailSerializer
        """
        return super(RegionViewSet, self).retrieve(request, *args, **kwargs)


class ShowroomViewSet(common_views.ShowroomViewSet):
    permission_classes = ()


class JoinRequestViewSet(GenericViewSet, CreateModelMixin):
    permission_classes = ()
    throttle_classes = (throttling.throttle_by('2/min', 'join-request'),)
    serializer_class = JoinRequestSerializer

    def create(self, request, *args, **kwargs):
        """
        Send join requests here hehe.
        ---

        request_serializer: core.rest.other.serializers.JoinRequestSerializer

        """
        response = super(JoinRequestViewSet, self).create(request, *args, **kwargs)
        response.status_code = 200
        return response


class SignUpRequestViewSet(GenericViewSet, CreateModelMixin):
    permission_classes = ()
    throttle_classes = (throttling.throttle_by('2/min', 'join-request'),)
    serializer_class = SignUpRequestSerializer

    def create(self, request, *args, **kwargs):
        """
        Send join requests here.
        ---

        request_serializer: core.rest.other.serializers.SignUpRequestSerializer

        """
        response = super(SignUpRequestViewSet, self).create(request, *args, **kwargs)
        response.status_code = 200
        return response
