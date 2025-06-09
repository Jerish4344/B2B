# po_system/urls.py - Updated with email functionality

from django.urls import path
from . import views

app_name = 'po_system'

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Main application URLs
    path('', views.dashboard, name='dashboard'),
    path('suppliers/', views.supplier_search, name='supplier_search'),
    path('suppliers/<int:supplier_id>/products/', views.supplier_products, name='supplier_products'),
    path('send-po/', views.send_purchase_order, name='send_po'),
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
    
    # Purchase Order URLs
    path('purchase-orders/', views.purchase_orders, name='purchase_orders'),
    path('create-po/', views.create_po, name='create_po'),
    path('po/<int:po_id>/confirm/', views.confirm_po, name='confirm_po'),
    path('po/<int:po_id>/', views.po_detail, name='po_detail'),
    path('po/<int:po_id>/print/', views.print_po, name='print_po'),
    path('po/<int:po_id>/send/', views.send_po_email_view, name='send_po_email'),
    path('po/<int:po_id>/cancel/', views.cancel_po, name='cancel_po'),
    
    # Email Management URLs - NEW
    path('email-settings/', views.email_settings_view, name='email_settings'),
    path('test-email/', views.test_email_view, name='test_email'),
    
    # Supplier Management URLs
    path('suppliers/list/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:supplier_id>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:supplier_id>/delete/', views.supplier_delete, name='supplier_delete'),
    
    # Category Management URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    
    # Shop Management URLs
    path('shops/', views.shop_list, name='shop_list'),
    path('shops/create/', views.shop_create, name='shop_create'),
    path('shops/<int:shop_id>/edit/', views.shop_edit, name='shop_edit'),
    path('shops/<int:shop_id>/delete/', views.shop_delete, name='shop_delete'),
    
    # Product Management URLs
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    
    # Stock Management URLs
    path('stocks/', views.stock_list, name='stock_list'),
    path('stocks/create/', views.stock_create, name='stock_create'),
    path('stocks/<int:stock_id>/edit/', views.stock_edit, name='stock_edit'),
    path('stocks/<int:stock_id>/delete/', views.stock_delete, name='stock_delete'),
]