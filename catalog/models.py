from django.db import models
from django.urls import reverse
from django.utils.text import slugify


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
        # This will work once we create the Product model
        count = self.products.filter(is_active=True).count()
        for child in self.children.all():
            count += child.get_product_count()
        return count
