# po_system/models.py - Updated with unit choices

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone

class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()
    contact_person = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    head_email = models.EmailField()
    head_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class Shop(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    manager_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.location}"

class Product(models.Model):
    name = models.CharField(max_length=200)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    unit = models.CharField(max_length=20, default='Kg')
    current_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    
    # Make these fields optional by adding null=True, blank=True
    proposed_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        null=True,  # Allows NULL in database
        blank=True,  # Allows empty in forms
        help_text='Optional: Proposed price for this product'
    )
    proposed_stock = models.IntegerField(
        validators=[MinValueValidator(0)],
        null=True,  # Allows NULL in database
        blank=True,  # Allows empty in forms
        help_text='Optional: Proposed stock quantity'
    )
    
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.supplier.name}"

    @property
    def current_stock(self):
        """Calculate total current stock from all shops"""
        return sum(stock.quantity for stock in self.stocks.filter(shop__is_active=True))

    @property
    def total_value(self):
        """Calculate total value based on proposed price and stock"""
        if self.proposed_price and self.proposed_stock:
            return self.proposed_price * self.proposed_stock
        return 0

    class Meta:
        unique_together = ['name', 'supplier']

class ProductStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stocks')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'shop']

    def __str__(self):
        return f"{self.product.name} at {self.shop.name}: {self.quantity} {self.product.unit}"

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"PO-{self.po_number} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        if not self.po_number:
            self.po_number = self.generate_po_number()
        super().save(*args, **kwargs)

    def generate_po_number(self):
        """Generate unique PO number"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{timestamp}{str(uuid.uuid4())[:8].upper()}"
    
    def get_status_display(self):
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} {self.product.unit}"