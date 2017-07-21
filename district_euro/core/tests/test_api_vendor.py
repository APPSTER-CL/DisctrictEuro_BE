import json

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from core.rest.vendor import views, serializers
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


class VendorTestCase(TestCase):
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

    def tearDown(self):
        pass

    def test_order_list(self):
        url = '/api/vendor/order/'

        existing_order = models.Order.objects.select_related('store', 'store__vendor', 'store__vendor__user').first()
        if existing_order:
            user = existing_order.store.vendor.user
        else:
            raise Exception('Cant test order services if thers no orders')

        request = self.factory.get(url)
        force_authenticate(request, user)

        response = views.OrderView.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        self.assertIn('results', data)
        first_order = data.get('results')[0]
        self.assertIn('id', first_order)
        self.assertIn('created', first_order)
        self.assertIn('status', first_order)

    def test_order_list_history(self):
        url = '/api/vendor/order/history/'

        existing_order = models.Order.objects.select_related('store', 'store__vendor', 'store__vendor__user').first()
        if existing_order:
            user = existing_order.store.vendor.user
        else:
            raise Exception('Cant test order services if thers no orders')

        models.Order.objects.filter(pk=existing_order.pk).update(status='RET')

        request = self.factory.get(url)
        force_authenticate(request, user)

        response = views.OrderView.as_view({'get': 'history'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        orders_ids = [o.get('id') for o in data.get('results')]
        self.assertIn(existing_order.id, orders_ids)

    def test_order_list_history(self):
        url = '/api/vendor/order/unconfirmed/'

        existing_order = models.Order.objects.select_related('store', 'store__vendor', 'store__vendor__user').first()
        if existing_order:
            user = existing_order.store.vendor.user
        else:
            raise Exception('Cant test order services if thers no orders')

        models.Order.objects.filter(pk=existing_order.pk).update(status='RET')

        request = self.factory.get(url)
        force_authenticate(request, user)

        response = views.OrderView.as_view({'get': 'unconfirmed'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        orders_ids = [o.get('id') for o in data.get('results')]
        self.assertNotIn(existing_order.id, orders_ids)

    def test_order_update_tracking_information(self):
        url = '/api/vendor/order/%s/'

        existing_order = models.Order.objects.select_related('store', 'store__vendor', 'store__vendor__user').first()

        self.assertIsNotNone(existing_order)
        user = existing_order.store.vendor.user

        payload = {
            'status': 'SHP',
            'shipping_company': get_random_name(),
            'tracking_number': get_random_number(15),
        }

        request = self.factory.patch(url % existing_order.pk, data=payload)
        force_authenticate(request, user)
        response = views.OrderView.as_view({'patch': 'partial_update'})(request, pk=existing_order.pk)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(payload.get('shipping_company'), data.get('shipping_company'))
        self.assertEqual(payload.get('tracking_number'), data.get('tracking_number'))

    def test_order_update_tracking_information_partial(self):
        url = '/api/vendor/order/%s/'

        existing_order = models.Order.objects.select_related('store', 'store__vendor', 'store__vendor__user').first()

        self.assertIsNotNone(existing_order)
        user = existing_order.store.vendor.user

        payload = {
            'status': 'SHP',
            'shipping_company': get_random_name(),
            'tracking_number': None,
        }

        request = self.factory.patch(url % existing_order.pk, data=json.dumps(payload), content_type='application/json')
        force_authenticate(request, user)
        response = views.OrderView.as_view({'patch': 'partial_update'})(request, pk=existing_order.pk)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(payload.get('shipping_company'), data.get('shipping_company'))

    def test_order_detail(self):
        url = '/api/vendor/order/%d/'

        existing_order = models.Order.objects.select_related('store', 'store__vendor', 'store__vendor__user').first()

        self.assertIsNotNone(existing_order)

        user = existing_order.store.vendor.user

        request = self.factory.get(url % existing_order.id)
        force_authenticate(request, user)

        response = views.OrderView.as_view({'get': 'retrieve'})(request, pk=existing_order.pk)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('order_items', data)
        self.assertIn('total_price', data)

    def test_product_list(self):
        url = '/api/vendor/product/'

        data = {
            'field': 'name',
            'text': u'a new product translation',
            'language': 'en',
            'object': models.Product.objects.filter(store=self.vendor.vendor.store).first(),
        }

        request = self.factory.get(url)
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        if data.get('count') > 0:
            self.assertTrue(len(data.get('results')) > 0)
        else:
            self.assertTrue(len(data.get('results')) == 0)

    def test_product_detail(self):
        url = '/api/vendor/product/%s/'

        product = models.Product.actives.first()
        product_id = product.pk

        data = {
            'field': 'name',
            'text': u'a new product translation',
            'language': 'en',
            'object': product,
        }

        request = self.factory.get(url % product_id)
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'get': 'retrieve'})(request, pk=product_id)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('units', data)

    def test_product_create(self):
        url = '/api/vendor/product/'

        request = self.factory.post(url, data=json.dumps(product_data), content_type='application/json')
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'post': 'create'})(request)

        self.assertEqual(response.status_code, 201)

    def test_product_create_save_incomplete_success(self):
        url = '/api/vendor/product/?save_incomplete=true'

        request = self.factory.post(url, data=json.dumps(product_data), content_type='application/json')
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'post': 'create'})(request)

        self.assertEqual(response.status_code, 201)

    def test_product_create_save_incomplete_fail(self):
        url = '/api/vendor/product/?save_incomplete=true'

        data = product_data.copy()
        data['price_currency'] = 'USF'

        request = self.factory.post(url, data=json.dumps(data), content_type='application/json')
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'post': 'create'})(request)

        self.assertEqual(response.status_code, 202)

    def test_product_create_save_incomplete_fail_full_use_case(self):
        """
        Sends product information with errors with save_incmplete flag on. Then fix information and send it again.
        """
        url = '/api/vendor/product/?save_incomplete=true'

        data = product_data.copy()
        data['price_currency'] = 'USF'

        request = self.factory.post(url, data=json.dumps(data), content_type='application/json')
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'post': 'create'})(request)

        self.assertEqual(response.status_code, 202)

        incomplete = models.IncompleteProduct.objects.get(pk=response.data.get('id'))
        incomplete.price_currency = 'USD'

        payload = serializers.IncompleteProductDetailSerializer(incomplete).data

        url = '%s&incomplete_product=%d' % (url, incomplete.id)

        request = self.factory.post(url, data=json.dumps(payload), content_type='application/json')
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'post': 'create'})(request)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(models.IncompleteProduct.objects.filter(id=incomplete.id).first() is None)

    def test_create_product_from_incomplete(self):
        url = '/api/vendor/product/?incomplete_product=%d'

        data = product_data.copy()
        data['store'] = self.vendor.vendor.store
        incomplete_product, created = models.IncompleteProduct.objects.get_or_create(**data)

        models.Image.objects.create(name='an image', object=incomplete_product)

        url = url % incomplete_product.pk

        data.pop('store')

        data = product_data.copy()

        request = self.factory.post(url, data=json.dumps(data), content_type='application/json')
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'post': 'create'})(request)

        self.assertEqual(response.status_code, 201)

    def test_product_edit(self):
        url = '/api/vendor/product/%s/'

        product_unit = models.ProductUnit.objects.select_related('product').filter(product__is_active=True).first()
        product = product_unit.product

        data = {
            'name': get_random_name(12),
            'units': [
                {
                    'id': product_unit.id,
                    'quantity': product_unit.quantity + 1,
                    'attributes': [models.AttributeValue.objects.values_list('pk', flat=True).first()]
                },
                {
                    'sku': 'daa7894',
                    'quantity': 12,
                    'attributes': [],
                }
            ]
        }

        request = self.factory.patch(url % product.id, data=json.dumps(data), content_type='application/json')
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'patch': 'partial_update'})(request, pk=product.id)

        self.assertEqual(response.status_code, 200)

    def test_product_delete(self):
        url = '/api/vendor/product/%s/'

        product_id = models.Product.actives.values_list('pk', flat=True).first()

        request = self.factory.delete(url % product_id)
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'delete': 'destroy'})(request, pk=product_id)

        self.assertEqual(response.status_code, 204)

        url = '/api/vendor/product/'
        request = self.factory.get(url)
        force_authenticate(request, self.vendor)
        response = views.ProductViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        result = response.data.get('result') or []
        self.assertNotIn(product_id, [p.get('id') for p in result])

    def test_incomplete_product_list(self):
        url = '/api/vendor/incomplete-product/'

        data = product_data.copy()
        data['store'] = self.vendor.vendor.store
        models.IncompleteProduct.objects.get_or_create(**data)

        request = self.factory.get(url)
        force_authenticate(request, self.vendor)
        response = views.IncompleteProductViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        if data.get('count') > 0:
            self.assertTrue(len(data.get('results')) > 0)
        else:
            self.assertTrue(len(data.get('results')) == 0)

    def test_incomplete_product_detail(self):
        url = '/api/vendor/incomplete-product/%s/'

        data = product_data.copy()
        data['store'] = self.vendor.vendor.store
        product, _ = models.IncompleteProduct.objects.get_or_create(**data)

        product_id = product.id

        request = self.factory.get(url % product_id)
        force_authenticate(request, self.vendor)
        response = views.IncompleteProductViewSet.as_view({'get': 'retrieve'})(request, pk=product_id)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('units', data)

    def test_incomplete_product_update(self):
        url = '/api/vendor/incomplete-product/%s/'

        data = product_data.copy()
        data['store'] = self.vendor.vendor.store
        incomplete, _ = models.IncompleteProduct.objects.get_or_create(**data)

        units = []
        for u in incomplete.units:
            units.append(serializers.ProductUnitDumbSerializer(u).data)

        units.append(
            {'sku': 'DAA7894', 'quantity': 20}
        )

        payload = {
            'name': "%s - %s" % (incomplete.name, "EDITED"),
            'units': units,
        }

        request = self.factory.patch(url % incomplete.id, data=json.dumps(payload), content_type='application/json')
        force_authenticate(request, self.vendor)
        response = views.IncompleteProductViewSet.as_view({'patch': 'partial_update'})(request, pk=incomplete.id)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(payload.get('name'), data.get('name'))
        self.assertIn('units', data)
        self.assertEqual(len(payload.get('units')), len(data.get('units')))

    def test_inventory_list(self):
        url = '/api/vendor/inventory/'

        request = self.factory.get(url)
        force_authenticate(request, self.vendor)
        response = views.InventoryViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        if data.get('count') > 0:
            self.assertTrue(len(data.get('results')) > 0)
        else:
            self.assertTrue(len(data.get('results')) == 0)

    def test_sample_dispatch_create(self):
        url = '/api/vendor/sample-dispatch/'
        store = self.vendor.vendor.store
        showroom = models.Showroom.objects.select_related('warehouse').first()
        product = models.Product.actives.filter(store=store).first()

        units = list(product.units.all())
        if not units:
            for i in xrange(2):
                models.ProductUnit.objects.create(quantity=i, product=product)

        sample_units = []
        for unit in models.ProductUnit.objects.filter(product=product):
            sample_units.append({
                'quantity': 1,
                'product_unit': unit.id,
            })

        sample_data = {
            'warehouse': showroom.warehouse.id,
            'showroom': showroom.id,
            'samples_units': sample_units,
        }

        request = self.factory.post(url, data=json.dumps(sample_data), content_type='application/json')
        force_authenticate(request, self.vendor)
        response = views.SampleDispatchViewSet.as_view({'post': 'create'})(request)

        self.assertEqual(response.status_code, 201)
        data = response.data
        self.assertIn('warehouse', data)

    def test_sample_dispatche_list(self):
        url = '/api/vendor/sample-dispatch/'

        request = self.factory.get(url)
        force_authenticate(request, self.vendor)
        response = views.SampleDispatchViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        self.assertTrue(data.get('count') > 0)
        first = data.get('results')[0]
        self.assertIn('samples_units', first)

    def test_sample_list(self):
        url = '/api/vendor/sample/'

        request = self.factory.get(url)
        force_authenticate(request, self.vendor)
        response = views.ProductSampleViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)

    def test_attribute_list(self):
        url = '/api/vendor/attribute/'

        request = self.factory.get(url)
        force_authenticate(request, self.vendor)
        response = views.AttributeViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        self.assertTrue(data.get('count') > 0)
        first = data.get('results')[0]
        self.assertIn('name', first)

    def test_attribute_list_filter(self):
        url = '/api/vendor/attribute/?category=%d'

        category1 = models.Category.objects.filter(super_category=None).first()
        category2 = models.Category.objects.create(name='test category')

        attribute1 = models.Attribute.objects.last()
        attribute2 = models.Attribute.objects.create(name='test attribute')

        attribute1.categories.clear()
        attribute1.categories.add(category1)

        attribute2.categories.clear()
        attribute2.categories.add(category2)

        url = url % category1.id

        request = self.factory.get(url)
        force_authenticate(request, self.vendor)
        response = views.AttributeViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        self.assertTrue(data.get('count') > 0)

        all_ids = [c.get('id') for c in data.get('results')]

        self.assertNotIn(attribute2.id, all_ids)
