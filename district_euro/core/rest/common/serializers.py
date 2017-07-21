from rest_framework import serializers

from core import models
from core.utils.fields import MoneyField


class ThinImageSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = models.Image
        fields = ('id', 'name', 'url')

    def get_name(self, obj):
        return obj.name.split('/')[-1]


class ImageSerializer(ThinImageSerializer):
    class Meta:
        model = models.Image
        fields = ('id', 'name', 'url', 'small_url', 'portrait_url', 'landscape_url')


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    status_id = serializers.CharField(source='status')
    total_price = serializers.CharField()
    consumer_full_name = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    class Meta:
        model = models.Order
        fields = ('id', 'total_price', 'tracking_number', 'created', 'shipping_address', 'status', 'status_id',
                  'total_quantity', 'consumer_full_name')

    def get_status(self, obj):
        return models.Order.STATUS_DICT.get(obj.status)

    def get_consumer_full_name(self, obj):
        return obj.consumer.user.get_full_name()

    def get_id(self, obj):
        return "%05d" % obj.id


class OrderItemSerializer(serializers.ModelSerializer):
    total_price = serializers.CharField()
    unit_price = serializers.CharField()
    image = ImageSerializer(source='product_unit.product.image')

    class Meta:
        model = models.OrderItem
        fields = ('sku', 'name', 'description', 'unit_price', 'total_price', 'quantity', 'attributes', 'image')


class ConsumerOrderSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source='user.email')
    full_name = serializers.SerializerMethodField()
    phone = serializers.CharField(source='phone_number')

    class Meta:
        model = models.Consumer
        fields = ('email', 'full_name', 'phone')

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class OrderDetailSerializer(OrderSerializer):
    order_items = OrderItemSerializer(many=True)
    consumer = ConsumerOrderSerializer()

    class Meta:
        model = models.Order
        fields = ('id', 'total_price', 'tracking_number', 'created', 'shipping_address', 'status', 'status_id',
                  'total_quantity', 'order_items', 'consumer')


class SimpleCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = ('id', 'name',)


class StoreSerializer(serializers.ModelSerializer):
    categories = SimpleCategorySerializer(many=True)
    logo = ImageSerializer(source='image', read_only=True)

    class Meta:
        fields = ('id', 'name', 'description', 'logo', 'categories')
        model = models.Store


class ProductSerializer(serializers.ModelSerializer):
    store = serializers.SlugRelatedField(slug_field='name', read_only=True)
    price_amount = MoneyField(source='price.amount')
    price_currency = serializers.CharField(source='price.currency')
    image = ImageSerializer()

    class Meta:
        model = models.Product
        fields = ('id', 'store', 'name', 'description', 'price_amount', 'price_currency', 'image')


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute.name')

    class Meta:
        model = models.AttributeValue
        fields = ('id', 'attribute_name', 'value')


class ProductUnitSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    attributes = AttributeValueSerializer(many=True)

    class Meta:
        model = models.ProductUnit
        fields = ('id', 'sku', 'quantity', 'attributes')

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError('quantity must be grater than zero')
        return value


class PropertySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = models.Attribute
        fields = ('id', 'name', 'image_url')

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.small_url or obj.image.url


class ProductDetailSerializer(ProductSerializer):
    images = ImageSerializer(many=True)
    units = ProductUnitSerializer(many=True)
    category = serializers.StringRelatedField()
    properties = PropertySerializer(many=True)
    infographics = ThinImageSerializer(many=True, read_only=True)
    stock_quantity = serializers.IntegerField(read_only=True)
    store = StoreSerializer(read_only=True)

    class Meta:
        model = models.Product
        fields = (
            'id', 'store', 'name', 'description', 'category', 'price_amount', 'price_currency', 'image',
            'amount_reviews', 'mean_qualification', 'sold_quantity', 'stock_quantity', 'properties',
            'infographics', 'images', 'units')


class ProductSampleSerializer(serializers.ModelSerializer):
    product = serializers.IntegerField(source='product_unit.product.id', read_only=True)
    sku = serializers.CharField(source='product_unit.sku', read_only=True)
    name = serializers.CharField(source='product_unit.product.name', read_only=True)
    quantity = serializers.IntegerField()
    warehouse = serializers.CharField(source='warehouse.name', read_only=True)

    class Meta:
        model = models.Sample
        fields = ('id', 'sku', 'name', 'quantity', 'warehouse', 'product')


class SampleSerializer(ProductSampleSerializer):
    attributes = AttributeValueSerializer(many=True, source='product_unit.attributes')

    class Meta:
        model = models.Sample
        fields = ('id', 'sku', 'name', 'quantity', 'warehouse', 'attributes')


class AttributeSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = models.Attribute
        fields = ('id', 'name', 'is_boolean', 'image_url')

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.small_url or obj.image.url


class AttributeValueListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.AttributeValue
        fields = ('id', 'value')


class AttributeDetailSerailzer(AttributeSerializer):
    values = AttributeValueListSerializer(many=True)

    class Meta:
        model = models.Attribute
        fields = ('id', 'name', 'is_boolean', 'image_url', 'values')


class ProductSampleUnitReadsSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='product_unit.product.name')
    sku = serializers.CharField(source='product_unit.sku')

    class Meta:
        model = models.ProductSampleUnits
        fields = ('quantity', 'name', 'sku')


class WarehouseSerializer(serializers.ModelSerializer):
    city = serializers.SlugRelatedField(slug_field='name', read_only=True)
    country = serializers.SlugRelatedField(slug_field='name', read_only=True)

    class Meta:
        model = models.Warehouse
        fields = ('id', 'name', 'address', 'city', 'country')


class SampleDispatchSerializer(serializers.ModelSerializer):
    warehouse = WarehouseSerializer(read_only=True)
    status = serializers.SerializerMethodField(read_only=True)
    status_id = serializers.CharField(source='status')
    samples_units = ProductSampleUnitReadsSerializer(many=True)
    id = serializers.SerializerMethodField()
    store = serializers.SlugRelatedField(slug_field='name', read_only=True)

    class Meta:
        model = models.SampleDispatch
        fields = ('id', 'created', 'warehouse', 'status', 'status_id', 'samples_units', 'tracking_number',
                  'shipping_company', 'store')

    def get_status(self, obj):
        return obj.STATUS_DICT.get(obj.status)

    def get_id(self, obj):
        return "%05d" % obj.id


class ShowroomSerializer(serializers.ModelSerializer):
    city = serializers.SlugRelatedField(slug_field='name', read_only=True)
    country = serializers.SlugRelatedField(slug_field='name', read_only=True)
    image = ImageSerializer()

    class Meta:
        model = models.Showroom
        fields = ('id', 'name', 'description', 'city', 'country', 'address', 'image')


class ShowroomDetailSerializer(ShowroomSerializer):
    class Meta:
        model = models.Showroom
        fields = ('id', 'name', 'description', 'city', 'country', 'address', 'latitude', 'longitude', 'image')
