from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Category management with hierarchy support"""
    
    list_display = ('name', 'parent', 'get_hierarchy_level', 'product_count', 'is_active', 'sort_order', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    # Organize fields in admin form
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'parent')
        }),
        ('Display & SEO', {
            'fields': ('icon', 'image', 'meta_description', 'is_active', 'sort_order')
        }),
    )
    
    # Inline editing
    list_editable = ('sort_order', 'is_active')
    
    # Ordering and pagination
    ordering = ('sort_order', 'name')
    list_per_page = 50
    
    def get_hierarchy_level(self, obj):
        """Display visual hierarchy level in admin list"""
        level = 0
        parent = obj.parent
        while parent:
            level += 1
            parent = parent.parent
        
        indent = '&nbsp;&nbsp;&nbsp;&nbsp;' * level
        if level > 0:
            return format_html(f'{indent}└─ Level {level}')
        return 'Top Level'
    get_hierarchy_level.short_description = 'Hierarchy'
    get_hierarchy_level.allow_tags = True
    
    def product_count(self, obj):
        """Show product count for each category"""
        try:
            return obj.get_product_count()
        except:
            return 0  # Will return 0 until Product model is created
    product_count.short_description = 'Products'
    
    def get_queryset(self, request):
        """Optimize queries for admin list view"""
        qs = super().get_queryset(request)
        return qs.select_related('parent')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize parent category choices to prevent circular references"""
        if db_field.name == "parent":
            # Exclude self when editing existing category
            if request.resolver_match.kwargs.get('object_id'):
                category_id = request.resolver_match.kwargs['object_id']
                kwargs["queryset"] = Category.objects.exclude(pk=category_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        """Bulk action to make categories active"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} categories were successfully marked as active.')
    make_active.short_description = "Mark selected categories as active"
    
    def make_inactive(self, request, queryset):
        """Bulk action to make categories inactive"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} categories were successfully marked as inactive.')
    make_inactive.short_description = "Mark selected categories as inactive"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Enhanced admin interface for Product management"""
    
    list_display = (
        'get_image_preview', 'title', 'seller', 'category', 'price', 
        'status', 'is_featured', 'purchase_count', 'download_count', 'created_at'
    )
    list_filter = ('status', 'is_active', 'is_featured', 'category', 'created_at', 'seller')
    search_fields = ('title', 'description', 'tags', 'seller__username')
    prepopulated_fields = {'slug': ('title',)}
    
    # Organize fields in admin form
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'short_description', 'seller', 'category')
        }),
        ('Pricing & Status', {
            'fields': ('price', 'status', 'is_active', 'is_featured')
        }),
        ('Files & Images', {
            'fields': ('main_file', 'preview_file', 'featured_image', 'image_2', 'image_3', 'image_4')
        }),
        ('Product Details', {
            'fields': ('file_format', 'file_size', 'compatibility', 'tags')
        }),
        ('SEO & Metadata', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('download_count', 'purchase_count', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Read-only fields
    readonly_fields = ('download_count', 'purchase_count', 'published_at', 'created_at', 'updated_at')
    
    # Inline editing
    list_editable = ('price', 'status', 'is_featured')
    
    # Ordering and pagination
    ordering = ('-created_at',)
    list_per_page = 25
    
    # Date hierarchy
    date_hierarchy = 'created_at'
    
    def get_image_preview(self, obj):
        """Show thumbnail preview in admin list"""
        if obj.featured_image:
            return mark_safe(f'<img src="{obj.featured_image.url}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />')
        return "No Image"
    get_image_preview.short_description = 'Preview'
    
    def get_queryset(self, request):
        """Optimize queries for admin list view"""
        qs = super().get_queryset(request)
        return qs.select_related('seller', 'seller__profile', 'category')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Customize seller choices based on user role"""
        if db_field.name == "seller":
            # Only show users with seller or admin role
            from accounts.models import Profile
            seller_profiles = Profile.objects.filter(role__in=['seller', 'admin'])
            kwargs["queryset"] = User.objects.filter(profile__in=seller_profiles)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """Auto-assign current user as seller if not set and user can sell"""
        if not obj.seller_id and request.user.profile.role in ['seller', 'admin']:
            obj.seller = request.user
        super().save_model(request, obj, form, change)
    
    # Custom actions
    actions = ['make_active', 'make_inactive', 'make_featured', 'remove_featured', 'approve_products']
    
    def make_active(self, request, queryset):
        """Bulk action to activate products"""
        updated = queryset.update(status='active', is_active=True)
        self.message_user(request, f'{updated} products were successfully activated.')
    make_active.short_description = "Activate selected products"
    
    def make_inactive(self, request, queryset):
        """Bulk action to deactivate products"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} products were successfully deactivated.')
    make_inactive.short_description = "Deactivate selected products"
    
    def make_featured(self, request, queryset):
        """Bulk action to feature products"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} products were successfully featured.')
    make_featured.short_description = "Feature selected products"
    
    def remove_featured(self, request, queryset):
        """Bulk action to unfeature products"""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} products were successfully unfeatured.')
    remove_featured.short_description = "Remove featured status"
    
    def approve_products(self, request, queryset):
        """Bulk action to approve pending products"""
        updated = queryset.filter(status='pending').update(status='active')
        self.message_user(request, f'{updated} products were successfully approved.')
    approve_products.short_description = "Approve pending products"
