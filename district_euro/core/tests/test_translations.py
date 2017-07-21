# from django.test import TestCase
# from django.utils.translation import activate
#
# from core import models
#
# class TranslationTestCase(TestCase):
#     fixtures = ('initial_data.yaml',)
#
#     def test_product_translation(self):
#         product = models.Product.objects.first()
#
#         activate('en')
#         name = product.trans.name
#
#         self.assertEqual(name, name_es)
#
#     def test_store_translation(self):
#         store = models.Store.objects.first()
#         data = {
#             'field': 'name',
#             'text': u'a new store translation',
#             'language': 'en',
#             'object': store,
#         }
#         Translation.objects.create(**data)
#
#         activate('en')
#         name = store.trans.name
#
#         self.assertEqual(name, data.get('text'))
