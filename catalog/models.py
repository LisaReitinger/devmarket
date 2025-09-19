from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Category(models.Model):
    """
    Category model for organizing digital products in the marketplace.
    Supports hierarchical categories (parent/child relationships) as shown in wireframes.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Category name (e.g., 'Web Templates')")
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text="URL-friendly version of name")
    description = models.TextField(blank=True, help_text="Brief description of what this category contains")
    
    # Hierarchy support - categories can have parent categories
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        help_text="Parent category (leave empty for top-level categories)"
    )
    
    # Display and organization
    icon = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="CSS icon class (e.g., 'fas fa-code' for web development)"
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True, help_text="Category thumbnail image")
    is_active = models.BooleanField(default=True, help_text="Whether this category is visible on the site")
    
    # SEO and metadata
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO meta description")
    
    # Ordering and timestamps
    sort_order = models.PositiveIntegerField(default=0, help_text="Lower numbers appear first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']
        
    def __str__(self):
        """String representation showing hierarchy"""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided"""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """URL to view products in this category"""
        return reverse('catalog:category', kwargs={'slug': self.slug})
    
    @property
    def get_full_path(self):
        """Get full category path (e.g., 'Development > Web Templates')"""
        if self.parent:
            return f"{self.parent.get_full_path} > {self.name}"
        return self.name
    
    @property
    def is_top_level(self):
        """Check if this is a top-level category"""
        return self.parent is None
    
    def get_descendants(self):
        """Get all descendant categories (children, grandchildren, etc.)"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    def get_product_count(self):
        """Get number of products in this category and all subcategories"""
        count = self.products.filter(is_active=True).count()
        for child in self.children.all():
            count += child.get_product_count()
        return count


class Product(models.Model):
    """
    Digital product model for the marketplace.
    Handles digital downloads, pricing, and seller relationships.
    """
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('rejected', 'Rejected'),
    )
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, help_text="Product title as shown to customers")
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL-friendly version")
    description = models.TextField(help_text="Detailed product description")
    short_description = models.CharField(max_length=500, blank=True, help_text="Brief summary for listings")
    
    # Relationships
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', help_text="Product seller")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', help_text="Product category")
    
    # Pricing
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text="Product price in dollars"
    )
    
    # Digital Files
    main_file = models.FileField(
        upload_to='products/files/', 
        help_text="Main digital product file (ZIP, PSD, etc.)"
    )
    preview_file = models.FileField(
        upload_to='products/previews/', 
        blank=True, 
        null=True,
        help_text="Preview file for customers (optional)"
    )
    
    # Images
    featured_image = models.ImageField(
        upload_to='products/images/',
        help_text="Main product image shown in listings"
    )
    image_2 = models.ImageField(upload_to='products/images/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='products/images/', blank=True, null=True)
    image_4 = models.ImageField(upload_to='products/images/', blank=True, null=True)
    
    # Product Details
    file_format = models.CharField(max_length=100, blank=True, help_text="e.g., 'PSD, AI, FIGMA'")
    file_size = models.CharField(max_length=50, blank=True, help_text="e.g., '15.2 MB'")
    compatibility = models.CharField(max_length=200, blank=True, help_text="e.g., 'Adobe Photoshop CS6+'")
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Status and Metrics
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True, help_text="Whether product is visible to customers")
    is_featured = models.BooleanField(default=False, help_text="Featured products appear prominently")
    
    # Sales and Downloads
    download_count = models.PositiveIntegerField(default=0, help_text="Total number of downloads")
    purchase_count = models.PositiveIntegerField(default=0, help_text="Total number of purchases")
    
    # SEO
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO page title")
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO meta description")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True, help_text="When product was first published")
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['is_featured', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.seller.username}"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug and handle publishing"""
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Set published_at when first published
        if self.status == 'active' and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """URL to product detail page"""
        return reverse('catalog:product_detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self):
        """Check if product is published and active"""
        return self.status == 'active' and self.is_active
    
    @property
    def seller_profile(self):
        """Get seller's profile"""
        return self.seller.profile
    
    @property
    def can_be_purchased(self):
        """Check if product can be purchased"""
        return self.is_published and self.seller.profile.role in ['seller', 'admin']
    
    def get_tags_list(self):
        """Get tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def get_main_image(self):
        """Get the main product image"""
        return self.featured_image
    
    def get_additional_images(self):
        """Get list of additional product images"""
        images = []
        for img_field in [self.image_2, self.image_3, self.image_4]:
            if img_field:
                images.append(img_field)
        return images
    
    def increment_download_count(self):
        """Increment download counter"""
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    def increment_purchase_count(self):
        """Increment purchase counter"""
        self.purchase_count += 1
        self.save(update_fields=['purchase_count'])
