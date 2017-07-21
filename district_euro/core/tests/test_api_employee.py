import json

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from core.rest.employee import views, serializers
from .utils import *

product_data = {
    "name": "Test product",
    "description": "Test product description",
    "price_amount": "150.00",
    "price_currency": "USD",
    "units": [
        {
            "sku": "KDJAS9876",
            "quantity": "5",
            "attributes": []
        },
        {
            "sku": "KDJAS9877",
            "quantity": "10",
            "attributes": []
        }
    ]
}


class EmployeeTestCase(TestCase):
    fixtures = ('initial_data.yaml',)

    def setUp(self):
        self.factory = APIRequestFactory()
        product = models.Product.actives.select_related('store', 'store__vendor', 'store__vendor__user').first()
        assert product is not None, "cant run this test without products in the database"
        self.vendor = product.store.vendor.user
        self.store = models.Store.objects.create(
            vendor=self.vendor.vendor,
            name='test-store',
            description='store description',
        )
        self.store.categories.add(*list(models.Category.objects.filter(super_category=None)))
        units = product.units.all()
        if not units:
            for i in xrange(2):
                models.ProductUnit.objects.create(product=product, quantity=100)

        unit = models.ProductUnit.objects.filter(product=product).first()
        warehouse = models.Warehouse.objects.first()
        sample_dispatch = models.SampleDispatch.objects.create(store=self.store, warehouse=warehouse)
        models.ProductSampleUnits.objects.create(sample_dispatch=sample_dispatch, quantity=1, product_unit=unit)

        for u in product_data.get('units'):
            u['attributes'] = random.sample(models.AttributeValue.objects.all().values_list('pk', flat=True), 2)

        product_data['category'] = random.choice(models.Category.objects.all().values_list('pk', flat=True))

        self.employee = models.Employee.objects.filter(warehouse=sample_dispatch.warehouse).first()
        assert self.employee is not None, "cant run this test without an employee for all warehouses"

    def tearDown(self):
        pass

    def test_sample_confirm_received(self):
        url = '/api/employee/sample-dispatch/%d/confirm/'

        sample_dispatched = models.SampleDispatch.objects.filter(warehouse=self.employee.warehouse).first()
        if not sample_dispatched.was_shipped():
            sample_dispatched.tracking_number = sample_dispatched.tracking_number or 'UY6181981919CH'
            sample_dispatched.shipping_company = sample_dispatched.shipping_company or 'DHL'
            sample_dispatched.status = models.SampleDispatch.SHIPPED
            sample_dispatched.save()

        url = url % sample_dispatched.pk

        request = self.factory.post(url)
        force_authenticate(request, self.employee.user)

        response = views.SampleDispatchViewSet.as_view({'post': 'confirm_received'})(request, pk=sample_dispatched.pk)

        self.assertEqual(response.status_code, 200)

        created_samples_count = models.Sample.objects.filter(sample_dispatch=sample_dispatched.pk).count()

        self.assertEqual(created_samples_count, sample_dispatched.samples_units.count())

    def test_sample_list(self):
        url = '/api/employee/sample/'

        request = self.factory.get(url)
        force_authenticate(request, self.employee.user)
        response = views.SampleViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)

    def test_sample_transfer_valid(self):
        url = '/api/employee/sample/%d/transfer/'

        sample = models.Sample.objects.first()

        self.assertIsNotNone(sample)

        if sample.quantity < 2:
            sample.quantity == 10
            sample.save()

        warehouse = models.Warehouse.objects.first()

        previous_location = sample.location = warehouse
        sample.showrooms.clear()
        sample.showrooms.add(*list(warehouse.showrooms.all()))
        sample.save()

        data = {'quantity': sample.quantity - 2}
        destiny = sample.showrooms.first()
        data['showroom'] = destiny.pk

        request = self.factory.post(url % sample.pk, data=data)
        force_authenticate(request, self.employee.user)
        response = views.SampleViewSet.as_view({'post': 'transfer'})(request, pk=sample.pk)

        self.assertEqual(response.status_code, 200)

        # There're samples in destiny
        self.assertTrue(destiny.samples.filter(product_unit=sample.product_unit).count() > 0)
        # There're still samples in origin (becouse didint transfer all)
        self.assertTrue(previous_location.samples.filter(product_unit=sample.product_unit).count() > 0)

    def test_sample_transfer_invalid(self):
        url = '/api/employee/sample/%d/transfer/'

        sample = models.Sample.objects.first()

        self.assertIsNotNone(sample)

        warehouse = models.Warehouse.objects.first()
        sample.location = warehouse
        sample.save()

        data = {
            'quantity': 1,
            'warehouse': warehouse.pk,
        }

        request = self.factory.post(url % sample.pk, data=data)
        force_authenticate(request, self.employee.user)
        response = views.SampleViewSet.as_view({'post': 'transfer'})(request, pk=sample.pk)

        self.assertTrue(response.status_code, 400)





