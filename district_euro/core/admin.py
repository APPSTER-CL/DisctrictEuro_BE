from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.admin import GenericStackedInline
from django.utils.html import format_html

from core import forms
from core import models
from landing import models as landing_models
from modeltranslation.admin import TranslationAdmin, TranslationStackedInline

admin_models = [
    models.Consumer,
    models.Employee,
    models.Sample,
    models.OverviewType,
    models.PeriodOverview,
]

for m in admin_models:
    admin.site.register(m)


class CoreUserAdmin(UserAdmin):
    # The forms to add and change user instances
    form = forms.UserEditForm
    add_form = forms.UserCreationForm
    list_display = ("email",)
    ordering = ("email",)

    fieldsets = (
        (None, {'fields': ('email', 'password', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active',
                           'image_file', 'image_url')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name', 'is_superuser', 'is_staff', 'is_active',
                       'image_file', 'image_url')}
         ),
    )

    filter_horizontal = ()


class ImageInlineAdmin(GenericStackedInline):
    model = models.Image
    form = forms.ImageForm
    extra = 0
    min_num = 0
    ct_field = 'object_type'
    ct_fk_field = 'object_id'


class ImageOnlyInlineAdmin(GenericStackedInline):
    classes = ['collapse']
    model = models.Image
    form = forms.ImageForm
    ct_field = 'object_type'

    def has_add_permission(self, request):
        return False

    def image_url(self, instance):
        if instance.pk:
            return format_html(u'<a href="{}" target="_blank"><img src="{}" height=300></a>', instance.url,
                               instance.url)
        else:
            return ""

    image_url.short_description = "Image"
    image_url.allow_tags = True

    fields = ('image_url',)
    readonly_fields = fields


class OtherImageInline(ImageInlineAdmin):
    verbose_name = 'Other Image'
    verbose_name_plural = 'Other Images'


class CityInlineAdmin(TranslationStackedInline):
    model = models.City
    extra = 1


class CountryAdmin(TranslationAdmin):
    inlines = (CityInlineAdmin, OtherImageInline,)
    form = forms.CountryForm
    fields = ('name', 'description', 'in_app', 'image_file', 'image_url')


class RegionInline(TranslationStackedInline):
    model = models.Region
    form = forms.RegionForm
    extra = 1


class CityAdmin(TranslationAdmin):
    inlines = (RegionInline,)


class CategoryInline(TranslationStackedInline):
    model = models.Category
    verbose_name = 'Subcategory'
    verbose_name_plural = 'SubCategories'
    extra = 0


class CategoryAdmin(TranslationAdmin):
    inlines = (CategoryInline,)


class StoreInline(TranslationStackedInline):
    model = models.Store
    exclude = ('image',)
    extra = 1
    min_num = 1
    max_num = 1
    verbose_name_plural = 'Store'


class VendorAdmin(admin.ModelAdmin):
    inlines = (StoreInline,)


class StoreLocationInline(admin.StackedInline):
    model = models.StoreLocation
    extra = 1


class InformationImageInline(ImageInlineAdmin):
    form = forms.InformationImageForm
    ct_fk_field = 'object_id2'
    verbose_name = 'Information Image'
    verbose_name_plural = 'Information Images'


class StoreAdmin(TranslationAdmin):
    inlines = (StoreLocationInline, OtherImageInline, InformationImageInline)
    form = forms.StoreForm
    readonly_fields = ('countries',)


class ProductUnitAdmin(admin.StackedInline):
    model = models.ProductUnit
    min_num = 1
    extra = 0


class UnApprovedProductAdmin(TranslationAdmin):
    inlines = (ProductUnitAdmin,)
    form = forms.ProductForm
    list_display = ('id', 'name', 'store', 'price', 'category', 'is_active')


class ProductAdmin(TranslationAdmin):
    inlines = (ProductUnitAdmin,)
    form = forms.ProductForm
    list_display = ('id', 'name', 'store', 'price', 'category', 'is_active')

    def get_queryset(self, request):
        return super(ProductAdmin, self).get_queryset(request).filter(is_approved=True)


class OrderItemInline(admin.StackedInline):
    model = models.OrderItem
    extra = 0
    min_num = 1
    form = forms.OrderItemForm


class OrderAdmin(admin.ModelAdmin):
    inlines = (OrderItemInline,)
    form = forms.OrderCreateForm
    readonly_fields = ('total_quantity', 'total_price')
    list_display = ('id', 'consumer', 'store', 'created')


class ShowroomInline(admin.StackedInline):
    model = models.Showroom
    form = forms.ShowroomForm
    extra = 0
    min_num = 0


class ShowroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'warehouse', 'country')
    form = forms.ShowroomForm


class WarehouseAdmin(TranslationAdmin):
    inlines = (ShowroomInline,)


class AttributeValueAdminInline(admin.StackedInline):
    model = models.AttributeValue
    extra = 0
    min_num = 0
    form = forms.AttributeValueCreationForm


class AttribtueAdmin(TranslationAdmin):
    inlines = (AttributeValueAdminInline,)
    form = forms.AttributeForm


class ProductSampleUnitAdmin(admin.StackedInline):
    model = models.ProductSampleUnits
    extra = 0
    min_num = 1


class SampleDispatchAdmin(admin.ModelAdmin):
    inlines = (ProductSampleUnitAdmin,)


class RegionAdmin(TranslationAdmin):
    form = forms.RegionForm


class SignUpRequestAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    fields = ('name', 'email', 'created')
    readonly_fields = fields


class JoinRequestAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    fields = ('name',
              'website_url',
              'email',
              'phone_number',
              'address',
              'products_description',
              'extra_description',
              'social_facebook',
              'social_instagram',
              'social_other',
              'business_description',
              'certifications')

    readonly_fields = fields
    inlines = (ImageOnlyInlineAdmin,)


admin.site.register(models.Vendor, VendorAdmin)
admin.site.register(models.Product, ProductAdmin)
admin.site.register(models.UnapprovedProduct, UnApprovedProductAdmin)
admin.site.register(models.Category, CategoryAdmin)
admin.site.register(models.User, CoreUserAdmin)
admin.site.register(models.Country, CountryAdmin)
admin.site.register(models.Order, OrderAdmin)
admin.site.register(models.Warehouse, WarehouseAdmin)
admin.site.register(models.Attribute, AttribtueAdmin)
admin.site.register(models.SampleDispatch, SampleDispatchAdmin)
admin.site.register(models.Store, StoreAdmin)
admin.site.register(models.City, CityAdmin)
admin.site.register(models.Region, RegionAdmin)
admin.site.register(landing_models.JoinRequest, JoinRequestAdmin)
admin.site.register(landing_models.SignUpRequest, SignUpRequestAdmin)
admin.site.register(models.Showroom, ShowroomAdmin)

admin.site.site_header = 'Oumimen Administration'
