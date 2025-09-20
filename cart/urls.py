from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_view, name='cart_view'),
    path('add/<slug:product_slug>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<slug:product_slug>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('count/', views.cart_count, name='cart_count'),
]
