import moneyed
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from core.models import _max_digits, _decimal_places, AttributeValue, Category


class GeneralProductSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(required=True)
    sku = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    price_amount = serializers.DecimalField(max_digits=_max_digits, decimal_places=_decimal_places, required=True)
    price_currency = serializers.CharField(required=True)
    category = serializers.CharField(required=True)

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError()
        return value

    def validate_price_currency(self, value):
        obj, error = self.get_currency(value)
        if obj is None:
            raise serializers.ValidationError(error)
        return obj

    def get_currency(self, value):
        try:
            code = value.split()[-1]
            moneyed.get_currency(code)
            return code, None
        except:
            raise None, _("Invalid Currency")

    def validate_category(self, value):
        obj, error = self.get_category(value)
        if obj is None:
            raise serializers.ValidationError(error)
        return obj

    def get_category(self, value):
        try:
            subcategory = value.split()[-1]
        except Exception as e:
            return None, _('Category does not exists')
        obj = Category.objects.filter(name__iexact=subcategory).first()
        if obj is None:
            return None, _('Category does not exists')
        return obj, None

    def validate(self, attrs):
        validated_data = super(GeneralProductSerializer, self).validate(attrs)
        return self.format_data(validated_data)

    @property
    def data(self):
        if not hasattr(self, '_data'):
            data = super(GeneralProductSerializer, self).data
            self._data = self.format_data(data)
        return self._data

    def format_data(self, data):
        quantity = data.pop('quantity', 0)
        sku = data.pop('sku')

        if sku or quantity:
            data['units'] = [
                {
                    'sku': sku,
                    'quantity': quantity,
                    'attributes': []
                }
            ]
        else:
            data['units'] = []

        category = data.get('category', None)
        if not isinstance(category, Category):
            category, errors = self.get_category(category)
        data['category'] = category.id if category is not None else None

        currency = data.get('price_currency')
        if currency is not None and len(currency.split()) > 0:
            currency, errors = self.get_currency(currency)
        data['price_currency'] = currency

        return data


class WearSerializer(GeneralProductSerializer):
    color = serializers.CharField(required=True)
    size = serializers.CharField(required=True)

    def format_data(self, data):
        """
        Adds size and color to the units if it exists. This method only cares about size and color, the other fields are
        formated in super class.
        """
        data = super(WearSerializer, self).format_data(data)
        color = data.pop('color')
        size = data.pop('size')

        queryset = AttributeValue.objects.values_list('pk', flat=True)
        color_attribute_id = queryset.filter(value=color, attribute_name__iexact='color').first()
        size_attribute_id = queryset.filter(value=size, attribute_name__iexact='size').first()

        attributes = []
        if color_attribute_id:
            attributes.append(color_attribute_id)
        if size_attribute_id:
            attributes.append(size_attribute_id)

        if (size_attribute_id or color_attribute_id) and data.get('units'):
            data['units'][0].update({
                'attributes': attributes
            })

        return data
