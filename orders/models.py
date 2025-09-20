from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product
import uuid


class Order(models.Model):
    """Order model to track purchases"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    email = models.EmailField()  # Store email for guest orders in future
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Stripe fields
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.id} - {self.user.username} - ${self.total_amount}"

    @property
    def is_completed(self):
        """Check if order is completed"""
        return self.status == 'completed'

    def mark_completed(self):
        """Mark order as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def get_total_items(self):
        """Get total number of items in order"""
        return self.items.count()


class OrderItem(models.Model):
    """Individual item in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Store price at time of purchase
    
    # Product snapshot fields (in case product gets deleted/modified)
    product_title = models.CharField(max_length=255)
    product_slug = models.SlugField(max_length=255)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product_title} in Order {self.order.id}"

    @property
    def download_url(self):
        """Get download URL for the product file"""
        if self.product and self.product.main_file:
            return self.product.main_file.url
        return None