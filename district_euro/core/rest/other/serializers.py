from rest_framework import serializers

from core import models
from core.rest.common.serializers import ImageSerializer, ThinImageSerializer, StoreSerializer
from landing import models as landing_models


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = models.Category
        fields = ('id', 'name', 'subcategories',)

    def get_subcategories(self, obj):
        return self.__class__(obj.subcategories.all(), many=True).data


class WarehouseSerializer(serializers.ModelSerializer):
    country = serializers.SlugRelatedField(slug_field='name', read_only=True)
    city = serializers.SlugRelatedField(slug_field='name', read_only=True)

    class Meta:
        fields = ('id', 'name', 'city', 'country', 'address')
        model = models.Warehouse


class CountrySerializer(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        fields = ('id', 'name', 'image')
        model = models.Country


class CountryDetailSerializer(CountrySerializer):
    images = ImageSerializer(many=True)

    class Meta:
        fields = ('id', 'name', 'image', 'description', 'images')
        model = models.Country


class RegionSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)
    image = ImageSerializer()
    number_of_stores = serializers.IntegerField()

    class Meta:
        fields = ('id', 'name', 'description', 'latitude', 'longitude', 'city_name', 'image', 'number_of_stores')
        model = models.Region


class StoreLocationSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    logo = ImageSerializer(read_only=True, source='store.image')

    class Meta:
        model = models.StoreLocation
        fields = ('store', 'store_name', 'latitude', 'longitude', 'address', 'logo')


class StoreLocationSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StoreLocation
        fields = ('latitude', 'longitude', 'address', 'region')


class RegionDetailSerializer(serializers.ModelSerializer):
    stores = StoreLocationSerializer(many=True, source='region_stores')
    country_name = serializers.CharField(source='city.country.name', read_only=True)
    city_name = serializers.CharField(source='city.name', read_only=True)
    image = ImageSerializer()

    class Meta:
        fields = ('id', 'name', 'description', 'latitude', 'longitude', 'stores', 'country_name', 'city_name', 'image')
        model = models.Region


class StoreDetailSerializer(StoreSerializer):
    images = ImageSerializer(many=True, read_only=True)
    information_images = ThinImageSerializer(many=True, read_only=True)
    videos = serializers.ListSerializer(child=serializers.CharField())
    store_location = StoreLocationSimpleSerializer(many=True)

    class Meta:
        fields = ('id', 'name', 'description', 'logo', 'categories', 'images', 'videos', 'store_location',
                  'extra_information', 'information_images')
        model = models.Store


class JoinRequestSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = landing_models.JoinRequest
        exclude = ('created',)

    def create(self, validated_data):
        obj = super(JoinRequestSerializer, self).create(validated_data)
        # send_mail_join_request(obj)
        return obj


class SignUpRequestSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = landing_models.SignUpRequest
        exclude = ('created',)

    def create(self, validated_data):
        obj = super(SignUpRequestSerializer, self).create(validated_data)
        return obj
