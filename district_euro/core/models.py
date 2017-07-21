from __future__ import unicode_literals

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField, ArrayField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from djmoney.models.fields import MoneyField

from district_euro import settings

_decimal_places = 2
_max_digits = 15
_default_currency = 'USD'


class ShippingStatusMixin(object):
    PENDING = 'PEN'
    IN_PROGRESS = 'PRG'
    SHIPPED = 'SHP'
    DELIVERED = 'DLV'
    RETURNED = 'RET'

    STATUS = (
        (PENDING, _('Pending')),
        (IN_PROGRESS, _('In Progress')),
        (SHIPPED, _('Shipped')),
        (DELIVERED, _('Delivered')),
        (RETURNED, _('Returned')),
    )

    STATUS_DICT = {k: v for k, v in STATUS}


class Image(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Name'))
    object_type = models.ForeignKey(ContentType, verbose_name=_('Objcet Type'), blank=True, null=True)
    object_id = models.CharField(max_length=200, verbose_name=_('Object id'), blank=True, null=True)
    object = GenericForeignKey('object_type', 'object_id')

    # If we need models with two images sets
    object_id2 = models.CharField(max_length=200, verbose_name=_('Object id 2'), blank=True, null=True)
    object2 = GenericForeignKey('object_type', 'object_id2')

    url = models.CharField(max_length=255, verbose_name=_('URL'), blank=True, null=True)
    portrait_url = models.CharField(max_length=255, verbose_name=_('Portrait URL'), blank=True, null=True)
    landscape_url = models.CharField(max_length=255, verbose_name=_('Landscape URL'), blank=True, null=True)
    small_url = models.CharField(max_length=255, verbose_name=_('Small URL'), blank=True, null=True)

    def __unicode__(self):
        return self.name or self.url


class Country(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    image = models.ForeignKey(Image, verbose_name=_('Image'), null=True, blank=True)
    images = GenericRelation(Image, content_type_field='object_type')
    in_app = models.BooleanField(default=True, verbose_name=_('If this country is shown in the app'))

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name_plural = _('Countries')


class City(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    country = models.ForeignKey(Country, verbose_name=_('Country'), related_name='cities')

    class Meta:
        verbose_name = _('City')
        verbose_name_plural = _('Cities')
        ordering = ('country__name', 'name')

    def __unicode__(self):
        return u'%s, %s' % (self.name, self.country.name)


class Region(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    city = models.ForeignKey(City, verbose_name=_('City'), related_name='regions')
    latitude = models.FloatField(null=True, blank=True, verbose_name=_('Latitude'))
    longitude = models.FloatField(null=True, blank=True, verbose_name=_('Longitude'))
    image = models.ForeignKey(Image, verbose_name=_('Image'), null=True, blank=True)

    class Meta:
        verbose_name = _('Region')
        verbose_name_plural = _('Regions')
        ordering = ('city__country__name', 'name')

    def __unicode__(self):
        return u'%s, %s, %s' % (self.city.country.name, self.city.name, self.name)


class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    email = models.CharField(max_length=255, unique=True, db_index=True, verbose_name=_('email address'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    first_name = models.CharField(max_length=255, verbose_name=_('First Name'))
    last_name = models.CharField(max_length=255, verbose_name=_('Last Name'))
    is_staff = models.BooleanField(_('staff status'), default=False)
    is_active = models.BooleanField(_('active'), default=settings.USERS_AUTO_ACTIVATE)

    image = models.ForeignKey(Image, verbose_name=_('Image'), blank=True, null=True)

    def get_short_name(self):
        return self.email

    def get_full_name(self):
        return (self.first_name + ' ' if len(self.first_name) > 0 else '') + self.last_name

    @property
    def profiles(self):
        """
        Returns list of profiles for this user.
        :return: list(str)
        """
        profile_opts = [('consumer', _('Consumer')), ('employee', _('Employee')), ('vendor', _('Vendor'))]
        profiles = []
        for profile_attr, profile_string in profile_opts:
            try:
                getattr(self, profile_attr)
            except:
                pass
            else:
                profiles.append(profile_string)
        return profiles


class Consumer(models.Model):
    user = models.OneToOneField(User, primary_key=True, verbose_name=_('User'), on_delete=models.CASCADE,
                                related_name='consumer')
    phone_number = models.CharField(max_length=255, verbose_name=_('Phone Number'), null=True, blank=True)

    def __unicode__(self):
        return unicode(self.user)


class Employee(models.Model):
    user = models.OneToOneField(User, primary_key=True, verbose_name=_('User'), on_delete=models.CASCADE,
                                related_name='employee')
    warehouse = models.ForeignKey('Warehouse', verbose_name=_('Warehouse'))
    showroom = models.ForeignKey('Showroom', verbose_name=_('Showroom'))

    def __unicode__(self):
        return unicode(self.user)


class Vendor(models.Model):
    user = models.OneToOneField(User, primary_key=True, verbose_name=_('User'), on_delete=models.CASCADE,
                                related_name='vendor')

    def __unicode__(self):
        return unicode(self.user)

    @property
    def store(self):
        """
        This method asumes the vendor has up to one store.
        """
        return self.stores.first()


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    super_category = models.ForeignKey('Category', null=True, blank=True, verbose_name=_('Parent Category'),
                                       related_name='subcategories')
    is_leaf = models.BooleanField(default=False, verbose_name=_('Is Leaf'))

    def __unicode__(self):
        prefix = (u'%s/' % unicode(self.super_category)) if self.super_category else ''
        return u'%s%s' % (prefix, self.name)

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def flatten(self):
        categories = []
        for category in self.subcategories.all():
            categories += category.flatten()
        categories.append(self)
        return categories


class Store(models.Model):
    vendor = models.ForeignKey(Vendor, verbose_name=_('Vendor'), related_name='stores')
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    categories = models.ManyToManyField(Category, verbose_name=_('Categories'), related_name='stores')
    countries = models.ManyToManyField(Country, verbose_name=_('Countries'), related_name='country_store', blank=True,
                                       help_text=_('Do not alter this directly, add or delete store location instead.'))
    image = models.ForeignKey(Image, verbose_name=_('Image'), null=True, blank=True)
    images = GenericRelation(Image, content_type_field='object_type')

    videos = ArrayField(base_field=models.CharField(max_length=255), blank=True, null=True,
                        verbose_name=_('Links to videos'), help_text=_('To add more than one separate them with ,'))

    popularity = models.IntegerField(default=0, verbose_name=_('Popularity'), help_text=_('More is better'))

    extra_information = models.TextField(verbose_name=_('Extra information'), blank=True, null=True)
    information_images = GenericRelation(Image, content_type_field='object_type', object_id_field='object_id2' )

    def __unicode__(self):
        return self.name


class StoreLocation(models.Model):
    store = models.ForeignKey(Store, verbose_name=_('Store'), related_name='store_location')
    region = models.ForeignKey(Region, verbose_name=_('Region'), related_name='region_stores')
    latitude = models.FloatField(null=True, blank=True, verbose_name=_('Latitude'))
    longitude = models.FloatField(null=True, blank=True, verbose_name=_('Longitude'))
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Address'))

    class Meta:
        verbose_name = _('Store Location')
        verbose_name_plural = _('Store Locations')
        ordering = ('region',)


class ActiveProductManager(models.Manager):
    def get_queryset(self):
        return super(ActiveProductManager, self).get_queryset().filter(is_active=True)


class Product(models.Model):
    store = models.ForeignKey(Store, verbose_name=_('Store'))
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    price = MoneyField(max_digits=_max_digits, decimal_places=_decimal_places, default_currency=_default_currency)
    is_active = models.BooleanField(default=True, verbose_name=_('Is active'))
    image = models.ForeignKey(Image, verbose_name=_('Main image'), blank=True, null=True, related_name='product_image')
    images = GenericRelation(Image, content_type_field='object_type')
    attributes = models.ManyToManyField('Attribute', verbose_name=_('Product Attributes'), blank=True)
    category = models.ForeignKey(Category, verbose_name=_('Category'))
    infographics = models.ManyToManyField(Image, verbose_name=_('Infographics'), blank=True)

    date_created = models.DateTimeField(verbose_name=_('Created'), default=timezone.now)
    date_approved = models.DateTimeField(verbose_name=_('Date Approved'), default=None, null=True, blank=True)

    sold_quantity = models.PositiveIntegerField(default=0, verbose_name=_('Amount sold'))
    amount_reviews = models.IntegerField(default=0, verbose_name=_('Amount of reviews of this product'))
    mean_qualification = models.FloatField(blank=True, null=True,
                                           validators=[MinValueValidator(0), MaxValueValidator(5)],
                                           verbose_name=_('Mean Review Qualification'))
    popular_in = models.ManyToManyField(Country, verbose_name=_('Popular In'), blank=True,
                                        related_name='popular_products')
    is_approved = models.BooleanField(default=False, verbose_name=_('Is this product approved'))

    objects = models.Manager()
    actives = ActiveProductManager()

    def __unicode__(self):
        return u'%s@%s' % (self.name, self.store.name)

    def set_inactive(self):
        self.is_active = False
        self.save()

    @property
    def properties(self):
        return self.attributes.filter(is_boolean=True)


class UnapprovedProductManager(models.Manager):
    def get_queryset(self):
        return super(UnapprovedProductManager, self).get_queryset().filter(is_approved=False)


class UnapprovedProduct(Product):
    objects = UnapprovedProductManager()

    class Meta:
        proxy = True
        verbose_name = 'Product Unapproved'
        verbose_name_plural = 'Products Unapproved'


class IncompleteProduct(models.Model):
    store = models.ForeignKey(Store, verbose_name=_('Store'))
    date_added = models.DateTimeField(default=timezone.now, verbose_name=_('Date added'))
    name = models.CharField(max_length=255, verbose_name=_('Name'), blank=True, null=True)
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    price_currency = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Currency'))
    price_amount = models.DecimalField(max_digits=_max_digits, decimal_places=_decimal_places)
    units = JSONField(verbose_name=_('Attributes'), null=True, blank=True)
    errors = JSONField(verbose_name=_('Validation Errors'), null=True, blank=True)
    image = models.ForeignKey(Image, verbose_name=_('Main image'), blank=True, null=True)
    images = GenericRelation(Image, content_type_field='object_type')
    category = models.IntegerField(verbose_name=_('Category'), null=True, blank=True)

    def __unicode__(self):
        return u'INCOMPLETE %s@%s' % (self.name, self.store.name)


class Attribute(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    store = models.ForeignKey(Store, verbose_name=_('Store'), null=True, blank=True,
                              help_text=_('If this attribute is only usable for a store'))
    categories = models.ManyToManyField(Category, verbose_name=_('Categories'), blank=True, related_name='attributes',
                                        help_text=_('If a category is selected then subcategories are included too'))
    is_boolean = models.BooleanField(default=False, verbose_name=_('If this attribute has no values'))
    image = models.ForeignKey(Image, verbose_name=_('Logo'), blank=True, null=True,
                              help_text=_('Only boolean attribtues should have images'))

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name


class AttributeValue(models.Model):
    value = models.CharField(max_length=255, verbose_name=_('Value'))
    attribute_name = models.CharField(max_length=255, verbose_name=_('Cached attribute name'))
    attribute = models.ForeignKey(Attribute, verbose_name=_('Attribute'), related_name='values')
    ordering = models.IntegerField(verbose_name=_('Ordering'), default=0, help_text=_('Ascendent'))

    class Meta:
        ordering = ('value',)

    def __unicode__(self):
        return u'%s: %s' % (self.attribute_name, self.value)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.pk and self.attribute:
            self.attribute_name = self.attribute.name
        return super(AttributeValue, self).save(force_insert=False, force_update=False, using=None, update_fields=None)


class ProductUnit(models.Model):
    product = models.ForeignKey(Product, verbose_name=_('Product'), related_name='units')
    sku = models.CharField(max_length=255, verbose_name=_('SKU'), blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    attributes = models.ManyToManyField(AttributeValue, verbose_name=_('Product Attributes'), blank=True)

    def __unicode__(self):
        return u'%s (x%d)' % (unicode(self.product), self.quantity)

    class Meta:
        verbose_name = _('Product Units')
        verbose_name_plural = _('Products Units')


class Warehouse(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    city = models.ForeignKey(City, verbose_name=_('City'), null=True)
    country = models.ForeignKey(Country, verbose_name=_('Country'), null=True)
    address = models.CharField(max_length=255, verbose_name=_('Address'), blank=True, null=True)
    description = models.TextField(verbose_name=_('Description'), blank=True, null=True)
    latitude = models.FloatField(null=True, blank=True, verbose_name=_('Latitude'))
    longitude = models.FloatField(null=True, blank=True, verbose_name=_('Longitude'))
    samples = GenericRelation('Sample', content_type_field='object_type')

    def __unicode__(self):
        return self.name


class Showroom(models.Model):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    city = models.ForeignKey(City, verbose_name=_('City'), null=True)
    country = models.ForeignKey(Country, verbose_name=_('Country'), null=True)
    address = models.CharField(max_length=255, verbose_name=_('Address'), blank=True, null=True)
    description = models.TextField(verbose_name=_('Description'), blank=True, null=True)
    warehouse = models.ForeignKey(Warehouse, verbose_name=_('Warehouse'), related_name='showrooms')
    latitude = models.FloatField(null=True, blank=True, verbose_name=_('Latitude'))
    longitude = models.FloatField(null=True, blank=True, verbose_name=_('Longitude'))
    image = models.ForeignKey(Image, verbose_name=_('Image'), null=True, blank=True)
    samples = GenericRelation('Sample', content_type_field='object_type')

    def __unicode__(self):
        return self.name


class SystemLog(models.Model):
    level = models.CharField(max_length=255, verbose_name=_('Level'))
    message = models.TextField(verbose_name=_('Message'))
    extra = models.TextField(verbose_name=_('Message'), blank=True, null=True)
    create_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Log')
        verbose_name_plural = _('Logs')
        ordering = ('-id',)

    def __unicode__(self):
        return '%s: %s' % (self.level, self.message)


class Order(models.Model, ShippingStatusMixin):
    consumer = models.ForeignKey(Consumer, verbose_name=_('Consumer'))
    store = models.ForeignKey(Store, verbose_name=_('Store'))
    total_price = MoneyField(max_digits=_max_digits, decimal_places=_decimal_places)
    tracking_number = models.CharField(max_length=255, verbose_name=_('Tracking Number'), blank=True, null=True)
    shipping_company = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(default=timezone.now, verbose_name=_('Date created'))
    shipping_address = models.CharField(max_length=255, verbose_name=_('Shipping Address'))
    status = models.CharField(max_length=100, choices=ShippingStatusMixin.STATUS, default=ShippingStatusMixin.PENDING)
    total_quantity = models.PositiveIntegerField(verbose_name=_('Total Products Quantity'))

    def __unicode__(self):
        return u'%s %s' % (unicode(self.consumer), self.pk)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name=_('Order'), related_name='order_items')

    sku = models.CharField(max_length=255, verbose_name=_('SKU'), blank=True, null=True, db_index=True)
    product_unit = models.ForeignKey(ProductUnit, verbose_name=_('Product Unit'))
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    unit_price = MoneyField(max_digits=_max_digits, decimal_places=_decimal_places, verbose_name=_('Unit Price'))
    total_price = MoneyField(max_digits=_max_digits, decimal_places=_decimal_places, verbose_name=_('Total Price'))
    quantity = models.PositiveIntegerField(verbose_name=_('Quantity'))
    attributes = JSONField(verbose_name=_('Attributes'), null=True, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')


class SampleDispatch(models.Model, ShippingStatusMixin):
    created = models.DateTimeField(default=timezone.now, verbose_name=_('Date created'))
    showrooms = models.ManyToManyField(Showroom, verbose_name=_('Showrooms'))
    warehouse = models.ForeignKey(Warehouse, verbose_name=_('Warehouse'))
    store = models.ForeignKey(Store, verbose_name=_('Store'))
    tracking_number = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('Tracking Number'))
    status = models.CharField(max_length=50, verbose_name=_('Status'), choices=ShippingStatusMixin.STATUS,
                              default=ShippingStatusMixin.PENDING)
    shipping_company = models.CharField(max_length=255, null=True, blank=True)
    received_by = models.ForeignKey(User, verbose_name=_('Received By'), null=True, blank=True)

    class Meta:
        verbose_name = _('Dispatched Sample')
        verbose_name_plural = _('Dispatched Samples')
        ordering = ('-created', '-id')

    def __unicode__(self):
        return u'%s: %s to %s' % (
            self.STATUS_DICT[self.status], unicode(self.store), unicode(self.warehouse))

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        # Set status to SHIPPED if tracking number is provided.
        if not self.pk:
            if self.tracking_number is not None and self.tracking_number != "":
                self.status = self.SHIPPED
        super(SampleDispatch, self).save(force_insert, force_update, using, update_fields)

    def was_shipped(self):
        return self.status == self.SHIPPED


class ProductSampleUnits(models.Model):
    product_unit = models.ForeignKey(ProductUnit, verbose_name=_('Product Unit'))
    quantity = models.PositiveIntegerField(verbose_name=_('Quantity'))
    sample_dispatch = models.ForeignKey(SampleDispatch, verbose_name=_('Sample Dispatch'),
                                        related_name='samples_units')

    def __unicode__(self):
        return u'%s(x%d)' % (self.product_unit, self.quantity)


class OverviewType(models.Model):
    name = models.SlugField(max_length=255, verbose_name=_('Analyics Nmae'), primary_key=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('Overview Type')
        verbose_name_plural = _('Overview Types')


class PeriodOverview(models.Model):
    store = models.ForeignKey(Store, verbose_name=_('Store'))
    type = models.ForeignKey(OverviewType, verbose_name=_('Overview Type'))
    date_from = models.DateField(verbose_name=_('Date From'))
    date_to = models.DateField(verbose_name=_('Date To'))
    value = models.BigIntegerField(verbose_name=_('Value'))
    aggregate_value = models.BigIntegerField(verbose_name=_('Aggregate Value'), default=0, blank=True)

    def __unicode__(self):
        return u'%s::%s %s to %s -> %d' % (self.store, self.type, self.date_from, self.date_to, self.value)

    class Meta:
        verbose_name = _('Period Overview')
        verbose_name_plural = _('Period Overviews')


class Sample(models.Model):
    product_unit = models.ForeignKey(ProductUnit, verbose_name=_('Product Unit'))
    quantity = models.PositiveIntegerField(verbose_name=_('Quantity'))
    warehouse = models.ForeignKey(Warehouse, verbose_name=_('Warehouse'))
    showrooms = models.ManyToManyField('Showroom', verbose_name=_('Showrooms'), blank=True)

    # sample_dispatch field should not be null
    sample_dispatch = models.ForeignKey(SampleDispatch, verbose_name=_('Sample Dispatch'), null=True, blank=True)
    updated = models.DateTimeField(verbose_name=_('Last Updated'), auto_now=True)
    object_type = models.ForeignKey(ContentType, verbose_name=_('Objcet Type'), blank=True, null=True)
    object_id = models.PositiveIntegerField(verbose_name=_('Object id'), blank=True, null=True)
    location = GenericForeignKey('object_type', 'object_id')

    def __unicode__(self):
        return u'%s (x%d) at %s' % (unicode(self.product_unit), self.quantity, unicode(self.warehouse))
