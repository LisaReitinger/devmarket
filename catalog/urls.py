from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # Product detail page
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Category listing page  
    path('category/<slug:slug>/', views.category_products, name='category_detail'),
    
    # Search functionality
    path('search/', views.search_products, name='search'),
    path('quick-search/', views.quick_search, name='quick_search'),
]
