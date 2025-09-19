from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse

from catalog.models import Product, Category
from accounts.models import Profile
from .forms import ProductForm, ProductUpdateForm


@login_required
def dashboard_home(request):
    """
    Main dashboard overview for sellers.
    Shows key metrics, recent products, and quick actions.
    """
    # Check if user is a seller or admin
    if not (request.user.profile.is_seller or request.user.profile.is_admin):
        messages.error(request, 'Access denied. Only sellers can access the dashboard.')
        return redirect('pages:home')
    
    # Get user's products
    user_products = Product.objects.filter(seller=request.user)
    
    # Calculate metrics
    total_products = user_products.count()
    active_products = user_products.filter(status='active', is_active=True).count()
    pending_products = user_products.filter(status='pending').count()
    total_downloads = user_products.aggregate(total=Sum('download_count'))['total'] or 0
    total_purchases = user_products.aggregate(total=Sum('purchase_count'))['total'] or 0
    
    # Calculate total earnings (assuming price * purchase_count)
    total_earnings = 0
    for product in user_products:
        total_earnings += float(product.price) * product.purchase_count
    
    # Get recent products
    recent_products = user_products.order_by('-created_at')[:5]
    
    # Get popular products (by downloads)
    popular_products = user_products.filter(
        download_count__gt=0
    ).order_by('-download_count')[:5]
    
    context = {
        'total_products': total_products,
        'active_products': active_products,
        'pending_products': pending_products,
        'total_downloads': total_downloads,
        'total_purchases': total_purchases,
        'total_earnings': total_earnings,
        'recent_products': recent_products,
        'popular_products': popular_products,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def product_list(request):
    """
    List all products for the current seller with management options.
    """
    # Check seller permissions
    if not (request.user.profile.is_seller or request.user.profile.is_admin):
        messages.error(request, 'Access denied. Only sellers can access the dashboard.')
        return redirect('pages:home')
    
    # Get user's products with filtering
    products = Product.objects.filter(seller=request.user).order_by('-created_at')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        products = products.filter(status=status_filter)
    
    # Search functionality
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'page_obj': page_obj,
    }
    
    return render(request, 'dashboard/product_list.html', context)


@method_decorator(login_required, name='dispatch')
class ProductCreateView(CreateView):
    """
    Create a new product with file upload functionality.
    """
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:product_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Check seller permissions
        if not (request.user.profile.is_seller or request.user.profile.is_admin):
            messages.error(request, 'Access denied. Only sellers can add products.')
            return redirect('pages:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        messages.success(self.request, 'Product created successfully! It will be reviewed before going live.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Product'
        context['button_text'] = 'Create Product'
        return context


@method_decorator(login_required, name='dispatch')
class ProductUpdateView(UpdateView):
    """
    Update an existing product.
    """
    model = Product
    form_class = ProductUpdateForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:product_list')
    
    def dispatch(self, request, *args, **kwargs):
        # Check seller permissions and ownership
        if not (request.user.profile.is_seller or request.user.profile.is_admin):
            messages.error(request, 'Access denied. Only sellers can edit products.')
            return redirect('pages:home')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Only allow editing own products (unless admin)
        if self.request.user.profile.is_admin:
            return Product.objects.all()
        return Product.objects.filter(seller=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Product updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit: {self.object.title}'
        context['button_text'] = 'Update Product'
        return context


@login_required
def product_toggle_status(request, pk):
    """
    Toggle product active status via AJAX.
    """
    # Check seller permissions
    if not (request.user.profile.is_seller or request.user.profile.is_admin):
        return JsonResponse({'success': False, 'error': 'Permission denied'})
    
    # Get product and check ownership
    if request.user.profile.is_admin:
        product = get_object_or_404(Product, pk=pk)
    else:
        product = get_object_or_404(Product, pk=pk, seller=request.user)
    
    if request.method == 'POST':
        product.is_active = not product.is_active
        product.save()
        
        return JsonResponse({
            'success': True,
            'is_active': product.is_active,
            'message': f'Product {"activated" if product.is_active else "deactivated"} successfully'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def product_toggle_featured(request, pk):
    """
    Toggle product featured status via AJAX (admin only).
    """
    # Check admin permissions
    if not request.user.profile.is_admin:
        return JsonResponse({'success': False, 'error': 'Admin access required'})
    
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.is_featured = not product.is_featured
        product.save()
        
        return JsonResponse({
            'success': True,
            'is_featured': product.is_featured,
            'message': f'Product {"marked as featured" if product.is_featured else "removed from featured"}'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def analytics_view(request):
    """
    Detailed analytics view for sellers.
    """
    # Check seller permissions
    if not (request.user.profile.is_seller or request.user.profile.is_admin):
        messages.error(request, 'Access denied. Only sellers can access analytics.')
        return redirect('pages:home')
    
    # Get user's products
    user_products = Product.objects.filter(seller=request.user)
    
    # Product performance data
    product_stats = []
    for product in user_products.order_by('-purchase_count')[:10]:
        earnings = float(product.price) * product.purchase_count
        product_stats.append({
            'product': product,
            'earnings': earnings,
            'conversion_rate': (product.purchase_count / max(product.download_count, 1)) * 100
        })
    
    # Category performance
    category_stats = {}
    for product in user_products:
        category = product.category.name
        if category not in category_stats:
            category_stats[category] = {'products': 0, 'downloads': 0, 'purchases': 0, 'earnings': 0}
        
        category_stats[category]['products'] += 1
        category_stats[category]['downloads'] += product.download_count
        category_stats[category]['purchases'] += product.purchase_count
        category_stats[category]['earnings'] += float(product.price) * product.purchase_count
    
    context = {
        'product_stats': product_stats,
        'category_stats': category_stats,
        'total_products': user_products.count(),
        'total_earnings': sum([stat['earnings'] for stat in product_stats]),
    }
    
    return render(request, 'dashboard/analytics.html', context)