from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import APIException


class NotEnoughStockError(APIException):
    status_code = 400
    default_detail = _('Not enough stock')


class FileTooBigException(APIException):
    status_code = 400
    default_detail = _('File is too big')


class InvalidImageFileException(APIException):
    status_code = 400
    default_detail = _('File is not an image')
