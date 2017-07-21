"""district_euro URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework_jwt.views import refresh_jwt_token

from core.rest.auth.views import obtain_jwt_token
from core.urls import api_urls

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]

account_patterns = [
    url(r'^login/?$', obtain_jwt_token, name='login'),
    url(r'^refresh-token/?$', refresh_jwt_token, name='refresh-token'),
]

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^account/', include(account_patterns)),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^api/', include(api_urls)),
]