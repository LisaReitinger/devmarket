from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Product, Category
from .forms import ProductSearchForm, QuickSearchForm

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


def search_products(request):
    """
    Advanced product search with filtering and sorting.
    """
    form = ProductSearchForm(request.GET)
    products = Product.objects.filter(is_active=True, status='active').select_related('seller', 'category')
    query = request.GET.get('q', '')
    results_count = 0
    
    if form.is_valid():
        # Search query
        if form.cleaned_data.get('q'):
            query = form.cleaned_data['q']
            search_query = Q(title__icontains=query) | Q(description__icontains=query) | Q(tags__icontains=query)
            products = products.filter(search_query)
        
        # Category filter
        if form.cleaned_data.get('category'):
            products = products.filter(category=form.cleaned_data['category'])
        
        # Price range filters
        if form.cleaned_data.get('min_price'):
            products = products.filter(price__gte=form.cleaned_data['min_price'])
        
        if form.cleaned_data.get('max_price'):
            products = products.filter(price__lte=form.cleaned_data['max_price'])
        
        # File format filter
        if form.cleaned_data.get('file_format'):
            products = products.filter(file_format__icontains=form.cleaned_data['file_format'])
        
        # Tags filter
        if form.cleaned_data.get('tags'):
            tag_list = [tag.strip() for tag in form.cleaned_data['tags'].split(',')]
            tag_query = Q()
            for tag in tag_list:
                tag_query |= Q(tags__icontains=tag)
            products = products.filter(tag_query)
        
        # Featured products only
        if form.cleaned_data.get('featured_only'):
            products = products.filter(is_featured=True)
        
        # Sorting
        sort_option = form.cleaned_data.get('sort', 'relevance')
        if sort_option == 'newest':
            products = products.order_by('-created_at')
        elif sort_option == 'oldest':
            products = products.order_by('created_at')
        elif sort_option == 'price_low':
            products = products.order_by('price')
        elif sort_option == 'price_high':
            products = products.order_by('-price')
        elif sort_option == 'popular':
            products = products.order_by('-purchase_count', '-download_count')
        elif sort_option == 'downloads':
            products = products.order_by('-download_count')
        else:  # relevance or default
            if query:
                # For relevance, prioritize title matches over description matches
                products = products.extra(
                    select={
                        'title_match': "CASE WHEN title ILIKE %s THEN 1 ELSE 0 END"
                    },
                    select_params=[f'%{query}%']
                ).order_by('-title_match', '-created_at')
            else:
                products = products.order_by('-created_at')
    
    results_count = products.count()
    
    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get popular categories for sidebar
    popular_categories = Category.objects.filter(
        is_active=True,
        products__is_active=True,
        products__status='active'
    ).annotate(
        product_count=Count('products')
    ).filter(product_count__gt=0).order_by('-product_count')[:6]
    
    context = {
        'form': form,
        'products': page_obj,
        'query': query,
        'results_count': results_count,
        'popular_categories': popular_categories,
        'page_obj': page_obj,
    }
    
    return render(request, 'catalog/search.html', context)


def quick_search(request):
    """
    Quick search from navigation bar - redirects to full search.
    """
    form = QuickSearchForm(request.GET)
    if form.is_valid() and form.cleaned_data.get('q'):
        # Redirect to full search page with query
        from django.shortcuts import redirect
        return redirect(f"/search/?q={form.cleaned_data['q']}")
    
    # If no query, redirect to search page
    from django.shortcuts import redirect
    return redirect('/search/')