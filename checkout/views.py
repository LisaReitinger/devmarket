from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.urls import reverse
from catalog.models import Product
from cart.models import Cart
from orders.models import Order, OrderItem
import stripe
import json
import logging

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)


@login_required
def checkout_view(request):
    """Display checkout page with order summary"""
    cart = get_object_or_404(Cart, user=request.user)
    
    if cart.is_empty:
        messages.error(request, "Your cart is empty!")
        return redirect('cart:cart_view')
    
    # Check if Stripe is configured
    if not settings.STRIPE_SECRET_KEY or not settings.STRIPE_PUBLISHABLE_KEY:
        messages.error(request, "Payment system is not configured. Please contact support.")
        return redirect('cart:cart_view')
    
    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('product').all(),
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY,
    }
    return render(request, 'checkout/checkout.html', context)


@login_required
@require_POST
def create_checkout_session(request):
    """Create Stripe checkout session"""
    try:
        cart = get_object_or_404(Cart, user=request.user)
        
        if cart.is_empty:
            return JsonResponse({'error': 'Cart is empty'}, status=400)
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            email=request.user.email,
            total_amount=cart.total_price,
            status='pending'
        )
        
        # Create order items
        line_items = []
        for cart_item in cart.items.select_related('product').all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                price=cart_item.price,
                product_title=cart_item.product.title,
                product_slug=cart_item.product.slug
            )
            
            line_items.append({
                'price_data': {
                    'currency': settings.STRIPE_CURRENCY,
                    'product_data': {
                        'name': cart_item.product.title,
                        'description': cart_item.product.short_description or 'Digital Product',
                        'images': [request.build_absolute_uri(cart_item.product.featured_image.url)] if cart_item.product.featured_image else [],
                    },
                    'unit_amount': int(cart_item.price * 100),  # Stripe expects cents
                },
                'quantity': 1,
            })
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(reverse('checkout:success')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('checkout:cancel')),
            metadata={
                'order_id': str(order.id),
                'user_id': str(request.user.id),
            }
        )
        
        # Store session ID in order
        order.stripe_session_id = checkout_session.id
        order.save()
        
        return JsonResponse({'checkout_url': checkout_session.url})
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return JsonResponse({'error': 'Failed to create checkout session'}, status=500)


@login_required
def checkout_success(request):
    """Handle successful payment"""
    session_id = request.GET.get('session_id')
    
    if not session_id:
        messages.error(request, "Invalid session!")
        return redirect('cart:cart_view')
    
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Get the order
        order = get_object_or_404(Order, stripe_session_id=session_id, user=request.user)
        
        if session.payment_status == 'paid' and order.status == 'pending':
            # Mark order as completed
            order.mark_completed()
            order.stripe_payment_intent_id = session.payment_intent
            order.save()
            
            # Clear the user's cart
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart.clear()
            
            # Update product purchase counts
            for item in order.items.all():
                item.product.increment_purchase_count()
            
            messages.success(request, f"Payment successful! Order #{order.id} is complete.")
            return render(request, 'checkout/success.html', {'order': order})
        
        elif session.payment_status == 'paid':
            # Already processed
            return render(request, 'checkout/success.html', {'order': order})
        
        else:
            messages.error(request, "Payment was not completed successfully.")
            return redirect('checkout:cancel')
            
    except Exception as e:
        logger.error(f"Error processing successful payment: {str(e)}")
        messages.error(request, "There was an error processing your payment.")
        return redirect('cart:cart_view')


def checkout_cancel(request):
    """Handle cancelled payment"""
    messages.info(request, "Payment was cancelled. Your cart is still available.")
    return redirect('cart:cart_view')


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload in Stripe webhook")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature in Stripe webhook")
        return HttpResponse(status=400)
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        try:
            order = Order.objects.get(stripe_session_id=session['id'])
            if order.status == 'pending':
                order.mark_completed()
                order.stripe_payment_intent_id = session.get('payment_intent')
                order.save()
                
                logger.info(f"Order {order.id} marked as completed via webhook")
        except Order.DoesNotExist:
            logger.error(f"Order not found for session {session['id']}")
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        
        try:
            order = Order.objects.get(stripe_payment_intent_id=payment_intent['id'])
            order.status = 'failed'
            order.save()
            
            logger.info(f"Order {order.id} marked as failed via webhook")
        except Order.DoesNotExist:
            logger.error(f"Order not found for payment intent {payment_intent['id']}")
    
    return HttpResponse(status=200)


@login_required
def buy_now(request, product_slug):
    """Direct buy now functionality (bypass cart)"""
    if request.method == 'POST':
        product = get_object_or_404(Product, slug=product_slug, is_active=True)
        
        # Create order directly
        order = Order.objects.create(
            user=request.user,
            email=request.user.email,
            total_amount=product.price,
            status='pending'
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            product_title=product.title,
            product_slug=product.slug
        )
        
        try:
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': settings.STRIPE_CURRENCY,
                        'product_data': {
                            'name': product.title,
                            'description': product.short_description or 'Digital Product',
                            'images': [request.build_absolute_uri(product.featured_image.url)] if product.featured_image else [],
                        },
                        'unit_amount': int(product.price * 100),  # Stripe expects cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri(reverse('checkout:success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('checkout:cancel')),
                metadata={
                    'order_id': str(order.id),
                    'user_id': str(request.user.id),
                }
            )
            
            # Store session ID in order
            order.stripe_session_id = checkout_session.id
            order.save()
            
            return redirect(checkout_session.url)
            
        except Exception as e:
            logger.error(f"Error creating buy now checkout session: {str(e)}")
            messages.error(request, "Failed to create checkout session. Please try again.")
            return redirect('catalog:product_detail', slug=product_slug)
    
    return redirect('catalog:product_detail', slug=product_slug)