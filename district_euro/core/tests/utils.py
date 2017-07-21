import random
import string

from core import models

_vendor_data = {
    'email': 'vendor@asap.uy',
    'first_name': 'vendor',
    'last_name': 'test',
    'password': 'password',
}

_consumer_data = {
    'email': 'vendor@asap.uy',
    'first_name': 'vendor',
    'last_name': 'test',
    'password': 'password',
}


def get_vendor_data(override_data={}):
    data = _vendor_data.copy()
    data.update(override_data)
    return data


def get_consumer_data(override_data={}):
    data = _consumer_data.copy()
    data.update(override_data)
    return data


def get_or_create_user(data):
    user = models.User.objects.filter(email=data.get('email')).first()
    if user is not None:
        return False, user
    user = models.User.objects.create_user(**data)
    return True, user


def create_vendor(**kwargs):
    created, user = get_or_create_user(get_vendor_data(kwargs))
    if not created:
        return user
    models.Vendor.objects.create(user=user)
    return user


def create_consumer(**kwargs):
    created, user = get_or_create_user(get_vendor_data(kwargs))
    if not created:
        return user
    models.Consumer.objects.create(user=user)
    return user


def get_random_name(len=12):
    return string.capwords(''.join(random.choice(string.ascii_lowercase) for i in range(len)))


def get_random_number(len=12):
    return ''.join(random.choice(string.digits) for i in range(len))
