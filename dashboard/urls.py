from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home
    path('', views.dashboard_home, name='home'),
    
    # Product management
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.ProductCreateView.as_view(), name='product_add'),
    path('products/<uuid:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<uuid:pk>/toggle-status/', views.product_toggle_status, name='product_toggle_status'),
    path('products/<uuid:pk>/toggle-featured/', views.product_toggle_featured, name='product_toggle_featured'),
    
    # Analytics
    path('analytics/', views.analytics_view, name='analytics'),
]
