from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import Image


class JoinRequest(models.Model):
    created = models.DateTimeField(default=timezone.now, verbose_name=_('Date'))
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    website_url = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Website URL'))
    email = models.EmailField(verbose_name=_('Email'))
    phone_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Phone Number'))
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Address'))
    products_description = models.TextField(blank=True, verbose_name=_('Producs Descripition'))
    extra_description = models.TextField(blank=True, verbose_name=_('Others Products Infromation'))
    social_facebook = models.CharField(max_length=255, blank=True, null=True, verbose_name='Facebook')
    social_instagram = models.CharField(max_length=255, blank=True, null=True, verbose_name='Instagram')
    social_other = models.CharField(max_length=255, blank=True, null=True, verbose_name='Social Other')
    business_description = models.TextField(blank=True, verbose_name=_('Business Description'))
    certifications = models.TextField(blank=True, verbose_name=_('Certifications'))
    images = GenericRelation(Image, content_type_field='object_type')

    class Meta:
        verbose_name = _('Join Request')
        verbose_name_plural = _('Join Requests')
        ordering = ('-id',)
        app_label = 'landing'
        db_table = 'core_joinrequest'

    def __unicode__(self):
        return u'{} - {} - {}'.format(self.pk, unicode(self.name), unicode(self.email))


class SignUpRequest(models.Model):
    created = models.DateTimeField(default=timezone.now, verbose_name=_('Date'))
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    email = models.EmailField(verbose_name=_('Email'))

    class Meta:
        verbose_name = _('Sign Up Request')
        verbose_name_plural = _('Sign Up Requests')
        ordering = ('-id',)
        app_label = 'landing'
        db_table = 'core_signuprequest'

    def __unicode__(self):
        return u'{} - {} - {}'.format(self.pk, unicode(self.name), unicode(self.email))
