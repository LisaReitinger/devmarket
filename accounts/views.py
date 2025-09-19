from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile
from .forms import CustomUserCreationForm, ProfileUpdateForm


def register_view(request):
    """
    User registration view with automatic profile creation.
    """
    if request.user.is_authenticated:
        return redirect('pages:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Login the user automatically after registration
            login(request, user)
            messages.success(request, f'Welcome to DevMarket, {username}! Your account has been created successfully.')
            
            # Redirect to profile completion or home
            return redirect('accounts:profile')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    Custom login view with beautiful template.
    """
    if request.user.is_authenticated:
        return redirect('pages:home')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to next page or home
            next_page = request.GET.get('next', 'pages:home')
            return redirect(next_page)
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """
    Logout view with confirmation message.
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'You have been logged out successfully. See you soon, {username}!')
    
    return redirect('pages:home')


@login_required
def profile_view(request):
    """
    User profile view showing user information and activity.
    """
    user = request.user
    profile = user.profile
    
    # Get user's purchased products (we'll implement this later)
    # purchased_products = []
    
    # Get user's products if they're a seller
    if profile.is_seller or profile.is_admin:
        from catalog.models import Product
        user_products = Product.objects.filter(seller=user).order_by('-created_at')[:5]
    else:
        user_products = []
    
    context = {
        'user': user,
        'profile': profile,
        'user_products': user_products,
        # 'purchased_products': purchased_products,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit_view(request):
    """
    Edit user profile information.
    """
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    context = {
        'form': form,
        'user': user,
        'profile': profile,
    }
    
    return render(request, 'accounts/profile_edit.html', context)