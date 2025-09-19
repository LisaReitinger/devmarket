from django.shortcuts import render
from catalog.models import Category, Product

def home_view(request):
    """
    Home page view displaying hero section, categories, and featured products.
    Matches the wireframe design with real data from the database.
    """
    # Get top-level categories for the category showcase
    top_categories = Category.objects.filter(
        parent=None, 
        is_active=True
    ).order_by('sort_order')[:6]
    
    # Get featured products for the featured section
    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True,
        status='active'
    ).select_related('seller', 'category').order_by('-created_at')[:8]
    
    # Get latest products for "New Arrivals" section
    latest_products = Product.objects.filter(
        is_active=True,
        status='active'
    ).select_related('seller', 'category').order_by('-created_at')[:6]
    
    # Get some stats for the hero section
    total_products = Product.objects.filter(is_active=True, status='active').count()
    total_categories = Category.objects.filter(is_active=True).count()
    
    context = {
        'top_categories': top_categories,
        'featured_products': featured_products,
        'latest_products': latest_products,
        'total_products': total_products,
        'total_categories': total_categories,
    }
    
    return render(request, 'pages/home.html', context)
