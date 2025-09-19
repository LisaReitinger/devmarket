from django import forms
from .models import Category, Product


class ProductSearchForm(forms.Form):
    """
    Advanced product search and filtering form.
    """
    SORT_CHOICES = (
        ('relevance', 'Relevance'),
        ('newest', 'Newest First'),
        ('oldest', 'Oldest First'),
        ('price_low', 'Price: Low to High'),
        ('price_high', 'Price: High to Low'),
        ('popular', 'Most Popular'),
        ('downloads', 'Most Downloads'),
    )
    
    # Search query
    q = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Search for digital products...',
            'autocomplete': 'off'
        }),
        label='Search'
    )
    
    # Category filter
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True).order_by('name'),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    # Price range filters
    min_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Min price',
            'min': '0',
            'step': '0.01'
        }),
        label='Min Price'
    )
    
    max_price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Max price',
            'min': '0',
            'step': '0.01'
        }),
        label='Max Price'
    )
    
    # File format filter
    file_format = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'e.g., PSD, ZIP, AI, PDF'
        }),
        label='File Format'
    )
    
    # Tags filter
    tags = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Enter tags separated by commas'
        }),
        label='Tags'
    )
    
    # Sort options
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='relevance',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    # Featured products only
    featured_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        }),
        label='Featured products only'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add form-wide CSS classes
        for field_name, field in self.fields.items():
            if field_name not in ['featured_only']:  # Skip checkbox fields
                field.widget.attrs['class'] += ' transition-colors duration-200'


class QuickSearchForm(forms.Form):
    """
    Simple search form for the navigation bar.
    """
    q = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 text-sm',
            'placeholder': 'Search products...',
            'autocomplete': 'off'
        }),
        label=''
    )
