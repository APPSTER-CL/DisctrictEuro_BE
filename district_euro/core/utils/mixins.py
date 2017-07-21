from rest_framework.response import Response
from rest_framework import serializers

class PartialUpdateModelMixin(object):
    """
    Partial updates a model instance.
    """

    def partial_update(self, request, *args, **kwargs):
        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def perform_update(self, serializer):
        serializer.save()


class UserViewMixin(object):
    def get_user_id(self):
        return self.request.user.id

    def get_user(self):
        return self.request.user


class QueryParamMixin(object):
    def get_query_param(self, key, default=None):
        if hasattr(self, 'request') and hasattr(self.request, 'query_params') and hasattr(self.request.query_params,
                                                                                          'get'):
            return self.request.query_params.get(key, default)
        return default

    def get_query_param_int(self, key, default=None, raise_exception=True):
        param = self.get_query_param(key, default)
        if param is not None:
            try:
                return int(param)
            except:
                raise serializers.ValidationError('%s field must be an integer' % key)
        return param
