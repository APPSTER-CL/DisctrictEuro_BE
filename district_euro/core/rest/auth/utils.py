from django.utils import timezone
from rest_framework_jwt.serializers import api_settings as jwt_settings

from .serializers import UserLoginSerializer


def jwt_response_payload_handler(token, user=None, request=None):
    """
    Returns the response data for both the login and refresh views.
    Override to return a custom response such as including the
    serialized representation of the User.

    Example:

    def jwt_response_payload_handler(token, user=None, request=None):
        return {
            'token': token,
            'user': UserSerializer(user).data
        }

    """
    return {
        'token': token,
        'token_expiration': timezone.now() + jwt_settings.JWT_EXPIRATION_DELTA,
        'user': UserLoginSerializer(user).data,
    }
