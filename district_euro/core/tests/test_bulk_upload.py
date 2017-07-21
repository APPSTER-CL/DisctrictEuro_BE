from django.test import TestCase

from core.product.bulk_upload import process_product_row

product_row = [
    '15',
    'KJA789',
    'Product Name',
    'Product Description',
    '109.99',
    'US Dollar - USD',
    'Men - Pijamas',
    'Black',
    'M',
]


class BulkUploadLogicTest(TestCase):
    fixtures = ('initial_data.yaml',)

    def test_process_product_row_success(self):
        data, errors = process_product_row(product_row, 'wear')
        self.assertIsNone(errors)

    def test_process_product_row_errors(self):
        row = [c for c in product_row]
        row[6] = 'Men - aosd'
        data, errors = process_product_row(row, 'wear')
        self.assertIsNotNone(errors)
        self.assertIn('category', errors)
