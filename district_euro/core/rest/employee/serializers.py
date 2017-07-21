from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core import models


class SampleTransferSerializer(serializers.Serializer):
    showroom = serializers.PrimaryKeyRelatedField(queryset=models.Showroom.objects.all(), required=False, allow_null=True)
    quantity = serializers.IntegerField(required=True)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError(_('Quantity should be grater than 0'))
        return value

    def validate(self, attrs):
        if self.context is None or not isinstance(self.context, dict) or 'sample' not in self.context:
            raise Exception('Need sample to validate sample transfer')
        sample = self.context.get('sample')
        destiny = attrs.get('showroom', None) or sample.warehouse
        if isinstance(destiny, type(sample.location)):
            raise serializers.ValidationError('Cannot transfer sample to same type of location')
        if sample.quantity < attrs.get('quantity'):
            raise serializers.ValidationError(_('Not enough quantity'))
        return attrs


class SampleSerializer(serializers.ModelSerializer):
    sku = serializers.CharField(source='product_unit.sku')
    name = serializers.CharField(source='product_unit.product.name')
    description = serializers.CharField(source='product_unit.product.description')
    location_type = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    store = serializers.CharField(source='product_unit.product.store.name')
    store_id = serializers.IntegerField(source='product_unit.product.store_id')

    class Meta:
        model = models.Sample
        fields = ('id', 'quantity', 'sku', 'name', 'description', 'location_type', 'location_name', 'store', 'store_id')

    def get_location_type(self, obj):
        if obj.location is not None:
            return obj.location.__class__.__name__
        return None

    def get_location_name(self, obj):
        if obj.location is not None:
            return unicode(obj.location)
        return None
