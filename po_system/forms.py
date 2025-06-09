# po_system/forms.py - Updated ProductForm with radio button units

from django import forms
from .models import *
from django.core.validators import MinValueValidator
from decimal import Decimal

# Update your ProductForm in po_system/forms.py

from django import forms
from .models import *
from django.core.validators import MinValueValidator
from decimal import Decimal

# Update your ProductForm in po_system/forms.py

from django import forms
from .models import *
from django.core.validators import MinValueValidator
from decimal import Decimal

class ProductForm(forms.ModelForm):
    """Form for adding/editing products with unit choices"""
    
    # Define unit choices
    UNIT_CHOICES = [
        ('Kg', 'Kilogram (Kg)'),
        ('gm', 'Gram (gm)'),
        ('nos', 'Numbers (nos)'),
        ('dozen', 'Dozen'),
        ('pairs', 'Pairs'),
        ('ltr', 'Liter (ltr)'),
        ('ml', 'Milliliter (ml)'),
    ]
    
    # Override the unit field to use radio buttons
    unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='Kg',
        help_text='Select the appropriate unit for this product'
    )
    
    class Meta:
        model = Product
        fields = ['name', 'supplier', 'category', 'current_price', 'proposed_price', 'proposed_stock', 'unit', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'current_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'proposed_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'proposed_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Product Description'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make proposed_price and proposed_stock optional (not required)
        self.fields['proposed_price'].required = False
        self.fields['proposed_stock'].required = False
        
        # You can also make description optional if needed
        self.fields['description'].required = False
        
        # Update help text to indicate optional fields
        self.fields['proposed_price'].help_text = 'Optional: Proposed price for this product'
        self.fields['proposed_stock'].help_text = 'Optional: Proposed stock quantity'

class SupplierForm(forms.ModelForm):
    """Form for adding/editing suppliers"""
    class Meta:
        model = Supplier
        fields = ['name', 'email', 'phone', 'address', 'contact_person', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Address'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Person'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CategoryForm(forms.ModelForm):
    """Form for adding/editing product categories"""
    class Meta:
        model = Category
        fields = ['name', 'head_email', 'head_name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Name'}),
            'head_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Category Head Email'}),
            'head_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category Head Name'}),
        }

class ShopForm(forms.ModelForm):
    """Form for adding/editing shops"""
    class Meta:
        model = Shop
        fields = ['name', 'location', 'manager_name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Shop Name'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location'}),
            'manager_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Manager Name'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductStockForm(forms.ModelForm):
    """Form for managing product stock levels"""
    class Meta:
        model = ProductStock
        fields = ['product', 'shop', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'shop': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active products and shops
        self.fields['product'].queryset = Product.objects.filter(is_active=True)
        self.fields['shop'].queryset = Shop.objects.filter(is_active=True)

class BulkUploadForm(forms.Form):
    csv_file = forms.FileField(
        label='Upload CSV File',
        help_text='CSV should contain: supplier_name, supplier_email, product_name, category_name, current_price, proposed_price, proposed_stock, unit',
        widget=forms.FileInput(attrs={'accept': '.csv', 'class': 'form-control'})
    )

class PurchaseOrderFilterForm(forms.Form):
    """Form for filtering purchase orders"""
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    DATE_CHOICES = [
        ('', 'All Time'),
        ('today', 'Today'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('quarter', 'This Quarter'),
    ]
    
    q = forms.CharField(
        label='Search', 
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by PO number'})
    )
    
    status = forms.ChoiceField(
        label='Status',
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    supplier = forms.ModelChoiceField(
        label='Supplier',
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        empty_label='All Suppliers',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_range = forms.ChoiceField(
        label='Date Range',
        choices=DATE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )