from django.test import TestCase
from rest_framework.test import APIRequestFactory

from core import models
from core.rest.auth.views import obtain_jwt_token


class VendorTestCase(TestCase):
    fixtures = ('initial_data.yaml',)

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_login(self):
        user = models.User.objects.first()
        password = 'password'
        user.set_password(password)
        user.save()

        url = '/account/login/'

        request = self.factory.post(url, data={'email': user.email, 'password': password})
        response = obtain_jwt_token(request)

        self.assertEqual(response.status_code, 200)
