from django.contrib import admin
from django.utils.html import format_html
from .models import Category


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
