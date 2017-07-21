import moneyed
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.utils.translation import gettext_lazy as _

from core import models
from core.image import upload_image, upload_image2, delete_image


class OrderItemForm(forms.ModelForm):
    product_unit = forms.ModelChoiceField(required=True,
                                          queryset=models.ProductUnit.objects.select_related(
                                              'product').prefetch_related('attributes').all())
    quantity = forms.IntegerField(required=True)

    class Meta:
        fields = ('order', 'product_unit', 'quantity',)
        model = models.OrderItem

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 0:
            raise forms.ValidationError('Quantity must be grater than zero')
        return quantity

    def clean(self):
        product_unit = self.cleaned_data.get('product_unit')
        quantity = self.cleaned_data.get('quantity')
        attribtues = []
        for a in product_unit.attributes.all():
            attribtues.append({a.attribute_name: a.value})

        return {
            'quantity': quantity,
            'product_unit': product_unit,
            'name': product_unit.product.name,
            'description': product_unit.product.description,
            'unit_price': product_unit.product.price,
            'total_price': product_unit.product.price * quantity,
            'attributes': attribtues,
        }

    def save(self, commit=True):
        order_item = models.OrderItem(**self.cleaned_data)
        order_item.order = self.instance.order
        order = models.Order.objects.filter(id=order_item.order_id).select_for_update().first()
        order.total_price += order_item.total_price
        order.total_quantity += order_item.quantity
        order.save()
        return order_item


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = models.Order
        fields = ('consumer', 'store', 'tracking_number', 'shipping_company', 'shipping_address', 'status')

    def save(self, commit=True):
        order = super(OrderCreateForm, self).save(commit=False)
        order.total_price = moneyed.Money(0, currency=moneyed.get_currency('USD'))
        order.total_quantity = 0
        order.save()
        return order


class AttributeValueCreationForm(forms.ModelForm):
    class Meta:
        model = models.AttributeValue
        fields = ('value', 'attribute')


class ImageUploadMixinForm(forms.ModelForm):
    image_file = forms.FileField(required=False)
    image_url = forms.URLField(required=False)

    def __init__(self, *args, **kwargs):
        super(ImageUploadMixinForm, self).__init__(*args, **kwargs)
        self.fields['image_url'].initial = self.instance.image.url if self.instance.image else ''
        self.fields['image_url'].widget.attrs['readonly'] = True


class AttributeForm(ImageUploadMixinForm):
    class Meta:
        model = models.Attribute
        exclude = ('image',)

    def save(self, commit=True):
        image = self.cleaned_data.pop('image_file', None)
        self.cleaned_data.pop('image_url', None)

        super(AttributeForm, self).save(commit=commit)

        attribute = self.instance
        if not attribute.pk:
            attribute.save()

        if image:
            prefix = "%s/%s/" % ('attribute', attribute.pk)
            image_obj = upload_image(prefix, None, image)
            old_image = attribute.image
            attribute.image = image_obj
            attribute.save()
            delete_image(old_image)
        return attribute


class UserCreationForm(ImageUploadMixinForm):
    class Meta:
        model = models.User
        fields = ('email',)

    def save(self, commit=True):
        image = self.cleaned_data.pop('image_file', None)
        self.cleaned_data.pop('image_url', None)
        # Save the provided password in hashed format
        user = super(UserCreationForm, self).save(commit=False)
        password = self.cleaned_data.get('password', None)
        if password:
            user.set_password(self.cleaned_data["password"])

        if commit:
            user.save()

        if image:
            if not user.pk:
                user.save()
            prefix = "%s/%s/" % ('user', user.pk)
            image_obj = upload_image(prefix, None, image)
            old_image = user.image
            user.image = image_obj
            user.save()
            delete_image(old_image)
        return user


class UserEditForm(UserCreationForm):
    # Borrowed from django.contrib.auth.forms.UserChangeForm
    password = ReadOnlyPasswordHashField(label=_("Password"),
                                         help_text=_("Raw passwords are not stored, so there is no way to see "
                                                     "this user's password, but you can change the password "
                                                     "using <a href=\"../password/\">this form</a>."))

    class Meta:
        model = models.User
        fields = '__all__'

    def clean_password(self):
        # Regardless of what the user provides, return the initial value.
        # This is done here, rather than on the field, because the
        # field does not have access to the initial value
        return self.initial["password"]


class CountryForm(ImageUploadMixinForm):
    class Meta:
        model = models.Country
        fields = ('name', 'description', 'in_app', 'image')

    def save(self, commit=True):
        image = self.cleaned_data.pop('image_file', None)
        self.cleaned_data.pop('image_url', None)

        super(CountryForm, self).save(commit=commit)

        country = self.instance
        if not country.pk:
            country.save()

        if image:
            prefix = "%s/%s/" % ('country', country.pk)
            image_obj = upload_image(prefix, None, image)
            old_image = country.image
            country.image = image_obj
            country.save()
            delete_image(old_image)
        return country


class RegionForm(ImageUploadMixinForm):
    class Meta:
        model = models.Region
        fields = ('name', 'description', 'latitude', 'longitude', 'image_file', 'image_url')

    def save(self, commit=True):
        image = self.cleaned_data.pop('image_file', None)
        self.cleaned_data.pop('image_url', None)

        super(RegionForm, self).save(commit=commit)

        region = self.instance
        if not region.pk:
            region.save()

        if image:
            prefix = "%s/%s/" % ('region', region.pk)
            image_obj = upload_image(prefix, None, image)
            old_image = region.image
            region.image = image_obj
            region.save()
            # Delete must be done after reasignment becaouse of weird error that deletes all related objects of country.
            delete_image(old_image)
        return region


class ImageForm(ImageUploadMixinForm):
    image_file = forms.FileField(required=False)
    image_url = forms.URLField(required=False)

    class Meta:
        model = models.Image
        fields = ()

    def __init__(self, *args, **kwargs):
        super(ImageUploadMixinForm, self).__init__(*args, **kwargs)
        self.fields['image_url'].initial = self.instance.url if self.instance else ''
        self.fields['image_url'].widget.attrs['readonly'] = True

    def save(self, commit=True):
        image = self.cleaned_data.pop('image_file', None)
        self.cleaned_data.pop('image_url', None)

        obj = self.instance.object
        obj_name = type(obj).__name__.lower()
        image_obj = None

        if image:
            prefix = "%s/%s/" % (obj_name, obj.pk)
            image_obj = upload_image(prefix, obj, image)
        return image_obj


class InformationImageForm(ImageForm):
    def save(self, commit=True):
        image = self.cleaned_data.pop('image_file', None)
        self.cleaned_data.pop('image_url', None)

        obj = self.instance.object2
        obj_name = type(obj).__name__.lower()
        image_obj = None

        if image:
            prefix = "%s/%s/information/" % (obj_name, obj.pk)
            image_obj = upload_image2(prefix, obj, image, file_name=image.name, resize_on_upload=False)
        return image_obj


class StoreForm(ImageUploadMixinForm):
    class Meta:
        model = models.Store
        exclude = ('image',)

    def clean_videos(self):
        value = self.data.get('videos', None)
        if value is not None:
            if len(value) == 0:
                return None
            return map(unicode.strip, value.split(','))
        return value

    def save(self, commit=True):
        image = self.cleaned_data.pop('image_file', None)
        self.cleaned_data.pop('image_url', None)

        super(StoreForm, self).save(commit=commit)

        store = self.instance
        if not store.pk:
            store.save()

        if image:
            prefix = "%s/%s/" % ('store', store.pk)
            image_obj = upload_image(prefix, None, image)
            old_image = store.image
            store.image = image_obj
            store.save()
            delete_image(old_image)
        return store


class ShowroomForm(ImageUploadMixinForm):
    class Meta:
        model = models.Showroom
        fields = (
            'name', 'city', 'country', 'address', 'description', 'latitude', 'longitude', 'image_file', 'image_url')

    def save(self, commit=True):
        image = self.cleaned_data.pop('image_file', None)
        self.cleaned_data.pop('image_url', None)

        super(ShowroomForm, self).save(commit=commit)

        showroom = self.instance
        if not showroom.pk:
            showroom.save()

        if image:
            prefix = "%s/%s/" % ('showroom', showroom.pk)
            image_obj = upload_image(prefix, None, image)
            old_image = showroom.image
            showroom.image = image_obj
            showroom.save()
            delete_image(old_image)
        return showroom


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        if self.instance:
            country_ids = models.StoreLocation.objects.filter(store=self.instance.store).values_list(
                'region__city__country_id', flat=True)
            self.fields['popular_in'].queryset = models.Country.objects.filter(id__in=country_ids)

    class Meta:
        model = models.Product
        fields = '__all__'
