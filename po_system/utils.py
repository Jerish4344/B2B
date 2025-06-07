import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
import json

def send_po_email(purchase_order, email_options=None):
    """Send purchase order email using Zepto Mail
    
    Args:
        purchase_order: The PurchaseOrder object
        email_options: Dict with keys 'to_supplier', 'to_po_dept', 'to_cat_head'
                      controlling which recipients receive the email
    """
    # Default email options if not provided
    if email_options is None:
        email_options = {
            'to_supplier': True,
            'to_po_dept': True,
            'to_cat_head': True
        }
    
    # Email content
    subject = f"Purchase Order #{purchase_order.po_number}"
    
    # Render email template
    email_content = render_to_string('emails/purchase_order.html', {
        'po': purchase_order,
        'items': purchase_order.items.all(),
        'company_name': 'Your Company Name',
    })
    
    # Recipients
    recipients = []
    
    # Add supplier if requested
    if email_options.get('to_supplier', True):
        recipients.append({
            'email_address': {
                'address': purchase_order.supplier.email,
                'name': purchase_order.supplier.contact_person,
            }
        })
    
    # CC recipients
    cc_recipients = []
    
    # Add PO Department if requested
    if email_options.get('to_po_dept', True) and hasattr(settings, 'PO_DEPARTMENT_EMAIL'):
        cc_recipients.append({
            'email_address': {
                'address': settings.PO_DEPARTMENT_EMAIL,
                'name': 'PO Department',
            }
        })
    
    # Add Category Heads if requested
    if email_options.get('to_cat_head', True):
        for item in purchase_order.items.all():
            cc_recipients.append({
                'email_address': {
                    'address': item.product.category.head_email,
                    'name': item.product.category.head_name,
                }
            })
    
    # Remove duplicates from CC
    seen_emails = set()
    unique_cc = []
    for cc in cc_recipients:
        email = cc['email_address']['address']
        if email not in seen_emails:
            seen_emails.add(email)
            unique_cc.append(cc)
    
    # If no recipients, don't send email
    if not recipients and not unique_cc:
        print("No recipients specified for email")
        return False
    
    # If supplier not included but others are, move first CC to primary recipient
    if not recipients and unique_cc:
        recipients = [unique_cc.pop(0)]
    
    # Zepto Mail API payload
    payload = {
        'from': {
            'address': settings.ZEPTO_FROM_EMAIL,
            'name': settings.ZEPTO_FROM_NAME,
        },
        'to': recipients,
        'cc': unique_cc,
        'subject': subject,
        'htmlbody': email_content,
    }
    
    # API Headers
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'authorization': f'Zoho-enczapikey {settings.ZEPTO_API_KEY}',
    }
    
    try:
        response = requests.post(
            'https://api.zeptomail.in/v1.1/email',
            data=json.dumps(payload),
            headers=headers
        )
        
        if response.status_code == 200:
            purchase_order.sent_at = timezone.now()
            purchase_order.save()
            return True
        else:
            print(f"Email sending failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        return False
