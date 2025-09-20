from django.urls import path
from . import views

app_name = 'checkout'

urlpatterns = [
    path('', views.checkout_view, name='checkout'),
    path('create-session/', views.create_checkout_session, name='create_session'),
    path('success/', views.checkout_success, name='success'),
    path('cancel/', views.checkout_cancel, name='cancel'),
    path('webhook/', views.stripe_webhook, name='webhook'),
    path('buy-now/<slug:product_slug>/', views.buy_now, name='buy_now'),
]
