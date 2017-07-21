import json

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from core import models
from landing import models as landing_models
from core.rest.other import views


class OtherTestCase(TestCase):
    fixtures = ('initial_data.yaml',)

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_order_staus_list(self):
        url = '/api/order/status/'

        request = self.factory.get(url)
        response = views.ShippingStatusView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)

    def test_currency_list(self):
        url = '/api/currency/'

        request = self.factory.get(url)
        response = views.CurrencyListView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)

    def test_product_list(self):
        url = '/api/product/'

        request = self.factory.get(url)
        response = views.ProductViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        if data.get('count') > 0:
            self.assertTrue(len(data.get('results')) > 0)
        else:
            self.assertTrue(len(data.get('results')) == 0)

    def test_product_detail(self):
        url = '/api/product/%s/'

        product_id = models.Product.actives.values_list('pk', flat=True).filter(is_approved=True).first()

        request = self.factory.get(url % product_id)
        response = views.ProductViewSet.as_view({'get': 'retrieve'})(request, pk=product_id)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('units', data)
        # TODO: test other fields

    def test_country_list(self):
        url = '/api/country/'

        request = self.factory.get(url)
        response = views.CountryViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        if data.get('count') > 0:
            self.assertTrue(len(data.get('results')) > 0)
        else:
            self.assertTrue(len(data.get('results')) == 0)

    def test_country_detail(self):
        url = '/api/country/%d/'

        country = models.Country.objects.first()
        if country is None:
            raise Exception('Country object needed for testing')
        country_id = country.pk

        url = url % country_id

        request = self.factory.get(url)
        response = views.CountryViewSet.as_view({'get': 'retrieve'})(request, pk=country_id)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('images', data)

    def test_country_region_list(self):
        url = '/api/country/%d/regions/'

        region = models.Region.objects.first()
        if region is None:
            raise Exception('Region object needed for testing')
        country_id = region.city.country_id

        url = url % country_id

        request = self.factory.get(url)
        response = views.CountryViewSet.as_view({'get': 'regions'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        if data.get('count') > 0:
            self.assertTrue(len(data.get('results')) > 0)
        else:
            self.assertTrue(len(data.get('results')) == 0)

    def test_country_popular_products(self):
        url = '/api/country/%d/popular-products/'

        country = models.Country.objects.first()
        if country is None:
            raise Exception('Country object needed for testing')
        country_id = country.pk

        url = url % country_id

        request = self.factory.get(url)
        response = views.CountryViewSet.as_view({'get': 'popular_products'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIsInstance(data, list)

    def test_region_detail(self):
        url = '/api/city/%s/'

        region = models.Region.objects.first()
        if region is None:
            raise Exception('Region object needed for testing')

        request = self.factory.get(url % region.id)
        response = views.RegionViewSet.as_view({'get': 'retrieve'})(request, pk=region.id)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('stores', data)
        # TODO: test other fields

    def test_showroom_list(self):
        url = '/api/showroom/'

        request = self.factory.get(url)
        response = views.ShowroomViewSet.as_view({'get': 'list'})(request)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('count', data)
        if data.get('count') > 0:
            self.assertTrue(len(data.get('results')) > 0)
        else:
            self.assertTrue(len(data.get('results')) == 0)

    def test_showroom_detail(self):
        url = '/api/showroom/%s/'

        showroom = models.Showroom.objects.first()
        if showroom is None:
            raise Exception('Showroom object needed for testing')

        request = self.factory.get(url % showroom.pk)
        response = views.ShowroomViewSet.as_view({'get': 'retrieve'})(request, pk=showroom.pk)

        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertIn('address', data)

    def test_join_request_add(self):
        url = '/api/join-request/'

        join_request_count = landing_models.JoinRequest.objects.count()

        data = {
            'name': 'Joaquin',
            'website_url': 'www.example.com',
            'email': 'joaquin@example.com',
            'phone_number': '+59899123456',
            'address': 'P. Sharmen 47',
            'products_description': 'We sell classic products from Wantanamera',
            'business_description': 'Local business specialiced on food',
        }

        request = self.factory.post(url, data=json.dumps(data), content_type='application/json')
        response = views.JoinRequestViewSet.as_view({'post': 'create'})(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(join_request_count + 1, landing_models.JoinRequest.objects.count())






