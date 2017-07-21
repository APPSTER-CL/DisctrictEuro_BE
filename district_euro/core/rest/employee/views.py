from django.db import transaction
from django.db.models import F
from rest_framework import status
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from core import models
from core.pagination import paginated_by
from core.permissions import EmployeePermission
from core.rest.common import views as common_views, serializers as common_serializers
from core.utils.mixins import UserViewMixin
from .serializers import SampleTransferSerializer, SampleSerializer


class SampleDispatchViewSet(common_views.AbstractSampleDispatchViewSet, UserViewMixin):
    permission_classes = (EmployeePermission,)
    pagination_class = paginated_by(page_size=5)

    def get_queryset(self):
        queryset = super(SampleDispatchViewSet, self).get_queryset()
        return queryset.filter(warehouse=self.get_user().employee.warehouse)

    def list(self, request, *args, **kwargs):
        """
        List samples sent by vendors to employees warehouse
        ---
        """
        return super(SampleDispatchViewSet, self).list(request, *args, **kwargs)

    @detail_route(methods=['POST'], url_path='confirm')
    def confirm_received(self, request, *args, **kwargs):
        """
        Confirms the reception of samples sent by the vendor.
        ---
        """
        sample_dispatched = self.get_object()

        warehouse = sample_dispatched.warehouse

        with transaction.atomic():
            sample_dispatched.status = models.SampleDispatch.DELIVERED
            sample_dispatched.save()

            sample_data = {
                'warehouse': warehouse,
                'sample_dispatch': sample_dispatched,
                'location': warehouse,
            }

            for unit in sample_dispatched.samples_units.all():
                existing_sample_pk = warehouse.samples.filter(product_unit=unit.product_unit,
                                                              warehouse=warehouse).values_list(
                    'pk', flat=True).first()
                if existing_sample_pk:
                    models.Sample.objects.filter(pk=existing_sample_pk).update(quantity=F('quantity') + unit.quantity)
                else:
                    sample = models.Sample.objects.create(product_unit=unit.product_unit,
                                                          quantity=unit.quantity, **sample_data)
                    sample.showrooms.add(*list(sample_dispatched.showrooms.all()))

        return Response(common_serializers.SampleDispatchSerializer(sample_dispatched).data, status=status.HTTP_200_OK)


class SampleViewSet(common_views.AbstractProductSampleViewSet, UserViewMixin):
    permission_classes = (EmployeePermission,)
    pagination_class = paginated_by(page_size=20)

    def get_queryset(self):
        if self.action == 'warehouse':
            return self.get_user().employee.warehouse.samples.select_related('product_unit__product__store')
        elif self.action == 'showroom':
            showroom_ids = models.Showroom.objects.filter(warehouse=self.get_user().employee.warehouse).values_list(
                'pk', flat=True)
            showroom_content_type = models.ContentType.objects.get_for_model(models.Showroom)
            return models.Sample.objects.filter(object_type=showroom_content_type,
                                                object_id__in=showroom_ids).select_related(
                'product_unit__product__store')

        return super(SampleViewSet, self).get_queryset() \
            .filter(warehouse=self.get_user().employee.warehouse) \
            .prefetch_related('location') \
            .select_related('product_unit__product__store')

    def get_serializer_class(self):
        if self.action in ['list', 'showroom', 'warehouse']:
            return SampleSerializer
        return super(SampleViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        List samples managed by employee's warehouse.
        ---
        response_serializer: core.rest.employee.serializers.SampleSerializer
        """
        return super(SampleViewSet, self).list(request, *args, **kwargs)

    @list_route(methods=['get'], url_path='on-warehouse')
    def warehouse(self, request, *args, **kwargs):
        """
        List samples for employee's warehouse that are currently on the warehouse.
        ---
        response_serializer: core.rest.employee.serializers.SampleSerializer
        """
        return super(SampleViewSet, self).list(request, *args, **kwargs)

    @list_route(methods=['get'], url_path='on-showroom')
    def showroom(self, request, *args, **kwargs):
        """
        List samples for employee's warehouse that are currently on a showroom managed by that warehouse.
        ---
        response_serializer: core.rest.employee.serializers.SampleSerializer
        """
        return super(SampleViewSet, self).list(request, *args, **kwargs)

    @detail_route(methods=['post'])
    def transfer(self, request, *args, **kwargs):
        """
        Transfer samples from current location to a warehouse or showroom.
        ---

        request_serializer: core.rest.employee.serializers.SampleTransferSerializer
        """
        sample = self.get_object()

        serializer = SampleTransferSerializer(data=request.data, context={'sample': sample})
        serializer.is_valid(raise_exception=True)
        destiny = serializer.validated_data.get('showroom') or sample.warehouse
        quantity = serializer.validated_data.get('quantity')

        with transaction.atomic():
            origin_pk = sample.pk
            origin_quantity = sample.quantity
            existing_sample = destiny.samples.filter(product_unit=sample.product_unit).first()
            if existing_sample:
                models.Sample.objects.filter(pk=existing_sample.pk).update(quantity=F('quantity') + quantity)
            else:
                # Creates new sample from existing one. Copies all fields of previous
                showrooms = sample.showrooms.all()
                sample.pk = None
                sample.quantity = quantity
                sample.location = destiny
                sample.save()
                sample.showrooms.add(*list(showrooms))
            if origin_quantity == quantity:
                # If origin is left without samples then delete object.
                models.Sample.objects.get(pk=origin_pk).delete()
            else:  # origin_quantity > quantity
                models.Sample.objects.filter(pk=origin_pk).update(quantity=F('quantity') - quantity)
        return Response()


class EmployeeShowroomViewSet(common_views.ShowroomViewSet, UserViewMixin):
    permission_classes = (EmployeePermission,)
    pagination_class = None

    def get_queryset(self):
        return super(EmployeeShowroomViewSet, self).get_queryset().filter(warehouse=self.get_user().employee.warehouse)
