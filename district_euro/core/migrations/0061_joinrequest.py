# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-04 18:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0060_auto_20161019_1523'),
    ]

    operations = [
        migrations.CreateModel(
            name='JoinRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date')),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('website_url', models.CharField(blank=True, max_length=255, null=True, verbose_name='Website URL')),
                ('email', models.EmailField(max_length=254, verbose_name='Email')),
                ('phone_number', models.CharField(max_length=100, verbose_name='Phone Number')),
                ('products_description', models.TextField(blank=True, verbose_name='Producs Descripition')),
                ('extra_description', models.TextField(blank=True, verbose_name='Others Products Infromation')),
                ('social_facebook', models.CharField(blank=True, max_length=255, null=True, verbose_name='Facebook')),
                ('social_instagram', models.CharField(blank=True, max_length=255, null=True, verbose_name='Instagram')),
                ('social_other', models.CharField(blank=True, max_length=255, null=True, verbose_name='Social Other')),
                ('business_description', models.TextField(blank=True, verbose_name='Business Description')),
                ('certifications', models.TextField(blank=True, verbose_name='Certifications')),
            ],
            options={
                'verbose_name': 'Join Request',
                'verbose_name_plural': 'Join Requests',
            },
        ),
    ]