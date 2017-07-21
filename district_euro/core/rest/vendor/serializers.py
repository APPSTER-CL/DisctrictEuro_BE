import moneyed
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.reverse import reverse

from core import models
from core.exceptions import NotEnoughStockError
from core.image import delete_image
from core.rest.common import serializers as common
from core.utils.fields import MoneyField


class OrderUpdateSerializer(serializers.Serializer):
    """
    Used to update shipping information of an order.
    """
    status = serializers.CharField(required=False, allow_null=True)
    shipping_company = serializers.CharField(required=False, allow_null=True)
    tracking_number = serializers.CharField(required=False, allow_null=True)

    def validate_status(self, value):
        if value not in models.Order.STATUS_DICT:
            raise serializers.ValidationError('Invalid status')
        return value

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError('Must provide al least one value')
        return attrs

    def update(self, instance, validated_data):
        for k in [k for k in validated_data.iterkeys()]:
            if validated_data.get(k) is None:
                validated_data.pop(k)
        models.Order.objects.filter(pk=instance.pk).update(**validated_data)
        return models.Order.objects.get(pk=instance.pk)


class ProductSerializer(serializers.ModelSerializer):
    """
    Used to list products of a vendor.
    """
    price = serializers.CharField()
    image = common.ImageSerializer(read_only=True)

    class Meta:
        model = models.Product
        fields = ('id', 'name', 'description', 'price', 'image', 'is_approved')


class AttributeDetailSerializer(serializers.ModelSerializer):
    value = serializers.IntegerField(source='id', read_only=True, help_text=_('Id of AttributeValue'))
    attribute = serializers.PrimaryKeyRelatedField(read_only=True, help_text=_('Id of Attribute'))

    class Meta:
        model = models.AttributeValue
        fields = ('value', 'attribute')


class ProductUnitDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    attributes = AttributeDetailSerializer(many=True)

    class Meta:
        model = models.ProductUnit
        fields = ('id', 'sku', 'quantity', 'attributes')


class ProductDetailSerializer(serializers.ModelSerializer):
    price_amount = MoneyField(source='price.amount')
    price_currency = serializers.CharField(source='price.currency')
    units = ProductUnitDetailSerializer(many=True)
    id = serializers.IntegerField(read_only=True)
    images = common.ImageSerializer(many=True, read_only=True)
    image = common.ImageSerializer(read_only=True)
    properties = serializers.SerializerMethodField()
    infographics = common.ThinImageSerializer(many=True, read_only=True)

    class Meta:
        model = models.Product
        fields = ('id', 'name', 'description', 'price_amount', 'price_currency', 'category', 'properties',
                  'is_approved', 'units', 'image', 'images', 'infographics')

    def validate_price_currency(self, value):
        try:
            moneyed.get_currency(value)
        except moneyed.CurrencyDoesNotExist:
            raise serializers.ValidationError('Invalid price_currency')
        return value

    def get_properties(self, obj):
        return map(lambda x: x.id, list(obj.attributes.all()))


class ProductUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductUnit
        fields = ('sku', 'quantity', 'attributes')

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError('quantity must be grater than zero')
        return value


class ProductCreateSerializer(ProductDetailSerializer):
    units = ProductUnitSerializer(many=True)
    properties = serializers.ListSerializer(child=serializers.IntegerField(), write_only=True, required=False)
    is_approved = serializers.BooleanField(read_only=True)

    class Meta:
        model = models.Product
        fields = ('id', 'name', 'description', 'price_amount', 'price_currency', 'category', 'units', 'images',
                  'properties', 'is_approved')

    def create(self, validated_data):
        incomplete_product_pk = self.context.get('incomplete_product_pk', None)
        with transaction.atomic():
            units = validated_data.pop('units')
            validated_data['price'] = moneyed.Money(**validated_data.pop('price'))
            properties = validated_data.pop('properties', [])
            product = models.Product.objects.create(**validated_data)
            product.attributes.add(*list(models.Attribute.objects.filter(pk__in=properties)))

            for unit in units:
                attributes = unit.pop('attributes')
                unit['product'] = product
                obj = models.ProductUnit.objects.create(**unit)
                if attributes:
                    obj.attributes.add(*attributes)

            # If this product is created from an incomplete product then i have to delete the incomplete and
            # get its images.
            if incomplete_product_pk:
                incomplete_product = get_object_or_404(models.IncompleteProduct.objects, pk=incomplete_product_pk)
                product.image = incomplete_product.image
                for image in incomplete_product.images.all():
                    image.object = product
                    image.save()
                incomplete_product.delete()

        return product

    def validate(self, attrs):
        validated = super(ProductCreateSerializer, self).validate(attrs)
        user = self.context.get('user', None)
        if user is None:
            raise Exception('Needs user instnace to validate ProductCreateSerializer')
        validated['store'] = user.vendor.store
        return validated


class ProductUnitUpdateSerializer(ProductUnitSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = models.ProductUnit
        fields = ('id', 'sku', 'quantity', 'attributes')


class ProductUpdateSerializer(ProductDetailSerializer):
    units = ProductUnitUpdateSerializer(many=True)
    remove_images = serializers.ListSerializer(child=serializers.IntegerField(), allow_null=True, write_only=True)
    remove_infographics = serializers.ListSerializer(child=serializers.IntegerField(), allow_null=True, write_only=True)
    properties = serializers.ListSerializer(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = models.Product
        fields = ('id', 'name', 'description', 'price_amount', 'price_currency', 'category', 'units', 'is_approved',
                  'images', 'remove_images', 'remove_infographics', 'properties')

    def validate(self, attrs):
        price_amount = attrs.get('price_currency')
        price_currency = attrs.get('price_currency')
        if [p for p in [price_amount, price_currency] if p is not None]:
            raise serializers.ValidationError(
                'price_amount and price_currency are required if one or the other is changed')
        return super(ProductUpdateSerializer, self).validate(attrs)

    def update(self, instance, validated_data):
        with transaction.atomic():
            remove_images = validated_data.pop('remove_images', [])
            remove_infographics = validated_data.pop('remove_infographics', [])
            properties = validated_data.pop('properties', [])
            units = validated_data.pop('units')
            if 'price' in validated_data:
                validated_data['price'] = moneyed.Money(**validated_data.pop('price'))
            models.Product.objects.filter(pk=instance.pk).update(**validated_data)

            product = models.Product.objects.prefetch_related('units').get(pk=instance.pk)

            product.attributes.clear()
            product.attributes.add(*list(models.Attribute.objects.filter(pk__in=properties)))

            product_units = product.units.all()
            product_units_by_id = {}
            for unit in product_units:
                product_units_by_id[unit.id] = unit

            for image_pk in remove_infographics:
                product.infographics.remove(image_pk)

            if remove_images + remove_infographics:
                for image_pk in remove_images:
                    delete_image(image_pk)

            for unit in units:
                attributes = unit.pop('attributes', [])
                if 'id' in unit:
                    obj = product_units_by_id.get(unit.pop('id'))
                    if unit:
                        models.ProductUnit.objects.filter(pk=obj.pk).update(**unit)
                        obj = models.ProductUnit.objects.get(pk=obj.pk)
                    if attributes:
                        obj.attributes.clear()
                else:
                    unit['product'] = product
                    obj = models.ProductUnit.objects.create(**unit)
                if attributes:
                    obj.attributes.add(*attributes)
        return product


class ProductUnitDumbSerializer(serializers.ModelSerializer):
    attributes = serializers.ListSerializer(child=serializers.IntegerField())

    class Meta:
        model = models.ProductUnit
        fields = ('sku', 'quantity', 'attributes')


class IncompleteProductCreateSerializer(serializers.ModelSerializer):
    units = ProductUnitDumbSerializer(many=True)
    price = serializers.SerializerMethodField(read_only=True)
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = models.IncompleteProduct
        fields = ('id', 'name', 'description', 'price_amount', 'price_currency', 'price', 'category', 'units')

    def create(self, validated_data):
        # Attempt to create an actual product first.
        product_serializer = ProductCreateSerializer(data=validated_data, context=self.context)
        if product_serializer.is_valid():
            return product_serializer.save()

        validated_data['errors'] = product_serializer.errors

        # Else creates an incomplete product
        return models.IncompleteProduct.objects.create(**validated_data)

    def validate(self, attrs):
        validated = super(IncompleteProductCreateSerializer, self).validate(attrs)
        user = self.context.get('user', None)
        if user is None:
            raise Exception('Needs user instnace to validate ProductCreateSerializer')
        validated['store'] = user.vendor.store
        return validated

    def get_price(self, obj):
        try:
            moneyed.get_currency(obj.price_currency)
        except:
            currency_valid = False
        else:
            currency_valid = True
        if not currency_valid:
            return str(obj.price_amount) if obj.price_amount else None
        return moneyed.Money(obj.price_amount, moneyed.get_currency(obj.price_currency))


class IncompleteProductSerializer(serializers.ModelSerializer):
    """
    Used to list incomplete products.
    """
    error_fields = serializers.SerializerMethodField()

    class Meta:
        model = models.IncompleteProduct
        fields = ('id', 'name', 'units', 'description', 'price_currency', 'price_amount', 'error_fields')

    def get_error_fields(self, obj):
        errors = []
        try:
            if obj.errors:
                for k, v in obj.errors.iteritems():
                    errors.append(k)
        except:
            pass
        return errors


class UnitSerializer(serializers.JSONField):
    def to_representation(self, value):
        if 'attributes' in value:
            attributes = []
            for a in models.AttributeValue.objects.filter(id__in=value.get('attributes')):
                attributes.append({
                    'value': a.id,
                    'attribtue': a.attribute_id,
                })
            value['attribtues'] = attributes
        return value


class IncompleteProductDetailSerializer(serializers.ModelSerializer):
    """
    Use to detail an incomplete product
    """
    units = serializers.ListSerializer(child=UnitSerializer())
    image = common.ImageSerializer(read_only=True)
    images = common.ImageSerializer(read_only=True,
                                    many=True)  # serializers.ListSerializer(child=serializers.SlugRelatedField(slug_field='url', read_only=True))

    class Meta:
        model = models.IncompleteProduct
        fields = (
            'id', 'name', 'description', 'price_currency', 'price_amount', 'category', 'units', 'errors', 'image',
            'images')


class IncompleteProductUpdateSerializer(serializers.ModelSerializer):
    """
    Use to update incomplete product information without trying to save it as an actual product.
    """
    id = serializers.IntegerField(read_only=True)
    images = serializers.ListSerializer(child=serializers.SlugRelatedField(slug_field='url', read_only=True))
    errors = serializers.JSONField(read_only=True)

    class Meta:
        model = models.IncompleteProduct
        fields = (
            'id', 'name', 'description', 'price_currency', 'price_amount', 'category', 'units', 'errors', 'images')

    def update(self, instance, validated_data):
        with transaction.atomic():
            untis_errors = []
            for unit in validated_data.get('units'):
                unit_serializer = ProductUnitDumbSerializer(data=unit)
                if not unit_serializer.is_valid():
                    untis_errors.append(unit_serializer.errors)

            models.IncompleteProduct.objects.filter(pk=instance.pk).update(**validated_data)
            instance = models.IncompleteProduct.objects.get(pk=instance.pk)

            product_data = IncompleteProductDetailSerializer(instance).data
            product_data.pop('errors')
            product_data.pop('images')

            product_serializer = ProductCreateSerializer(data=product_data, context=self.context)
            product_serializer.is_valid()

            instance.errors = product_serializer.errors
            if untis_errors:
                instance.errors['units'] = untis_errors
            instance.save()
        return instance

    def validate(self, attrs):
        user = self.context.get('user', None)
        if user is None:
            raise Exception('Needs user instnace to validate ProductCreateSerializer')
        return super(IncompleteProductUpdateSerializer, self).validate(attrs)


class ProductSampleUnitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductSampleUnits
        fields = ('quantity', 'product_unit')

    def validate(self, attrs):
        validated_data = super(ProductSampleUnitsSerializer, self).validate(attrs)
        quantity = validated_data.get('quantity')
        product_unit = validated_data.get('product_unit')
        if quantity > product_unit.quantity:
            raise serializers.ValidationError('Sample quantity must be lesser than stock available')
        return validated_data

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be grater than zero')
        return value


class SampleDispatchUpdateSerializer(serializers.ModelSerializer):
    status_name = serializers.SerializerMethodField()
    status = serializers.CharField(required=False, allow_null=True)
    shipping_company = serializers.CharField(required=False, allow_null=True)
    tracking_number = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = models.SampleDispatch
        fields = ('id', 'status', 'tracking_number', 'shipping_company', 'status_name')

    def validate_status(self, value):
        if value not in models.SampleDispatch.STATUS_DICT:
            raise serializers.ValidationError('Invalid status')
        return value

    def update(self, instance, validated_data):
        for k in [k for k in validated_data.iterkeys()]:
            if validated_data.get(k) is None:
                validated_data.pop(k)
        models.SampleDispatch.objects.filter(pk=instance.pk).update(**validated_data)
        return models.SampleDispatch.objects.get(pk=instance.pk)

    def get_status_name(self, obj):
        return obj.STATUS_DICT.get(obj.status)


class SampleDispatchCreateSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField(read_only=True)
    samples_units = ProductSampleUnitsSerializer(many=True)

    class Meta:
        model = models.SampleDispatch
        fields = ('warehouse', 'status', 'samples_units', 'tracking_number', 'shipping_company')

    def get_status(self, obj):
        return obj.STATUS_DICT.get(obj.status)

    def validate(self, attrs):
        assert self.context and 'user' in self.context, \
            "SampleDispatchSerializer requires the user in the context"

        validated_data = super(SampleDispatchCreateSerializer, self).validate(attrs)

        # Store is unique for vendor
        store = self.context.get('user').vendor.store

        validated_data['store'] = store

        return validated_data

    def create(self, validated_data):
        with transaction.atomic():
            samples_units = validated_data.pop('samples_units')

            sample_dispatch = models.SampleDispatch.objects.create(**validated_data)

            for sample in samples_units:
                sample['sample_dispatch'] = sample_dispatch

                # Check if stock is enough. If not then invalidates the entire sample dispatch creation.
                sample_quantity = sample.get('quantity')
                product_unit = models.ProductUnit.objects.filter(pk=sample.get('product_unit').id).first() #TODO: Must select_for_update() \


                if product_unit.quantity < sample_quantity:
                    raise NotEnoughStockError('Not enough stock of %s' % unicode(product_unit))

                product_unit.quantity -= sample_quantity
                product_unit.save()

                models.ProductSampleUnits.objects.create(**sample)

        return sample_dispatch


class InventorySerializer(serializers.ModelSerializer):
    is_approved = serializers.IntegerField(source='product.is_approved')
    product_id = serializers.IntegerField(source='product.id')
    name = serializers.SlugRelatedField(slug_field='name', source='product', read_only=True)
    description = serializers.SlugRelatedField(slug_field='description', source='product', read_only=True)
    price = serializers.CharField(source='product.price')
    attributes = common.AttributeValueSerializer(many=True)
    product_detail_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.ProductUnit
        fields = ('id', 'product_id', 'sku', 'name', 'description', 'price', 'quantity', 'attributes', 'is_approved',
                  'product_detail_url')

    def get_product_detail_url(self, obj):
        return reverse('product-detail', kwargs={'pk': obj.product.pk}, request=self.context.get('request'))


class PeriodOverviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PeriodOverview
        fields = ('date_from', 'date_to', 'value', 'aggregate_value')
