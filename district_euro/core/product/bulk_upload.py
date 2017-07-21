from .bulk_upload_validators import WearSerializer, GeneralProductSerializer

_columns_by_sheets = {
    'wear': list(WearSerializer().fields.iterkeys()),
    'general': list(GeneralProductSerializer().fields.iterkeys())
}

_serializers_by_sheet = {
    'wear': WearSerializer,
    'general': GeneralProductSerializer
}


def get_serializer_class(sheet):
    return _serializers_by_sheet.get(sheet)


def is_sheet_valid(sheet):
    return sheet in _columns_by_sheets


def get_sheet_columns(sheet):
    return _columns_by_sheets.get(sheet)


def _is_empty_list(row):
    ret = True
    for item in row:
        ret = ret and bool(item is None or not item)
        if not ret:
            return False
    return ret


def process_product_row(row, sheet):
    """
    Parse a row from the bulk upload file and returns validated data and errors
    if exists.

    :type row: workbook.sheet.row
    :param row: a row of the file

    :type sheet: str
    :param sheet: the sheet of the workbook the row belongs to.

    :rtype: tuple(dict, list)
    :return a dict with data or validated data and a list of errors or None if
        no errors.
    """
    assert is_sheet_valid(sheet), 'sheet must be a valid sheet'
    if not isinstance(row, list):
        row = map(lambda cell: cell.value, row)
    if _is_empty_list(row):
        raise Exception("Empty row")
    data = dict(zip(get_sheet_columns(sheet), row))
    serializer = get_serializer_class(sheet)(data=data)
    if serializer.is_valid():
        return serializer.validated_data, None
    else:
        return serializer.data, serializer.errors
