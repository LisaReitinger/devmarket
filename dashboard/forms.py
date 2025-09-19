from django import forms
from catalog.models import Product, Category


class ProductForm(forms.ModelForm):
    """
    Form for creating new products in the seller dashboard.
    """
    
    class Meta:
        model = Product
        fields = [
            'title', 'category', 'description', 'short_description',
            'price', 'main_file', 'preview_file', 'featured_image',
            'image_2', 'image_3', 'image_4', 'file_format', 'file_size',
            'compatibility', 'tags'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter product title'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'rows': 6,
                'placeholder': 'Detailed product description...'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Brief product summary (max 500 characters)'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'main_file': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'accept': '.zip,.rar,.psd,.ai,.sketch,.fig,.pdf,.eps'
            }),
            'preview_file': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*,.pdf'
            }),
            'featured_image': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
            'image_2': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
            'image_3': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
            'image_4': forms.FileInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'accept': 'image/*'
            }),
            'file_format': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., PSD, AI, ZIP, PDF'
            }),
            'file_size': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., 25 MB, 1.2 GB'
            }),
            'compatibility': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., Photoshop CS6+, Illustrator CC+'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Separate tags with commas (e.g., web design, template, modern)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter categories to show only active ones
        self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('name')
        
        # Add help text
        self.fields['main_file'].help_text = "Upload the main product file (ZIP, PSD, AI, etc.) - Max 100MB"
        self.fields['preview_file'].help_text = "Optional preview file for customers"
        self.fields['featured_image'].help_text = "Main product image shown in listings (required)"
        self.fields['tags'].help_text = "Enter relevant tags separated by commas to help customers find your product"
        self.fields['price'].help_text = "Set your product price in USD"
        
        # Make required fields more obvious
        required_fields = ['title', 'category', 'description', 'price', 'main_file', 'featured_image']
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['required'] = True
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0.01:
            raise forms.ValidationError("Price must be at least $0.01")
        return price
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            # Clean up tags: strip whitespace, remove duplicates
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            if len(tag_list) > 20:
                raise forms.ValidationError("Maximum 20 tags allowed")
            return ', '.join(tag_list)
        return tags


class ProductUpdateForm(ProductForm):
    """
    Form for updating existing products. Similar to ProductForm but with some modifications.
    """
    
    class Meta(ProductForm.Meta):
        # Inherit all fields from ProductForm
        pass
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make file fields optional for updates
        self.fields['main_file'].required = False
        self.fields['featured_image'].required = False
        
        # Update help text for file fields
        self.fields['main_file'].help_text = "Upload a new file to replace the current one (optional)"
        self.fields['featured_image'].help_text = "Upload a new image to replace the current one (optional)"
        
        # Add current file info to help text if instance exists
        if self.instance and self.instance.pk:
            if self.instance.main_file:
                current_file = self.instance.main_file.name.split('/')[-1]
                self.fields['main_file'].help_text += f" | Current: {current_file}"
            
            if self.instance.featured_image:
                current_image = self.instance.featured_image.name.split('/')[-1]
                self.fields['featured_image'].help_text += f" | Current: {current_image}"


class ProductSearchForm(forms.Form):
    """
    Form for searching products in the seller dashboard.
    """
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('pending', 'Pending Review'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('rejected', 'Rejected'),
    ]
    
    q = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Search your products...'
        }),
        label='Search'
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500'
        })
    )
