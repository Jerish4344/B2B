from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum, Count, Case, When, IntegerField, F
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.generic import ListView
from django.template.loader import render_to_string
import json
import csv
from io import StringIO
from decimal import Decimal
from datetime import datetime, timedelta

from po_management import settings
from .models import *
from .forms import *
from .services.email_service import email_service  # Import our email service
from .decorators import login_exempt

@login_exempt
def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('po_system:dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next')
            if not next_url:  # This will handle both None and empty string
                next_url = 'po_system:dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'po_system/login.html')

@login_exempt
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('po_system:login')

@login_exempt
def register_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('po_system:dashboard')
        
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Add email if provided
            email = request.POST.get('email')
            if email:
                user.email = email
                user.save()
                
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}. You can now log in.')
            
            # Auto-login after registration
            login(request, user)
            return redirect('po_system:dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'po_system/register.html', {'form': form})

@login_required
def dashboard(request):
    """Main dashboard view"""
    suppliers_count = Supplier.objects.filter(is_active=True).count()
    products_count = Product.objects.filter(is_active=True).count()
    pos_count = PurchaseOrder.objects.count()
    
    # Get recent purchase orders
    recent_purchase_orders = PurchaseOrder.objects.select_related('supplier').prefetch_related('items').order_by('-created_at')[:5]
    
    # Calculate PO status statistics
    total_pos = max(pos_count, 1)  # Avoid division by zero
    po_status = {
        'draft_count': PurchaseOrder.objects.filter(status='draft').count(),
        'sent_count': PurchaseOrder.objects.filter(status='sent').count(),
        'confirmed_count': PurchaseOrder.objects.filter(status='confirmed').count(),
        'cancelled_count': PurchaseOrder.objects.filter(status='cancelled').count(),
    }
    
    po_status['draft_percent'] = int((po_status['draft_count'] / total_pos) * 100)
    po_status['sent_percent'] = int((po_status['sent_count'] / total_pos) * 100)
    po_status['confirmed_percent'] = int((po_status['confirmed_count'] / total_pos) * 100)
    po_status['cancelled_percent'] = int((po_status['cancelled_count'] / total_pos) * 100)
    
    context = {
        'suppliers_count': suppliers_count,
        'products_count': products_count,
        'pos_count': pos_count,
        'today': timezone.now(),  # Add today's date for the dashboard
        'recent_purchase_orders': recent_purchase_orders,
        'po_status': po_status,
    }
    return render(request, 'po_system/dashboard.html', context)

@login_required
def supplier_search(request):
    """Search suppliers with AJAX support"""
    query = request.GET.get('q', '')
    suppliers = Supplier.objects.filter(is_active=True)
    
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) | 
            Q(contact_person__icontains=query)
        )
    
    paginator = Paginator(suppliers, 10)
    page = request.GET.get('page', 1)
    suppliers_page = paginator.get_page(page)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'suppliers': [
                {
                    'id': supplier.id,
                    'name': supplier.name,
                    'contact_person': supplier.contact_person,
                    'email': supplier.email,
                    'phone': supplier.phone,
                } for supplier in suppliers_page
            ],
            'has_next': suppliers_page.has_next(),
            'has_previous': suppliers_page.has_previous(),
        }
        return JsonResponse(data)
    
    return render(request, 'po_system/supplier_search.html', {
        'suppliers': suppliers_page,
        'query': query
    })

@login_required
def supplier_products(request, supplier_id):
    """Enhanced supplier products view with better data structure"""
    supplier = get_object_or_404(Supplier, id=supplier_id, is_active=True)
    products = Product.objects.filter(
        supplier=supplier, 
        is_active=True
    ).select_related('category').order_by('name')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Enhanced JSON response with all necessary data
        try:
            products_data = []
            for product in products:
                # Safely handle None values
                current_price = float(product.current_price) if product.current_price else 0.0
                proposed_price = float(product.proposed_price) if product.proposed_price else current_price
                current_stock = product.current_stock if product.current_stock is not None else 0
                proposed_stock = product.proposed_stock if product.proposed_stock is not None else 10
                
                product_data = {
                    'id': product.id,
                    'name': product.name or 'Unknown Product',
                    'current_price': current_price,
                    'proposed_price': proposed_price,
                    'current_stock': current_stock,
                    'proposed_stock': proposed_stock,
                    'total_value': proposed_price * proposed_stock,
                    'unit': product.unit or 'units',
                    'category': product.category.name if product.category else 'No Category',
                    'description': product.description or '',
                }
                products_data.append(product_data)
            
            data = {
                'supplier': {
                    'id': supplier.id,
                    'name': supplier.name or 'Unknown Supplier',
                    'email': supplier.email or '',
                    'contact_person': supplier.contact_person or '',
                    'phone': supplier.phone or '',
                    'address': supplier.address or '',
                },
                'products': products_data
            }
            
            return JsonResponse(data)
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in supplier_products AJAX: {str(e)}")
            
            return JsonResponse({
                'error': 'Failed to load products',
                'message': str(e)
            }, status=500)
    
    return render(request, 'po_system/supplier_products.html', {
        'supplier': supplier,
        'products': products
    })


@login_required
def bulk_upload(request):
    """Bulk upload products with enhanced duplicate detection and unit validation"""
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                csv_file = request.FILES['csv_file']
                decoded_file = csv_file.read().decode('utf-8')
                csv_data = csv.DictReader(StringIO(decoded_file))
                
                created_count = 0
                updated_count = 0
                skipped_count = 0
                errors = []
                
                # Valid unit choices
                valid_units = ['Kg', 'gm', 'nos', 'dozen', 'pairs', 'ml', 'ltr']
                
                for row_num, row in enumerate(csv_data, start=2):
                    try:
                        # Validate required fields
                        required_fields = ['supplier_name', 'product_name', 'category_name', 
                                         'current_price', 'proposed_price', 'proposed_stock']
                        
                        missing_fields = []
                        for field in required_fields:
                            if not row.get(field, '').strip():
                                missing_fields.append(field)
                        
                        if missing_fields:
                            errors.append(f"Row {row_num}: Missing required fields: {', '.join(missing_fields)}")
                            continue
                        
                        # Validate unit
                        unit = row.get('unit', 'Kg').strip()
                        if unit not in valid_units:
                            errors.append(f"Row {row_num}: Invalid unit '{unit}'. Valid units are: {', '.join(valid_units)}")
                            continue
                        
                        # Get or create supplier
                        supplier, _ = Supplier.objects.get_or_create(
                            name=row['supplier_name'].strip(),
                            defaults={
                                'email': row.get('supplier_email', '').strip(),
                                'phone': row.get('supplier_phone', '').strip(),
                                'address': row.get('supplier_address', '').strip(),
                                'contact_person': row.get('contact_person', '').strip(),
                            }
                        )
                        
                        # Get or create category
                        category, _ = Category.objects.get_or_create(
                            name=row['category_name'].strip(),
                            defaults={
                                'head_email': row.get('category_head_email', '').strip(),
                                'head_name': row.get('category_head_name', '').strip(),
                            }
                        )
                        
                        # Validate prices and stock
                        try:
                            current_price = Decimal(str(row['current_price']).strip())
                            proposed_price = Decimal(str(row['proposed_price']).strip())
                            proposed_stock = int(str(row['proposed_stock']).strip())
                            
                            if current_price <= 0:
                                errors.append(f"Row {row_num}: Current price must be greater than 0")
                                continue
                            if proposed_price <= 0:
                                errors.append(f"Row {row_num}: Proposed price must be greater than 0")
                                continue
                            if proposed_stock < 0:
                                errors.append(f"Row {row_num}: Proposed stock cannot be negative")
                                continue
                                
                        except (ValueError, TypeError, decimal.InvalidOperation):
                            errors.append(f"Row {row_num}: Invalid price or stock values")
                            continue
                        
                        # Check for existing product with same name and supplier
                        product_name = row['product_name'].strip()
                        existing_product = Product.objects.filter(
                            name__iexact=product_name,
                            supplier=supplier
                        ).first()
                        
                        if existing_product:
                            # Update existing product
                            existing_product.category = category
                            existing_product.current_price = current_price
                            existing_product.proposed_price = proposed_price
                            existing_product.proposed_stock = proposed_stock
                            existing_product.unit = unit
                            existing_product.description = row.get('description', '').strip()
                            existing_product.save()
                            updated_count += 1
                        else:
                            # Create new product
                            Product.objects.create(
                                name=product_name,
                                supplier=supplier,
                                category=category,
                                current_price=current_price,
                                proposed_price=proposed_price,
                                proposed_stock=proposed_stock,
                                unit=unit,
                                description=row.get('description', '').strip(),
                            )
                            created_count += 1
                            
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                
                # Show results
                success_msg = f"Successfully processed {created_count + updated_count} products! "
                success_msg += f"({created_count} created, {updated_count} updated)"
                
                if errors:
                    error_msg = f"{success_msg}\n\n{len(errors)} errors occurred:\n" + "\n".join(errors[:10])
                    if len(errors) > 10:
                        error_msg += f"\n... and {len(errors) - 10} more errors"
                    messages.warning(request, error_msg)
                else:
                    messages.success(request, success_msg)
                    
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    else:
        form = BulkUploadForm()
    
    return render(request, 'po_system/bulk_upload.html', {'form': form})

@login_required
def purchase_orders(request):
    """View and filter purchase orders"""
    # Get filter parameters
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    supplier_id = request.GET.get('supplier', '')
    date_range = request.GET.get('date_range', '')
    
    # Base queryset
    purchase_orders = PurchaseOrder.objects.select_related('supplier', 'created_by').order_by('-created_at')
    
    # Apply filters
    if query:
        purchase_orders = purchase_orders.filter(po_number__icontains=query)
    
    if status:
        purchase_orders = purchase_orders.filter(status=status)
    
    if supplier_id:
        try:
            supplier_id = int(supplier_id)
            purchase_orders = purchase_orders.filter(supplier_id=supplier_id)
        except ValueError:
            pass
    
    if date_range:
        today = timezone.now().date()
        if date_range == 'today':
            purchase_orders = purchase_orders.filter(created_at__date=today)
        elif date_range == 'week':
            start_of_week = today - timedelta(days=today.weekday())
            purchase_orders = purchase_orders.filter(created_at__date__gte=start_of_week)
        elif date_range == 'month':
            purchase_orders = purchase_orders.filter(created_at__date__year=today.year, created_at__date__month=today.month)
        elif date_range == 'quarter':
            current_quarter = ((today.month - 1) // 3) + 1
            start_month = (current_quarter - 1) * 3 + 1
            end_month = current_quarter * 3
            purchase_orders = purchase_orders.filter(
                created_at__date__year=today.year,
                created_at__date__month__gte=start_month,
                created_at__date__month__lte=end_month
            )
    
    # Pagination
    paginator = Paginator(purchase_orders, 10)
    page = request.GET.get('page', 1)
    purchase_orders_page = paginator.get_page(page)
    
    # Get all suppliers for the filter dropdown
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    
    context = {
        'purchase_orders': purchase_orders_page,
        'suppliers': suppliers,
        'query': query,
        'status': status,
        'supplier_id': supplier_id,
        'date_range': date_range,
    }
    
    return render(request, 'po_system/purchase_orders.html', context)

@login_required
def po_detail(request, po_id):
    """Get purchase order details"""
    po = get_object_or_404(PurchaseOrder.objects.select_related('supplier', 'created_by').prefetch_related('items__product'), id=po_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': po.id,
            'po_number': po.po_number,
            'created_at': po.created_at.isoformat(),
            'status': po.status,
            'created_by': po.created_by.get_full_name() or po.created_by.username,
            'total_amount': float(po.total_amount),
            'supplier': {
                'id': po.supplier.id,
                'name': po.supplier.name,
                'contact_person': po.supplier.contact_person,
                'email': po.supplier.email,
                'phone': po.supplier.phone,
            },
            'items': [
                {
                    'id': item.id,
                    'product': {
                        'id': item.product.id,
                        'name': item.product.name,
                        'unit': item.product.unit,
                    },
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price),
                } for item in po.items.all()
            ]
        }
        return JsonResponse(data)
    
    return render(request, 'po_system/po_detail.html', {'po': po})

@login_required
def print_po(request, po_id):
    """Generate printable version of purchase order"""
    po = get_object_or_404(PurchaseOrder.objects.select_related('supplier', 'created_by').prefetch_related('items__product'), id=po_id)
    
    context = {
        'po': po,
        'items': po.items.all(),
        'company_name': 'Your Company Name',
        'company_email': 'info@yourcompany.com',
        'company_phone': '+1 (555) 123-4567',
        'po_department_email': 'purchasing@yourcompany.com',
    }
    
    html_content = render_to_string('po_system/print_po.html', context)
    return HttpResponse(html_content)

@login_required
@csrf_exempt
def cancel_po(request, po_id):
    """Cancel purchase order"""
    if request.method == 'POST':
        try:
            po = get_object_or_404(PurchaseOrder, id=po_id)
            
            # Only allow cancelling draft or sent POs
            if po.status not in ['draft', 'sent']:
                return JsonResponse({'success': False, 'error': f'Cannot cancel a purchase order with status: {po.get_status_display()}'})
            
            # Update status
            po.status = 'cancelled'
            po.save()
            
            return JsonResponse({'success': True, 'message': f'Purchase Order {po.po_number} cancelled successfully!'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# Supplier Management Views
@login_required
def supplier_list(request):
    """List all suppliers with search and filter options"""
    query = request.GET.get('q', '')
    is_active = request.GET.get('is_active', 'all')
    
    suppliers = Supplier.objects.all().order_by('name')
    
    # Apply filters
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) | 
            Q(contact_person__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )
    
    if is_active == 'active':
        suppliers = suppliers.filter(is_active=True)
    elif is_active == 'inactive':
        suppliers = suppliers.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(suppliers, 10)
    page = request.GET.get('page', 1)
    suppliers_page = paginator.get_page(page)
    
    context = {
        'suppliers': suppliers_page,
        'query': query,
        'is_active': is_active,
        'total_count': suppliers.count(),
        'active_count': suppliers.filter(is_active=True).count(),
        'inactive_count': suppliers.filter(is_active=False).count(),
    }
    
    return render(request, 'po_system/supplier_list.html', context)

@login_required
def supplier_create(request):
    """Create a new supplier"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            
            # Handle AJAX requests for quick add
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'supplier': {
                        'id': supplier.id,
                        'name': supplier.name
                    }
                })
            
            messages.success(request, f'Supplier "{supplier.name}" created successfully!')
            return redirect('po_system:supplier_list')
        else:
            # Handle AJAX errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Please check the form data and try again.'
                })
    else:
        form = SupplierForm()
    
    return render(request, 'po_system/supplier_form.html', {
        'form': form,
        'title': 'Add New Supplier',
        'submit_text': 'Create Supplier'
    })

@login_required
def supplier_edit(request, supplier_id):
    """Edit an existing supplier"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier "{supplier.name}" updated successfully!')
            return redirect('po_system:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'po_system/supplier_form.html', {
        'form': form,
        'supplier': supplier,
        'title': f'Edit Supplier: {supplier.name}',
        'submit_text': 'Update Supplier'
    })

@login_required
def supplier_delete(request, supplier_id):
    """Delete a supplier (soft delete by setting is_active=False)"""
    supplier = get_object_or_404(Supplier, id=supplier_id)
    
    if request.method == 'POST':
        # Check if the supplier has associated products
        product_count = supplier.products.count()
        
        if product_count > 0:
            # Soft delete by setting is_active=False
            supplier.is_active = False
            supplier.save()
            messages.success(request, f'Supplier "{supplier.name}" has been deactivated. {product_count} associated products were also deactivated.')
            
            # Also deactivate all associated products
            supplier.products.update(is_active=False)
        else:
            # Hard delete if no associated products
            supplier_name = supplier.name
            supplier.delete()
            messages.success(request, f'Supplier "{supplier_name}" has been permanently deleted.')
        
        return redirect('po_system:supplier_list')
    
    return render(request, 'po_system/supplier_confirm_delete.html', {
        'supplier': supplier,
        'product_count': supplier.products.count()
    })

# Category Management Views
@login_required
def category_list(request):
    """List all product categories"""
    query = request.GET.get('q', '')
    
    categories = Category.objects.all().order_by('name')
    
    # Apply search filter
    if query:
        categories = categories.filter(name__icontains=query)
    
    # Pagination
    paginator = Paginator(categories, 10)
    page = request.GET.get('page', 1)
    categories_page = paginator.get_page(page)
    
    context = {
        'categories': categories_page,
        'query': query,
        'total_count': categories.count()
    }
    
    return render(request, 'po_system/category_list.html', context)

@login_required
def category_create(request):
    """Create a new product category"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            
            # Handle AJAX requests for quick add
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'category': {
                        'id': category.id,
                        'name': category.name
                    }
                })
            
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('po_system:category_list')
        else:
            # Handle AJAX errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Please check the form data and try again.'
                })
    else:
        form = CategoryForm()
    
    return render(request, 'po_system/category_form.html', {
        'form': form,
        'title': 'Add New Category',
        'submit_text': 'Create Category'
    })

@login_required
def category_edit(request, category_id):
    """Edit an existing product category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('po_system:category_list')
    else:
        form = CategoryForm(instance=category)
    
    return render(request, 'po_system/category_form.html', {
        'form': form,
        'category': category,
        'title': f'Edit Category: {category.name}',
        'submit_text': 'Update Category'
    })

@login_required
def category_delete(request, category_id):
    """Delete a product category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        # Check if the category has associated products
        product_count = Product.objects.filter(category=category).count()
        
        if product_count > 0:
            messages.error(request, f'Cannot delete category "{category.name}" because it has {product_count} associated products.')
            return redirect('po_system:category_list')
        
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" has been deleted.')
        return redirect('po_system:category_list')
    
    return render(request, 'po_system/category_confirm_delete.html', {
        'category': category,
        'product_count': Product.objects.filter(category=category).count()
    })

# Shop Management Views
@login_required
def shop_list(request):
    """List all shops"""
    query = request.GET.get('q', '')
    is_active = request.GET.get('is_active', 'all')
    
    shops = Shop.objects.all().order_by('name')
    
    # Apply filters
    if query:
        shops = shops.filter(
            Q(name__icontains=query) | 
            Q(location__icontains=query) |
            Q(manager_name__icontains=query)
        )
    
    if is_active == 'active':
        shops = shops.filter(is_active=True)
    elif is_active == 'inactive':
        shops = shops.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(shops, 10)
    page = request.GET.get('page', 1)
    shops_page = paginator.get_page(page)
    
    context = {
        'shops': shops_page,
        'query': query,
        'is_active': is_active,
        'total_count': shops.count(),
        'active_count': shops.filter(is_active=True).count(),
        'inactive_count': shops.filter(is_active=False).count(),
    }
    
    return render(request, 'po_system/shop_list.html', context)

@login_required
def shop_create(request):
    """Create a new shop"""
    if request.method == 'POST':
        form = ShopForm(request.POST)
        if form.is_valid():
            shop = form.save()
            messages.success(request, f'Shop "{shop.name}" created successfully!')
            return redirect('po_system:shop_list')
    else:
        form = ShopForm()
    
    return render(request, 'po_system/shop_form.html', {
        'form': form,
        'title': 'Add New Shop',
        'submit_text': 'Create Shop'
    })

@login_required
def shop_edit(request, shop_id):
    """Edit an existing shop"""
    shop = get_object_or_404(Shop, id=shop_id)
    
    if request.method == 'POST':
        form = ShopForm(request.POST, instance=shop)
        if form.is_valid():
            shop = form.save()
            messages.success(request, f'Shop "{shop.name}" updated successfully!')
            return redirect('po_system:shop_list')
    else:
        form = ShopForm(instance=shop)
    
    return render(request, 'po_system/shop_form.html', {
        'form': form,
        'shop': shop,
        'title': f'Edit Shop: {shop.name}',
        'submit_text': 'Update Shop'
    })

@login_required
def shop_delete(request, shop_id):
    """Delete a shop (soft delete by setting is_active=False)"""
    shop = get_object_or_404(Shop, id=shop_id)
    
    if request.method == 'POST':
        # Check if the shop has associated stock entries
        stock_count = ProductStock.objects.filter(shop=shop).count()
        
        if stock_count > 0:
            # Soft delete by setting is_active=False
            shop.is_active = False
            shop.save()
            messages.success(request, f'Shop "{shop.name}" has been deactivated. It has {stock_count} associated stock entries.')
        else:
            # Hard delete if no associated stock entries
            shop_name = shop.name
            shop.delete()
            messages.success(request, f'Shop "{shop_name}" has been permanently deleted.')
        
        return redirect('po_system:shop_list')
    
    return render(request, 'po_system/shop_confirm_delete.html', {
        'shop': shop,
        'stock_count': ProductStock.objects.filter(shop=shop).count()
    })

# Product Management Views
@login_required
def product_list(request):
    """List all products with search and filter options"""
    query = request.GET.get('q', '')
    supplier_id = request.GET.get('supplier', '')
    category_id = request.GET.get('category', '')
    is_active = request.GET.get('is_active', 'all')
    
    products = Product.objects.select_related('supplier', 'category').order_by('name')
    
    # Apply filters
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(supplier__name__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    if supplier_id:
        try:
            supplier_id = int(supplier_id)
            products = products.filter(supplier_id=supplier_id)
        except ValueError:
            pass
    
    if category_id:
        try:
            category_id = int(category_id)
            products = products.filter(category_id=category_id)
        except ValueError:
            pass
    
    if is_active == 'active':
        products = products.filter(is_active=True)
    elif is_active == 'inactive':
        products = products.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(products, 10)
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)
    
    # Get suppliers and categories for filter dropdowns
    suppliers = Supplier.objects.filter(is_active=True).order_by('name')
    categories = Category.objects.all().order_by('name')
    
    context = {
        'products': products_page,
        'suppliers': suppliers,
        'categories': categories,
        'query': query,
        'supplier_id': supplier_id,
        'category_id': category_id,
        'is_active': is_active,
        'total_count': products.count(),
        'active_count': products.filter(is_active=True).count(),
        'inactive_count': products.filter(is_active=False).count(),
    }
    
    return render(request, 'po_system/product_list.html', context)

@login_required
def product_create(request):
    """Create a new product with duplicate detection"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product_name = form.cleaned_data['name']
            supplier = form.cleaned_data['supplier']
            
            # Check if this exact combination already exists
            existing_product = Product.objects.filter(
                name__iexact=product_name,
                supplier=supplier
            ).first()
            
            if existing_product:
                messages.warning(
                    request, 
                    f'Product "{product_name}" already exists for supplier "{supplier.name}". '
                    f'You can edit the existing product instead.'
                )
                return redirect('po_system:product_edit', product_id=existing_product.id)
            
            # Check if product name exists with other suppliers
            other_suppliers = Product.objects.filter(
                name__iexact=product_name
            ).exclude(supplier=supplier).select_related('supplier')
            
            if other_suppliers.exists():
                supplier_names = [p.supplier.name for p in other_suppliers]
                messages.info(
                    request,
                    f'Note: Product "{product_name}" is already available from other suppliers: '
                    f'{", ".join(supplier_names)}. This helps maintain consistency.'
                )
            
            # Save the product
            product = form.save()
            messages.success(request, f'Product "{product.name}" created successfully!')
            
            # Check if user wants to add another product
            if 'add_another' in request.POST:
                return redirect('po_system:product_create')
            else:
                return redirect('po_system:product_list')
        else:
            # Handle form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.title()}: {error}')
    else:
        form = ProductForm()
        
        # Pre-fill from URL parameters if provided
        supplier_id = request.GET.get('supplier')
        category_id = request.GET.get('category')
        
        if supplier_id:
            try:
                form.fields['supplier'].initial = int(supplier_id)
            except (ValueError, TypeError):
                pass
                
        if category_id:
            try:
                form.fields['category'].initial = int(category_id)
            except (ValueError, TypeError):
                pass
    
    return render(request, 'po_system/product_form.html', {
        'form': form,
        'title': 'Add New Product',
        'submit_text': 'Create Product'
    })

@login_required
def product_edit(request, product_id):
    """Edit an existing product with enhanced validation"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product_name = form.cleaned_data['name']
            supplier = form.cleaned_data['supplier']
            
            # Check if this would create a duplicate (excluding current product)
            existing_product = Product.objects.filter(
                name__iexact=product_name,
                supplier=supplier
            ).exclude(id=product.id).first()
            
            if existing_product:
                messages.error(
                    request,
                    f'Product "{product_name}" already exists for supplier "{supplier.name}". '
                    f'Please choose a different name or supplier.'
                )
            else:
                # Save the product
                product = form.save()
                messages.success(request, f'Product "{product.name}" updated successfully!')
                return redirect('po_system:product_list')
        else:
            # Handle form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.title()}: {error}')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'po_system/product_form.html', {
        'form': form,
        'product': product,
        'title': f'Edit Product: {product.name}',
        'submit_text': 'Update Product'
    })

@login_required
def product_delete(request, product_id):
    """Delete a product (soft delete by setting is_active=False)"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        # Check if the product has associated purchase order items
        po_item_count = PurchaseOrderItem.objects.filter(product=product).count()
        
        if po_item_count > 0:
            # Soft delete by setting is_active=False
            product.is_active = False
            product.save()
            messages.success(request, f'Product "{product.name}" has been deactivated. It has {po_item_count} associated purchase order items.')
        else:
            # Hard delete if no associated purchase order items
            product_name = product.name
            product.delete()
            messages.success(request, f'Product "{product_name}" has been permanently deleted.')
        
        return redirect('po_system:product_list')
    
    return render(request, 'po_system/product_confirm_delete.html', {
        'product': product,
        'po_item_count': PurchaseOrderItem.objects.filter(product=product).count()
    })

# Stock Management Views
@login_required
def stock_list(request):
    """List all product stock entries"""
    query = request.GET.get('q', '')
    shop_id = request.GET.get('shop', '')
    
    stocks = ProductStock.objects.select_related('product', 'shop', 'product__supplier').order_by('-updated_at')
    
    # Apply filters
    if query:
        stocks = stocks.filter(
            Q(product__name__icontains=query) | 
            Q(shop__name__icontains=query) |
            Q(product__supplier__name__icontains=query)
        )
    
    if shop_id:
        try:
            shop_id = int(shop_id)
            stocks = stocks.filter(shop_id=shop_id)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(stocks, 10)
    page = request.GET.get('page', 1)
    stocks_page = paginator.get_page(page)
    
    # Get shops for filter dropdown
    shops = Shop.objects.filter(is_active=True).order_by('name')
    
    context = {
        'stocks': stocks_page,
        'shops': shops,
        'query': query,
        'shop_id': shop_id,
        'total_count': stocks.count(),
    }
    
    return render(request, 'po_system/stock_list.html', context)

@login_required
def stock_create(request):
    """Create a new stock entry"""
    if request.method == 'POST':
        form = ProductStockForm(request.POST)
        if form.is_valid():
            # Check if a stock entry already exists for this product and shop
            product = form.cleaned_data['product']
            shop = form.cleaned_data['shop']
            quantity = form.cleaned_data['quantity']
            
            stock, created = ProductStock.objects.update_or_create(
                product=product,
                shop=shop,
                defaults={'quantity': quantity}
            )
            
            if created:
                messages.success(request, f'Stock entry for "{product.name}" at "{shop.name}" created successfully!')
            else:
                messages.success(request, f'Stock entry for "{product.name}" at "{shop.name}" updated successfully!')
            
            return redirect('po_system:stock_list')
    else:
        form = ProductStockForm()
    
    return render(request, 'po_system/stock_form.html', {
        'form': form,
        'title': 'Add New Stock Entry',
        'submit_text': 'Create Stock Entry'
    })

@login_required
def stock_edit(request, stock_id):
    """Edit an existing stock entry"""
    stock = get_object_or_404(ProductStock, id=stock_id)
    
    if request.method == 'POST':
        form = ProductStockForm(request.POST, instance=stock)
        if form.is_valid():
            stock = form.save()
            messages.success(request, f'Stock entry for "{stock.product.name}" at "{stock.shop.name}" updated successfully!')
            return redirect('po_system:stock_list')
    else:
        form = ProductStockForm(instance=stock)
    
    return render(request, 'po_system/stock_form.html', {
        'form': form,
        'stock': stock,
        'title': f'Edit Stock: {stock.product.name} at {stock.shop.name}',
        'submit_text': 'Update Stock'
    })

@login_required
def stock_delete(request, stock_id):
    """Delete a stock entry"""
    stock = get_object_or_404(ProductStock, id=stock_id)
    
    if request.method == 'POST':
        product_name = stock.product.name
        shop_name = stock.shop.name
        stock.delete()
        messages.success(request, f'Stock entry for "{product_name}" at "{shop_name}" has been deleted.')
        return redirect('po_system:stock_list')
    
    return render(request, 'po_system/stock_confirm_delete.html', {
        'stock': stock
    })

@login_required
def create_po(request):
    """Create new purchase order page"""
    query = request.GET.get('q', '')
    suppliers = Supplier.objects.filter(is_active=True)
    
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) | 
            Q(contact_person__icontains=query)
        )
    
    paginator = Paginator(suppliers, 10)
    page = request.GET.get('page', 1)
    suppliers_page = paginator.get_page(page)
    
    # Get counts for stats
    suppliers_count = Supplier.objects.filter(is_active=True).count()
    products_count = Product.objects.filter(is_active=True).count()
    categories_count = Category.objects.count()
    
    context = {
        'suppliers': suppliers_page,
        'query': query,
        'suppliers_count': suppliers_count,
        'products_count': products_count,
        'categories_count': categories_count,
    }
    
    return render(request, 'po_system/create_po.html', context)


@login_required
@csrf_exempt
def confirm_po(request, po_id):
    """Confirm a purchase order"""
    if request.method == 'POST':
        try:
            po = get_object_or_404(PurchaseOrder, id=po_id)
            
            # Only allow confirming sent POs
            if po.status != 'sent':
                return JsonResponse({
                    'success': False, 
                    'error': f'Cannot confirm a purchase order with status: {po.get_status_display()}'
                })
            
            # Update status to confirmed
            po.status = 'confirmed'
            po.save()
            
            return JsonResponse({
                'success': True, 
                'message': f'Purchase Order {po.po_number} confirmed successfully!'
            })
                
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    })


@login_required
@csrf_exempt
def send_purchase_order(request):
    """Enhanced send purchase order via email using enhanced email service"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            supplier_id = data.get('supplier_id')
            selected_products = data.get('products', [])
            email_options = data.get('email_options', {
                'to_supplier': True,
                'to_po_dept': True,
                'to_cat_head': True
            })
            
            supplier = get_object_or_404(Supplier, id=supplier_id)
            
            # Validate that we have products
            if not selected_products:
                return JsonResponse({'success': False, 'error': 'No products selected'})
            
            # Create Purchase Order
            po = PurchaseOrder.objects.create(
                supplier=supplier,
                created_by=request.user,
                status='draft'  # Start as draft, will be updated when email is sent
            )
            
            total_amount = 0
            created_items = []
            
            # Process each selected product
            for product_data in selected_products:
                try:
                    product = get_object_or_404(Product, id=product_data['id'])
                    quantity = int(product_data['quantity'])
                    unit_price = Decimal(str(product_data.get('unit_price', product.proposed_price or product.current_price)))
                    
                    # Validate input
                    if quantity <= 0:
                        raise ValueError(f"Invalid quantity for {product.name}")
                    if unit_price <= 0:
                        raise ValueError(f"Invalid price for {product.name}")
                    
                    # Create PO item
                    po_item = PurchaseOrderItem.objects.create(
                        purchase_order=po,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=quantity * unit_price
                    )
                    
                    total_amount += po_item.total_price
                    created_items.append(po_item)
                    
                except (ValueError, TypeError, Product.DoesNotExist) as e:
                    # If any product fails, delete the PO and return error
                    po.delete()
                    return JsonResponse({
                        'success': False, 
                        'error': f'Error processing product: {str(e)}'
                    })
            
            # Update PO total amount
            po.total_amount = total_amount
            po.save()
            
            # Send email using our enhanced email service
            success, message = email_service.send_po_email(po, email_options)
            
            if success:
                return JsonResponse({
                    'success': True, 
                    'po_number': po.po_number,
                    'message': message,
                    'total_amount': float(total_amount),
                    'items_count': len(created_items)
                })
            else:
                # Even if email fails, PO is created
                return JsonResponse({
                    'success': True, 
                    'po_number': po.po_number,
                    'warning': f'PO created but email failed: {message}',
                    'total_amount': float(total_amount),
                    'items_count': len(created_items)
                })
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@csrf_exempt
def send_po_email_view(request, po_id):
    """Send purchase order email using enhanced email service"""
    if request.method == 'POST':
        try:
            po = get_object_or_404(PurchaseOrder, id=po_id)
            
            # Don't allow sending cancelled POs
            if po.status == 'cancelled':
                return JsonResponse({
                    'success': False, 
                    'error': 'Cannot send a cancelled purchase order'
                })
            
            # Get email options from request
            email_options = {
                'to_supplier': True,
                'to_po_dept': True,
                'to_cat_head': True
            }
            
            # If specific options are provided in the request
            if request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                    email_options.update(data.get('email_options', {}))
                except:
                    pass  # Use defaults if JSON parsing fails
            
            # Send email using enhanced email service
            success, message = email_service.send_po_email(po, email_options)
            
            if success:
                return JsonResponse({
                    'success': True, 
                    'message': message
                })
            else:
                return JsonResponse({
                    'success': False, 
                    'error': message
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Unexpected error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False, 
        'error': 'Invalid request method'
    })

@login_required
def test_email_view(request):
    """Test email functionality"""
    if request.method == 'POST':
        try:
            recipient_email = request.POST.get('email')
            method = request.POST.get('method', 'auto')  # auto, smtp, or api
            
            if not recipient_email:
                messages.error(request, 'Please provide an email address')
                return redirect('po_system:dashboard')
            
            # Send test email
            success, message = email_service.send_test_email(recipient_email, method)
            
            if success:
                messages.success(request, f'Test email sent successfully! {message}')
            else:
                messages.error(request, f'Test email failed: {message}')
                
        except Exception as e:
            messages.error(request, f'Error sending test email: {str(e)}')
    
    return redirect('po_system:dashboard')

@login_required
def email_settings_view(request):
    """View email settings and test functionality"""
    context = {
        'smtp_available': email_service.smtp_available,
        'api_available': email_service.api_available,
        'email_host': getattr(settings, 'EMAIL_HOST', 'Not configured'),
        'email_port': getattr(settings, 'EMAIL_PORT', 'Not configured'),
        'email_use_tls': getattr(settings, 'EMAIL_USE_TLS', False),
        'email_use_ssl': getattr(settings, 'EMAIL_USE_SSL', False),
        'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured'),
        'zepto_from_email': getattr(settings, 'ZEPTO_FROM_EMAIL', 'Not configured'),
        'company_name': getattr(settings, 'COMPANY_NAME', 'Not configured'),
    }
    
    return render(request, 'po_system/email_settings.html', context)

@login_required
def product_suggestions_api(request):
    """Enhanced API endpoint for product name suggestions with better search"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'products': []})
    
    try:
        # Enhanced search for products with better matching
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        ).select_related('category', 'supplier').distinct()[:20]
        
        # Group products by name to show supplier variations
        product_groups = {}
        for product in products:
            name = product.name.lower().strip()
            if name not in product_groups:
                product_groups[name] = {
                    'name': product.name,
                    'category': product.category.name,
                    'unit': product.unit,
                    'suppliers': [],
                    'price_range': {'min': float(product.current_price), 'max': float(product.current_price)},
                    'avg_price': float(product.current_price),
                    'total_suppliers': 0
                }
            
            # Add supplier info
            product_groups[name]['suppliers'].append({
                'name': product.supplier.name,
                'price': float(product.current_price),
                'proposed_price': float(product.proposed_price) if product.proposed_price else None,
                'stock': product.current_stock
            })
            
            # Update price range
            current_price = float(product.current_price)
            if current_price < product_groups[name]['price_range']['min']:
                product_groups[name]['price_range']['min'] = current_price
            if current_price > product_groups[name]['price_range']['max']:
                product_groups[name]['price_range']['max'] = current_price
        
        # Format response with enhanced data
        suggestions = []
        for name, data in product_groups.items():
            data['total_suppliers'] = len(data['suppliers'])
            # Calculate average price
            total_price = sum(s['price'] for s in data['suppliers'])
            data['avg_price'] = total_price / len(data['suppliers'])
            
            # Format supplier names for display
            supplier_names = [s['name'] for s in data['suppliers'][:3]]
            if len(data['suppliers']) > 3:
                data['suppliers_display'] = ', '.join(supplier_names) + f' and {len(data["suppliers"]) - 3} more'
            else:
                data['suppliers_display'] = ', '.join(supplier_names)
                
            suggestions.append(data)
        
        # Sort by relevance (exact matches first, then by supplier count)
        suggestions.sort(key=lambda x: (
            0 if query.lower() in x['name'].lower() else 1,
            -x['total_suppliers'],
            x['name'].lower()
        ))
        
        return JsonResponse({'products': suggestions[:15]})
        
    except Exception as e:
        logger.error(f"Error in product_suggestions_api: {e}")
        return JsonResponse({'products': [], 'error': str(e)})

@login_required 
def check_product_duplicate(request):
    """Check if product already exists with this supplier"""
    product_name = request.GET.get('name', '').strip()
    supplier_id = request.GET.get('supplier_id', '')
    
    if not product_name or not supplier_id:
        return JsonResponse({'exists': False})
    
    try:
        supplier_id = int(supplier_id)
        exists = Product.objects.filter(
            name__iexact=product_name,
            supplier_id=supplier_id
        ).exists()
        
        return JsonResponse({'exists': exists})
    except (ValueError, TypeError):
        return JsonResponse({'exists': False})
    
@login_required
def product_search_api(request):
    """Enhanced API endpoint for product autocomplete search"""
    query = request.GET.get('q', '').strip()
    supplier_id = request.GET.get('supplier_id', '')
    
    if len(query) < 1:
        return JsonResponse({'products': []})
    
    try:
        # Base query
        products_query = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(supplier__name__icontains=query),
            is_active=True
        ).select_related('supplier', 'category')
        
        # Filter by supplier if provided
        if supplier_id:
            try:
                supplier_id = int(supplier_id)
                products_query = products_query.filter(supplier_id=supplier_id)
            except (ValueError, TypeError):
                pass
        
        products = products_query.order_by('name')[:15]
        
        product_data = []
        for product in products:
            product_data.append({
                'id': product.id,
                'name': product.name,
                'description': product.description or f"{product.name} - {product.unit}",
                'supplier': {
                    'id': product.supplier.id,
                    'name': product.supplier.name,
                },
                'category': {
                    'id': product.category.id,
                    'name': product.category.name,
                },
                'unit': product.unit,
                'current_price': float(product.current_price),
                'proposed_price': float(product.proposed_price) if product.proposed_price else float(product.current_price),
                'current_stock': product.current_stock,
                'proposed_stock': product.proposed_stock if product.proposed_stock else 10,
                'total_value': float((product.proposed_price or product.current_price) * (product.proposed_stock or 10)),
                'is_available': product.is_active,
            })
        
        return JsonResponse({
            'products': product_data,
            'total': len(product_data),
            'query': query,
            'supplier_filtered': bool(supplier_id)
        })
        
    except Exception as e:
        logger.error(f"Error in product_search_api: {e}")
        return JsonResponse({
            'products': [], 
            'error': str(e),
            'total': 0,
            'query': query
        })
