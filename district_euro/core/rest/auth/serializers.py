from rest_framework import serializers
from core.rest.common.serializers import ImageSerializer
from core import models


class UserLoginSerializer(serializers.ModelSerializer):
    profiles = serializers.ListSerializer(child=serializers.CharField())
    image = ImageSerializer()

    class Meta:
        model = models.User
        fields = ('email', 'first_name', 'last_name', 'profiles', 'image')
