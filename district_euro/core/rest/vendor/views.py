from django.db.models import Prefetch, Q
from rest_framework import serializers
from rest_framework import status
from rest_framework.decorators import permission_classes, parser_classes, api_view, list_route
from rest_framework.mixins import CreateModelMixin, ListModelMixin, DestroyModelMixin, RetrieveModelMixin
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import models, permissions
from core import product as product_logic
from core.pagination import paginated_by
from core.rest.common import views as common_views
from core.utils.mixins import PartialUpdateModelMixin, UserViewMixin, QueryParamMixin
from .serializers import OrderUpdateSerializer, ProductCreateSerializer, ProductSerializer, \
    IncompleteProductCreateSerializer, IncompleteProductSerializer, \
    IncompleteProductDetailSerializer, InventorySerializer, SampleDispatchUpdateSerializer, \
    SampleDispatchCreateSerializer, ProductUpdateSerializer, ProductDetailSerializer, \
    IncompleteProductUpdateSerializer, PeriodOverviewSerializer


class OrderView(common_views.AbstractOrderView, PartialUpdateModelMixin):
    permission_classes = (permissions.VendorPermission,)

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return OrderUpdateSerializer
        return super(OrderView, self).get_serializer_class()

    def get_queryset(self):
        store = models.Store.objects.filter(vendor_id=self.get_user_id()).first()
        queryset = models.Order.objects.filter(store_id=store.id).select_related('consumer', 'consumer__user')
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('order_items')
        if self.action == 'history':
            queryset = queryset.filter(status__in=(models.Order.RETURNED, models.Order.DELIVERED))
        if self.action == 'unconfirmed':
            queryset = queryset.exclude(status__in=(models.Order.RETURNED, models.Order.DELIVERED))
        return queryset

    def partial_update(self, request, *args, **kwargs):
        """
        Updates some field of the order.
        ---
        request_serializer: core.rest.vendor.serializers.OrderUpdateSerializer
        omit_parameters:
            - query
        """
        return super(OrderView, self).partial_update(request, *args, **kwargs)

    @list_route(methods=['get'])
    def history(self, request, *args, **kwargs):
        """
        List order history (orders that are delivered or returned).
        ---
        response_serializer: core.rest.common.serializers.OrderSerializer
        """
        return super(OrderView, self).list(request, *args, **kwargs)

    @list_route(methods=['get'])
    def unconfirmed(self, request, *args, **kwargs):
        """
        List order history (orders that are delivered or returned).
        ---
        response_serializer: core.rest.common.serializers.OrderSerializer
        """
        return super(OrderView, self).list(request, *args, **kwargs)


class ProductViewSet(common_views.AbstractProductViewSet, UserViewMixin, CreateModelMixin, DestroyModelMixin,
                     PartialUpdateModelMixin,
                     QueryParamMixin):
    permission_classes = (permissions.VendorPermission,)

    def get_serializer_class(self):
        if self.action == 'create':
            if self.get_query_param('save_incomplete', False) == 'true':
                return IncompleteProductCreateSerializer
            return ProductCreateSerializer
        elif self.action == 'list':
            return ProductSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        elif self.action == 'partial_update':
            return ProductUpdateSerializer
        return super(ProductViewSet, self).get_serializer_class()

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        try:
            incomplete_product_pk = self.get_query_param('incomplete_product', None)
            if incomplete_product_pk:
                int(incomplete_product_pk)
        except:
            raise serializers.ValidationError('incomplete_product parameter must be an integer')
        context = {
            'user': self.get_user(),
            'incomplete_product_pk': incomplete_product_pk
        }
        return serializer_class(*args, context=context, **kwargs)

    def get_queryset(self):
        store = self.get_user().vendor.store
        queryset = models.Product.actives.filter(store=store)
        if self.action == 'retrieve':
            return queryset.prefetch_related(
                Prefetch('units', models.ProductUnit.objects.prefetch_related('attributes')))
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Creates a product and units. If query params save_incomplete is true and there are errors then the product is
        saved in incompleteProduct table. If its not specified or false then returns the errors encountered.
        ---
        request_serializer: core.rest.vendor.serializers.ProductCreateSerializer

        omit_parameters:
            - query

        parameters:
            - name: save_incomplete
              required: False
              paramType: query
              type: Boolean
            - name: incomplete_product_pk
              required: False
              paramType: query
              type: int

        responseMessages:
            - code: 201
              message: Product successfuly created
            - code: 202
              message: Product created but with incomplete information
            - code: 400
              message: Errors in product information validation.

        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        # If product is an IncompleteProduct then the request is accepted but not success nor created.
        if isinstance(product, models.IncompleteProduct):
            data = IncompleteProductDetailSerializer(product).data
            status_code = status.HTTP_202_ACCEPTED
        else:
            data = ProductCreateSerializer(product).data
            status_code = status.HTTP_201_CREATED
        return Response(data, status=status_code)

    def destroy(self, request, *args, **kwargs):
        """
        Set a product as inactive. Its not showed
        ---
        omit_parameters:
            - query
        """
        instance = self.get_object()
        instance.set_inactive()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        """
        Updates some of the product fields.
        ---
        omit_parameters:
            - query

        request_serializer: core.rest.vendor.serializers.ProductUpdateSerializer
        """
        return super(ProductViewSet, self).partial_update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Get product information to setup edit form.
        ---
        omit_parameters:
            - query

        request_serializer: core.rest.vendor.serializers.ProductDetailSerializer
        """
        return super(ProductViewSet, self).retrieve(request, *args, **kwargs)


class ProductSampleViewSet(common_views.AbstractProductSampleViewSet, UserViewMixin):
    permission_classes = (permissions.VendorPermission,)

    def get_queryset(self):
        queryset = super(ProductSampleViewSet, self).get_queryset()
        store_id = self.get_user().vendor.store.id
        return queryset.filter(product_unit__product__store_id=store_id)


class SampleDispatchViewSet(common_views.AbstractSampleDispatchViewSet, CreateModelMixin, UserViewMixin,
                            PartialUpdateModelMixin):
    permission_classes = (permissions.VendorPermission,)
    pagination_class = paginated_by(page_size=2)

    def get_queryset(self):
        queryset = models.SampleDispatch.objects.all()
        if self.action == 'create':
            return queryset
        return queryset.select_related('warehouse') \
            .exclude(status=models.SampleDispatch.DELIVERED) \
            .prefetch_related(Prefetch('samples_units',
                                       models.ProductSampleUnits.objects.select_related('product_unit',
                                                                                        'product_unit__product')))

    def get_serializer(self, *args, **kwargs):
        return self.get_serializer_class()(*args, context={'user': self.get_user()}, **kwargs)

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return SampleDispatchUpdateSerializer
        elif self.action == 'list':
            return super(SampleDispatchViewSet, self).get_serializer_class()
        return SampleDispatchCreateSerializer

    def create(self, request, *args, **kwargs):
        """
        Records a product sample send.
        ---
        serializer: core.rest.common.serializers.SampleDispatchSerializer
        """
        return super(SampleDispatchViewSet, self).create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        List products samples sent and not yet received.
        ---
        serializer: core.rest.common.serializers.SampleDispatchSerializer
        """
        return super(SampleDispatchViewSet, self).list(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Updates shipping information about sample.
        ---
        request_serializer: core.rest.vendor.serializers.SampleDispatchUpdateSerializer
        """
        return super(SampleDispatchViewSet, self).partial_update(request, *args, **kwargs)


class IncompleteProductViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin, UserViewMixin,
                               PartialUpdateModelMixin):
    permission_classes = (permissions.VendorPermission,)
    pagination_class = paginated_by(page_size=20)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return IncompleteProductDetailSerializer
        elif self.action == 'partial_update':
            return IncompleteProductUpdateSerializer
        return IncompleteProductSerializer

    def get_serializer(self, *args, **kwargs):
        context = {
            'user': self.get_user(),
        }
        return self.get_serializer_class()(*args, context=context, **kwargs)

    def get_queryset(self):
        store = self.get_user().vendor.store
        return models.IncompleteProduct.objects.filter(store=store).order_by('name')

    def retrieve(self, request, *args, **kwargs):
        """
        Return incomplete products for loged in vendor.
        ---
        response_serializer: core.rest.vendor.serializers.IncompleteProductDetailSerializer
        """
        return super(IncompleteProductViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        List vendor's incomplete products.
        ---
        response_serializer: core.rest.vendor.serializers.IncompleteProductSerializer
        """
        return super(IncompleteProductViewSet, self).list(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """
        Updates incomplete product information without trying to save it as an actual product.
        ---
        """
        return super(IncompleteProductViewSet, self).partial_update(request, *args, **kwargs)


class InventoryViewSet(GenericViewSet, ListModelMixin, UserViewMixin):
    permission_classes = (permissions.VendorPermission,)
    pagination_class = paginated_by(page_size=20)
    serializer_class = InventorySerializer

    def get_serializer(self, *args, **kwargs):
        context = {
            'request': self.request
        }
        return self.get_serializer_class()(*args, context=context, **kwargs)

    def get_queryset(self):
        store = self.get_user().vendor.store
        queryset = models.ProductUnit.objects.select_related('product') \
            .filter(product__store=store, product__is_active=True) \
            .prefetch_related(
            Prefetch('attributes', queryset=models.AttributeValue.objects.select_related('attribute'))) \
            .order_by('product__name')
        if self.action == 'unapproved_inventory':
            return queryset.filter(product__is_approved=False)
        elif self.action == 'list':
            return queryset.filter(product__is_approved=True)
        return queryset

    def list(self, request, *args, **kwargs):
        """
        Lists inventory that is shown for users.
        """
        return super(InventoryViewSet, self).list(request, *args, **kwargs)

    @list_route(methods=['get'], url_path='unapproved')
    def unapproved(self, request, *args, **kwrags):
        """
        List inventory that has not been approved.
        ---
        """
        return super(InventoryViewSet, self).list(request, *args, **kwrags)


class AttributeViewSet(common_views.AbstractAttributeViewSet, UserViewMixin, QueryParamMixin):
    permission_classes = (permissions.VendorPermission,)

    def get_queryset(self):
        queryset = super(AttributeViewSet, self).get_queryset()
        category_id = self.get_query_param_int('category')
        if category_id:
            category = models.Category.objects.filter(pk=category_id).prefetch_related('subcategories').first()
            if not category:
                raise serializers.ValidationError('category does not exists')
            queryset = queryset.filter(Q(categories__in=category.flatten()) | Q(categories=None))
        store = self.get_user().vendor.store
        return queryset.filter(Q(store=None) | Q(store=store))

    def list(self, request, *args, **kwargs):
        """
        List attributes
        ---
        parameters:
            - name: category
              required: False
              paramType: query
              description: Category for which to list product attribtutes. If the category has subcategories then subcategories' attributes are added too.

        response_serializer: core.rest.common.serializers.AttributeSerializer
        """
        return super(AttributeViewSet, self).list(request, *args, **kwargs)


class OverviewView(APIView, UserViewMixin):
    permission_classes = (permissions.VendorPermission,)

    def get_queryset(self):
        store = self.get_user().vendor.store
        type = self.kwargs['type']
        queryset = models.PeriodOverview.objects.filter(store=store, type__name__iexact=type).order_by('-date_to')
        return queryset

    def get(self, request, type, *args, **kwargs):
        """
        List past 12 months overview. Supported types are: <br>
        - sales<br>
        - visits<br>
        ---
        """
        serialized = PeriodOverviewSerializer(self.get_queryset()[:12], many=True)
        return Response(serialized.data)


@api_view(['post'])
@permission_classes([permissions.VendorPermission])
@parser_classes([FormParser, MultiPartParser])
def product_bulk_upload(request, *args, **kwargs):
    """
    Parse excel file and returns the same information as json with validation. Information is grouped by sheet.
    ---
    parameters:
        - name: file
          required: True
          type: file
          paramType: form
    """
    data = product_logic.bulk_product_upload(request.data.get('file', None), request.user)

    return Response(data=data, status=status.HTTP_200_OK)
