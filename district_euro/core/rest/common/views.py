from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.filters import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from core import models, permissions, image as image_logic
from core import throttling
from core.pagination import paginated_by
from core.utils.mixins import UserViewMixin
from .filters import OrderFilter, ProductFilter, SampleDispatchFilter
from .serializers import OrderSerializer, OrderDetailSerializer, ProductDetailSerializer, ProductSerializer, \
    ProductSampleSerializer, SampleSerializer, AttributeDetailSerailzer, SampleDispatchSerializer, ShowroomSerializer, \
    ShowroomDetailSerializer


class AbstractOrderView(GenericViewSet, RetrieveModelMixin, ListModelMixin, UserViewMixin):
    pagination_class = paginated_by(page_size=10)
    filter_backends = (DjangoFilterBackend,)
    filter_class = OrderFilter

    def get_queryset(self):
        raise NotImplementedError()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Get order and order items.
        ---
        omit_parameters:
            - query

        response_serializer: core.rest.common.serializers.OrderDetailSerializer
        """
        return super(AbstractOrderView, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        List orders.
        ---
        parameters:
            - name: date_from
              required: false
              paramType: query
            - name: date_to
              required: false
              paramType: query
            - name: status
              required: false
              paramType: query

        response_serializer: core.rest.common.serializers.OrderSerializer
        """
        return super(AbstractOrderView, self).list(request, *args, **kwargs)


class AbstractProductViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    """
    View for searching products, used by all users including anonymus.
    """
    pagination_class = paginated_by(page_size=10)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_class = ProductFilter
    ordering_fields = ('date_created', 'date_approved', 'sold_quantity')

    def get_queryset(self):
        queryset = models.Product.actives.prefetch_related('images')
        if self.action == 'retrieve':
            queryset = queryset.annotate(stock_quantity=Sum('units__quantity'))
        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer

    def retrieve(self, request, *args, **kwargs):
        """
        Get product detailed information.
        ---
        omit_parameters:
            - query
        """
        return super(AbstractProductViewSet, self).retrieve(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        List products. Ordering can be by date_created, date_approved, sold_quantity
        ---
        parameters:
            - name: ordering
              paramType: query
              required: false
        """
        return super(AbstractProductViewSet, self).list(request, *args, **kwargs)


class AbstractProductSampleViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    pagination_class = paginated_by(page_size=10)

    def get_queryset(self):
        return models.Sample.objects.all().select_related('product_unit', 'product_unit__product')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SampleSerializer
        return ProductSampleSerializer

    def list(self, request, *args, **kwargs):
        """
        List product samples location and other information.
        ---
        """
        return super(AbstractProductSampleViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve detail information about product sample location
        ---
        """
        return super(AbstractProductSampleViewSet, self).retrieve(request, *args, **kwargs)


class AbstractImageUploadView(APIView):
    """
    Abstract image uploader class.
    Attributes:
        - resize_on_upload:
            type: bool
            description: if the image is resized on upload.
        - associate_image_object:
            type: bool
            description: if the image should be asociated with the object.
        - app_label:
            type: str
            description: django app from which to retrieve objects.
    """
    parser_classes = (FormParser, MultiPartParser,)
    resize_on_upload = True
    associate_image_object = True
    app_label = 'core'

    def image_prefix(self, model, pk):
        """
        Image name prefix. It will be prefixed to its name.
        :param model: str
        :param pk: anythin with a .__str__ method
        :return: str
        """
        return "%s/%s/" % (model, pk)

    def validate_model(self, model):
        """
        Validate if images should be uploaded for the model. Returns model name on success or a False valuated value
        on error.
        :param model:
        :return: str
        """
        raise NotImplementedError()

    def on_after_upload(self, image, object):
        """
        Called after the image has been uploaded
        :param image:
        :param object:
        :return:
        """
        pass

    def validate_upload(self, obj, model, request):
        """
        Called before images are uploaded. Shuld raise a subclass of APIException
        :param obj:
        :param model:
        :param request:
        :return:
        """
        pass

    def get_file_name(self, file):
        """
        Return the file name (without prefix path) for this file. If None is returned then a random name is generated.
        :param file: FileUpload
        :return: str or None
        """
        return None

    def post(self, request, model, pk):
        """
        Uploads images and asociates it with an object.<br>
        For example a post to:<br>
        /api/image/product/38/ will upload an image to product 38<br>
        a post to:<br>
        /api/image/incompleteproduct/52/ will upload an image to an incomplete product<br>
        <br><br>
        Current enabled objects types are:<br>
        <ul>
            <li>product</li>
            <li>incompleteproduct</li>
        </ul>
        ---
        parameters:
            - name: model
              required: True
              type: string
              paramType: path
            - name: pk
              required: True
              type: int
              paramType: path
            - name: file1
              required: True
              type: file
              paramType: form
        """
        model = self.validate_model(model)

        if not model:
            raise Http404()

        prefix = self.image_prefix(model, pk)

        content_type = get_object_or_404(ContentType.objects.all(), model=model, app_label=self.app_label)
        obj = get_object_or_404(content_type.model_class().objects.all(), pk=pk)

        self.validate_upload(obj, model, request)

        for image in request.data.itervalues():
            image = image_logic.upload_image(prefix, (self.associate_image_object and obj) or None, image,
                                             file_name=self.get_file_name(image),
                                             resize_on_upload=self.resize_on_upload)
            self.on_after_upload(image, obj)

        return Response(status=status.HTTP_200_OK)


class ImageUploadView(AbstractImageUploadView):
    permission_classes = (permissions.VendorPermission,)

    def validate_model(self, model):
        if image_logic.is_model_valid(model):
            return model


class ImageUploadViewJoinUs(AbstractImageUploadView):
    permission_classes = ()
    throttle_classes = (throttling.throttle_by('60/min', 'join-request'),)
    resize_on_upload = False
    associate_image_object = True
    app_label = 'landing'

    def validate_model(self, model):
        return model

    def post(self, request, pk):
        """
        Uploads an image and asociate it with an object. Use this to set the object's main image if it supports it.
        Current enabled objects types are:<br>
        <ul>
            <li>product</li>
            <li>incompleteproduct</li>
        </ul>
        ---
        parameters:
            - name: pk
              required: True
              type: int
              paramType: path
            - name: file
              required: True
              type: file
              paramType: form
        """
        return super(ImageUploadViewJoinUs, self).post(request, "joinrequest", pk)


class MainImageUploadView(ImageUploadView):
    associate_image_object = False

    def on_after_upload(self, image, obj):
        old_image = obj.image
        obj.image = image
        obj.save()
        image_logic.delete_image(old_image)

    def validate_upload(self, obj, model, request):
        if not hasattr(obj, 'image'):
            raise APIException(status_code=400, detail=_('% object doesn\'t have main image' % model))

    def post(self, request, *args, **kwargs):
        """
        Uploads an image and asociate it with an object. Use this to set the object's main image if it supports it.
        Current enabled objects types are:<br>
        <ul>
            <li>product</li>
            <li>incompleteproduct</li>
        </ul>
        ---
        parameters:
            - name: model
              required: True
              type: string
              paramType: path
            - name: pk
              required: True
              type: int
              paramType: path
            - name: file1
              required: True
              type: file
              paramType: form
        """
        return super(MainImageUploadView, self).post(request, *args, **kwargs)


class InfographicUploadView(AbstractImageUploadView):
    permission_classes = (permissions.VendorPermission,)
    resize_on_upload = False
    associate_image_object = False

    def image_prefix(self, model, pk):
        return '%s/%s/infographic/' % (model, pk)

    def validate_model(self, model):
        if image_logic.is_model_valid(model):
            return model

    def on_after_upload(self, image, obj):
        obj.infographics.add(image)

    def get_file_name(self, file):
        return file.name

    def post(self, request, *args, **kwargs):
        """
        Uploads an image and asociate it with an object. Use this to upload a product infographic image.
        It can be used for products and incompleproducts.<br>
        ---
        parameters:
            - name: model
              required: True
              type: string
              paramType: path
            - name: pk
              required: True
              type: int
              paramType: path
            - name: file1
              required: True
              type: file
              paramType: form
        """
        return super(InfographicUploadView, self).post(request, *args, **kwargs)


class AbstractAttributeViewSet(GenericViewSet, ListModelMixin):
    def get_queryset(self):
        return models.Attribute.objects.prefetch_related('values').all()

    def get_serializer_class(self):
        return AttributeDetailSerailzer

    def list(self, request, *args, **kwargs):
        """
        List attributes
        ---
        response_serializer: core.rest.common.serializers.AttributeSerializer
        """
        return super(AbstractAttributeViewSet, self).list(request, *args, **kwargs)


class AbstractSampleDispatchViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    pagination_class = paginated_by(page_size=10)
    filter_backends = (DjangoFilterBackend,)
    filter_class = SampleDispatchFilter

    def get_queryset(self):
        queryset = models.SampleDispatch.objects.all()
        return queryset.select_related('warehouse') \
            .prefetch_related(Prefetch('samples_units',
                                       models.ProductSampleUnits.objects.select_related('product_unit',
                                                                                        'product_unit__product')))

    def get_serializer_class(self):
        return SampleDispatchSerializer

    def list(self, request, *args, **kwargs):
        """
        List products samples sent and not yet received.
        ---
        serializer: core.rest.common.serializers.SampleDispatchSerializer
        """
        return super(AbstractSampleDispatchViewSet, self).list(request, *args, **kwargs)


class ShowroomViewSet(GenericViewSet, RetrieveModelMixin, ListModelMixin):
    permission_classes = ()
    pagination_class = paginated_by(page_size=10)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ShowroomDetailSerializer
        return ShowroomSerializer

    def get_queryset(self):
        return models.Showroom.objects.select_related('country', 'city')

    def list(self, request, *args, **kwargs):
        """
        List showrooms.
        ---

        response_serializer: core.rest.common.serializers.ShowroomSerializer
        """
        return super(ShowroomViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Showroom detail
        ---

        response_serializer: core.rest.common.serializers.ShowroomDetailSerializer
        """
        return super(ShowroomViewSet, self).retrieve(request, *args, **kwargs)
