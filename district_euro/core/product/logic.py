import logging

from openpyxl import load_workbook

from .bulk_upload import process_product_row, is_sheet_valid

logger = logging.getLogger(__name__)


def bulk_product_upload(file, user):
    """
    Uploads products specified in file.

    :type file: readable file stream
    :param file: the file that contains products information

    :type user: models.User
    :param user: the user that is requesting the upload.

    :rtype: dict
    :return: a dict with products divided by sheet.
    """
    if file is None:
        return {}

    wb = load_workbook(file, read_only=True)

    products_by_sheet = {}
    for sheet in wb.get_sheet_names():
        current_sheet = []
        if not is_sheet_valid(sheet):
            continue
        ws = wb.get_sheet_by_name(sheet)

        is_first_row = True
        for row in ws.rows:

            if is_first_row:
                is_first_row = False
                continue
            try:
                product, errors = process_product_row(row, sheet)
            except Exception as e:
                continue
            product['errors'] = errors
            current_sheet.append(product)

        products_by_sheet[sheet] = current_sheet
    return products_by_sheet
