from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


status_code_field = 'status_code'
detail_field = 'detail'


def _make_payload(detail=None, status_code=None):
    ret = {}
    if detail:
        ret[detail_field] = detail
    if status_code:
        ret[status_code_field] = status_code
    return ret


def _make_response(detail=None, status_code=None):
    data = _make_payload(detail, status_code)
    return Response(data, status=status_code)


def core_exception_handler(exc, context):
    ret = None

    response = exception_handler(exc, context)
    if response is not None:
        return _make_response(response.data, response.status_code)

    if isinstance(exc, Http404):
        ret = _make_response(str(exc) or 'Not found', status.HTTP_404_NOT_FOUND)
    elif not settings.IS_TESTING:
        logger.error('Uncatched Exception raised: %s', str(exc))
        ret = _make_response(str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    return ret
