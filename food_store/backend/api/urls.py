from django.urls import include, path
from rest_framework import routers

from .views import CartViewSet, CategoryViewSet, ProductViewSet

app_name = 'api'

router_api = routers.DefaultRouter()

router_api.register(r'category', CategoryViewSet, basename='category')
router_api.register(r'products', ProductViewSet, basename='product')
router_api.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router_api.urls)),
]
