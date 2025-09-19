from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    """Inline Profile admin to show with User"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('role', 'bio', 'avatar')


class UserAdmin(BaseUserAdmin):
    """Extended User admin with Profile inline"""
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role', 'date_joined')
    
    def get_role(self, obj):
        """Display user's role in list view"""
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return 'No Profile'
    get_role.short_description = 'Role'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Standalone Profile admin for direct profile management"""
    list_display = ('user', 'get_full_name', 'role', 'created_at', 'updated_at')
    list_filter = ('role', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'bio')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Profile Details', {
            'fields': ('role', 'bio', 'avatar')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        """Display user's full name in list view"""
        return obj.full_name
    get_full_name.short_description = 'Full Name'


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
