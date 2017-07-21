from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

from core.rest.common import views as common_views
from core.rest.other import views as other_views
from core.rest.vendor import views as vendor_views
from core.rest.employee import views as employee_views

vendor_router = DefaultRouter()
vendor_router.register('order', vendor_views.OrderView, base_name='order')
vendor_router.register('product', vendor_views.ProductViewSet, base_name='product')
vendor_router.register('incomplete-product', vendor_views.IncompleteProductViewSet, base_name='incomplete-products')
vendor_router.register('inventory', vendor_views.InventoryViewSet, base_name='inventory')
vendor_router.register('sample', vendor_views.ProductSampleViewSet, base_name='sample')
vendor_router.register('sample-dispatch', vendor_views.SampleDispatchViewSet, base_name='sample-dispatch')
vendor_router.register('product-attribute', vendor_views.AttributeViewSet, base_name='product-attributes')

_vendor_urls = [
    url(r'^vendor/', include(vendor_router.urls)),
    url(r'^vendor/bulk-upload/?$', vendor_views.product_bulk_upload),
    url(r'^vendor/overview/(?P<type>\w+)/?', vendor_views.OverviewView.as_view())
]

employee_router = DefaultRouter()
employee_router.register('sample', employee_views.SampleViewSet, base_name='employee-sample')
employee_router.register('sample-dispatch', employee_views.SampleDispatchViewSet, base_name='employee-sample-dispatch')
employee_router.register('showroom', employee_views.EmployeeShowroomViewSet, base_name='employee-showroom')

_employee_urls = [
    url(r'^employee/', include(employee_router.urls)),
]

api_router = DefaultRouter()
api_router.register('product', other_views.ProductViewSet, base_name='products')
api_router.register('store', other_views.StoreViewSet, base_name='stores')
api_router.register('country', other_views.CountryViewSet, base_name='country')
api_router.register('region', other_views.RegionViewSet, base_name='region')
api_router.register('showroom', other_views.ShowroomViewSet, base_name='showroom')
api_router.register('warehouse', other_views.WarehouseViewSet, base_name='warehouse')
api_router.register('join-request', other_views.JoinRequestViewSet, base_name='join-request')
api_router.register('sign-up-request', other_views.SignUpRequestViewSet, base_name='sign-up-request')

_api_miscellaneous = [
                         url(r'^shipping-status/?$', other_views.ShippingStatusView.as_view()),
                         url(r'^currency/?$', other_views.CurrencyListView.as_view()),
                         url(r'^category/?$', other_views.CategoryView.as_view()),
                         url(r'^image/(?P<model>\w+)/(?P<pk>\d+)/?$', common_views.ImageUploadView.as_view()),
                         url(r'^image/(?P<model>\w+)/(?P<pk>\d+)/main/?$', common_views.MainImageUploadView.as_view()),
                         url(r'^image/(?P<model>\w+)/(?P<pk>\d+)/infographic/?$',
                             common_views.InfographicUploadView.as_view()),
                         url(r'^image/join-us/(?P<pk>\d+)/?$',
                             common_views.ImageUploadViewJoinUs.as_view()),
                         url(r'^language/?$', other_views.LanguageListView.as_view()),
                     ] + api_router.urls

api_urls = _vendor_urls + _api_miscellaneous + _employee_urls
