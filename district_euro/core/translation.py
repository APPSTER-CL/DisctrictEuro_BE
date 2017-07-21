from modeltranslation.translator import TranslationOptions, translator

from .models import Product, UnapprovedProduct, Store, Category, Attribute, AttributeValue, Warehouse, Country,\
    City, Region


class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)


class UnapprovedProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)


class StoreTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'extra_information')


class CategoryTranslationOptions(TranslationOptions):
    fields = ('name',)


class AttributeTranslationOptions(TranslationOptions):
    fields = ('name',)


class AttributeValueTranslationOption(TranslationOptions):
    fields = ('value',)


class WarehouseTranslationOption(TranslationOptions):
    fields = ('name',)


class CountryTranslationOption(TranslationOptions):
    fields = ('name', 'description')


class CityTranslationOption(TranslationOptions):
    fields = ('name',)


class RegionTranslationOption(TranslationOptions):
    fields = ('name', 'description')


translator.register(Product, ProductTranslationOptions)
translator.register(UnapprovedProduct, UnapprovedProductTranslationOptions)
translator.register(Store, StoreTranslationOptions)
translator.register(Category, CategoryTranslationOptions)
translator.register(Attribute, AttributeTranslationOptions)
translator.register(AttributeValue, AttributeValueTranslationOption)
translator.register(Warehouse, WarehouseTranslationOption)
translator.register(Country, CountryTranslationOption)
translator.register(City, CityTranslationOption)
translator.register(Region, RegionTranslationOption)
