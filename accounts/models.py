from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """
    Profile model extending Django's User model with role-based marketplace functionality.
    Supports buyer, seller, and admin roles for the DevMarket platform.
    """
    ROLE_CHOICES = (
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    bio = models.TextField(blank=True, help_text="Tell us about yourself")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s profile ({self.get_role_display()})"
    
    @property
    def is_seller(self):
        """Check if user has seller role"""
        return self.role == 'seller'
    
    @property
    def is_buyer(self):
        """Check if user has buyer role"""
        return self.role == 'buyer'
    
    @property
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    @property
    def full_name(self):
        """Get user's full name or username if not available"""
        if self.user.first_name and self.user.last_name:
            return f"{self.user.first_name} {self.user.last_name}"
        return self.user.username


# Signal handlers for automatic profile creation
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a Profile whenever a new User is created"""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the Profile whenever the User is saved"""
    # Create profile if it doesn't exist (for existing users)
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()
