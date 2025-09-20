from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product
from decimal import Decimal


class Cart(models.Model):
    """Shopping cart for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_items(self):
        """Get total number of items in cart"""
        return self.items.count()

    @property
    def total_price(self):
        """Calculate total price of all items in cart"""
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.get_total_price()
        return total

    @property
    def is_empty(self):
        """Check if cart is empty"""
        return self.items.count() == 0

    def add_product(self, product):
        """Add a product to cart (digital products don't need quantity)"""
        cart_item, created = CartItem.objects.get_or_create(
            cart=self,
            product=product,
            defaults={'price': product.price}
        )
        return cart_item

    def remove_product(self, product):
        """Remove a product from cart"""
        try:
            cart_item = self.items.get(product=product)
            cart_item.delete()
            return True
        except CartItem.DoesNotExist:
            return False

    def clear(self):
        """Remove all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    """Individual item in shopping cart"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product']  # Prevent duplicate items

    def __str__(self):
        return f"{self.product.title} in {self.cart.user.username}'s cart"

    def get_total_price(self):
        """Get total price for this item (price * 1 for digital products)"""
        return self.price

    @property
    def product_title(self):
        """Get product title"""
        return self.product.title

    @property
    def product_slug(self):
        """Get product slug for URL generation"""
        return self.product.slug