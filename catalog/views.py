from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import Product, Category

def product_detail(request, slug):
    """
    Display detailed information about a specific product.
    Includes product details, seller info, related products, and purchase options.
    """
    # Get the product by slug, ensuring it's active and published
    product = get_object_or_404(
        Product.objects.select_related('seller', 'category'),
        slug=slug,
        is_active=True,
        status='active'
    )
    
    # Get related products from the same category
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
        status='active'
    ).exclude(
        id=product.id
    ).select_related('seller', 'category')[:4]
    
    # Get more products from the same seller
    seller_products = Product.objects.filter(
        seller=product.seller,
        is_active=True,
        status='active'
    ).exclude(
        id=product.id
    ).select_related('category')[:3]
    
    # Increment view count (you could track this for analytics)
    # For now, we'll just pass the data to template
    
    context = {
        'product': product,
        'related_products': related_products,
        'seller_products': seller_products,
    }
    
    return render(request, 'catalog/product_detail.html', context)


def category_products(request, slug):
    """
    Display all products in a specific category.
    """
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get all products in this category and its subcategories
    products = Product.objects.filter(
        category=category,
        is_active=True,
        status='active'
    ).select_related('seller', 'category').order_by('-created_at')
    
    # Get subcategories if any
    subcategories = Category.objects.filter(
        parent=category,
        is_active=True
    ).order_by('sort_order')
    
    context = {
        'category': category,
        'products': products,
        'subcategories': subcategories,
    }
    
    return render(request, 'catalog/category_detail.html', context)