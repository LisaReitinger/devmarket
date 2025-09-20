from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from catalog.models import Product
from .models import Cart, CartItem
import json


@login_required
def cart_view(request):
    """Display the shopping cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': cart.total_price,
        'total_items': cart.total_items,
    }
    return render(request, 'cart/cart.html', context)


@login_required
@require_POST
def add_to_cart(request, product_slug):
    """Add a product to the cart"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    # Check if user already owns this product (prevent duplicate purchases)
    if hasattr(request.user, 'purchased_products'):
        if request.user.purchased_products.filter(id=product.id).exists():
            messages.error(request, "You already own this product!")
            return redirect('catalog:product_detail', slug=product_slug)
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Check if product is already in cart
    if cart.items.filter(product=product).exists():
        messages.info(request, f"{product.title} is already in your cart!")
    else:
        cart.add_product(product)
        messages.success(request, f"{product.title} added to cart!")
    
    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"{product.title} added to cart!",
            'cart_total': cart.total_items
        })
    
    return redirect('catalog:product_detail', slug=product_slug)


@login_required
@require_POST
def remove_from_cart(request, product_slug):
    """Remove a product from the cart"""
    product = get_object_or_404(Product, slug=product_slug)
    cart = get_object_or_404(Cart, user=request.user)
    
    if cart.remove_product(product):
        messages.success(request, f"{product.title} removed from cart!")
    else:
        messages.error(request, "Product not found in cart!")
    
    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"{product.title} removed from cart!",
            'cart_total': cart.total_items
        })
    
    return redirect('cart:cart_view')


@login_required
@require_POST
def clear_cart(request):
    """Clear all items from the cart"""
    cart = get_object_or_404(Cart, user=request.user)
    cart.clear()
    messages.success(request, "Cart cleared!")
    
    return redirect('cart:cart_view')


@login_required
def cart_count(request):
    """Get cart item count for AJAX requests"""
    try:
        cart = Cart.objects.get(user=request.user)
        count = cart.total_items
    except Cart.DoesNotExist:
        count = 0
    
    return JsonResponse({'count': count})