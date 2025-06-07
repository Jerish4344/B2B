from django.contrib import admin
from .models import *

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'contact_person', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'email', 'contact_person']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'head_name', 'head_email', 'created_at']
    search_fields = ['name', 'head_name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'supplier', 'category', 'current_price', 'proposed_price', 'proposed_stock', 'is_active']
    list_filter = ['category', 'supplier', 'is_active', 'created_at']
    search_fields = ['name', 'supplier__name']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'supplier', 'status', 'total_amount', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['po_number', 'supplier__name']

@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'manager_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'location', 'manager_name']

@admin.register(ProductStock)
class ProductStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'shop', 'quantity', 'updated_at']
    list_filter = ['shop', 'updated_at']
    search_fields = ['product__name', 'shop__name']

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'product', 'quantity', 'unit_price', 'total_price']
    list_filter = ['purchase_order']
    search_fields = ['purchase_order__po_number', 'product__name']
