# po_system/utils.py

import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.mail.backends.smtp import EmailBackend
import json
import logging
from typing import Dict, List, Tuple

# Set up logging
logger = logging.getLogger(__name__)

def send_po_email(po, email_options: Dict[str, bool] = None) -> bool:
    """
    Send PO email using Django SMTP with Zepto Mail
    
    Args:
        po: PurchaseOrder instance
        email_options: Dict with email recipient options
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        if email_options is None:
            email_options = {
                'to_supplier': True,
                'to_po_dept': True,
                'to_cat_head': True
            }

        # Prepare email recipients
        recipients = []
        
        if email_options.get('to_supplier', True):
            recipients.append(po.supplier.email)
        
        if email_options.get('to_po_dept', True):
            recipients.append(getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL))
        
        if email_options.get('to_cat_head', True):
            # Get category head emails from PO items
            category_heads = set()
            for item in po.items.all():
                if item.product.category.head_email:
                    category_heads.add(item.product.category.head_email)
            recipients.extend(list(category_heads))
        
        # Remove duplicates
        recipients = list(set(recipients))
        
        if not recipients:
            logger.error(f"No recipients found for PO {po.po_number}")
            return False

        # Email subject
        subject = f'Purchase Order {po.po_number} - {settings.COMPANY_NAME}'
        
        # Email content (HTML)
        html_content = render_to_string('emails/purchase_order.html', {
            'po': po,
            'items': po.items.all(),
            'company_name': settings.COMPANY_NAME,
            'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
            'company_email': getattr(settings, 'COMPANY_EMAIL', settings.DEFAULT_FROM_EMAIL),
            'po_department_email': getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL),
        })
        
        # Plain text version
        text_content = f"""
Purchase Order: {po.po_number}
Supplier: {po.supplier.name}
Date: {po.created_at.strftime('%Y-%m-%d')}
Total Amount: ₹{po.total_amount}

Items:
"""
        for item in po.items.all():
            text_content += f"- {item.product.name}: {item.quantity} {item.product.unit} @ ₹{item.unit_price} = ₹{item.total_price}\n"
        
        text_content += f"""
Total: ₹{po.total_amount}

Please confirm receipt of this purchase order.

Best regards,
{settings.COMPANY_NAME}
{getattr(settings, 'COMPANY_PHONE', '')}
{getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL)}
        """
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
            reply_to=[getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL)]
        )
        
        # Add HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        # Update PO status if it was draft
        if po.status == 'draft':
            po.status = 'sent'
            po.sent_at = timezone.now()
            po.save()
        
        logger.info(f"PO email sent successfully to {', '.join(recipients)} for PO {po.po_number}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send PO email for {po.po_number}: {str(e)}")
        return False

def test_smtp_connection() -> Tuple[bool, str]:
    """
    Test SMTP connection with current settings
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        # Test basic SMTP connection
        backend = EmailBackend(
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
            use_ssl=settings.EMAIL_USE_SSL,
        )
        
        connection = backend.open()
        if connection:
            backend.close()
            return True, "SMTP connection successful"
        else:
            return False, "Failed to establish SMTP connection"
            
    except Exception as e:
        return False, f"SMTP connection failed: {str(e)}"

def send_test_email(recipient_email: str) -> Tuple[bool, str]:
    """
    Send a test email to verify SMTP configuration
    
    Args:
        recipient_email: Email address to send test email to
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    try:
        subject = f'Test Email from {settings.COMPANY_NAME} PO System'
        message = f"""
This is a test email from the {settings.COMPANY_NAME} Purchase Order Management System.

If you received this email, the SMTP configuration is working correctly.

Email Settings:
- SMTP Host: {settings.EMAIL_HOST}
- SMTP Port: {settings.EMAIL_PORT}
- Use TLS: {settings.EMAIL_USE_TLS}
- From Email: {settings.DEFAULT_FROM_EMAIL}

Time: {timezone.now()}

Best regards,
{settings.COMPANY_NAME} IT Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        return True, f"Test email sent successfully to {recipient_email}"
        
    except Exception as e:
        return False, f"Failed to send test email: {str(e)}"

def test_zepto_mail_api() -> Dict[str, any]:
    """
    Test Zepto Mail API connection (alternative to SMTP)
    
    Returns:
        dict: Test results with status and message
    """
    try:
        # Check if API key is configured
        if not hasattr(settings, 'ZEPTO_API_KEY') or not settings.ZEPTO_API_KEY:
            return {
                'success': False,
                'message': 'ZEPTO_API_KEY not configured in settings'
            }
        
        # Prepare headers
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Zoho-enczapikey {settings.ZEPTO_API_KEY}',
        }
        
        # Test payload (this won't actually send)
        test_payload = {
            'bounce_address': settings.ZEPTO_FROM_EMAIL,
            'from': {
                'address': settings.ZEPTO_FROM_EMAIL,
                'name': settings.ZEPTO_FROM_NAME,
            },
            'to': [
                {
                    'email_address': {
                        'address': 'test@example.com',
                        'name': 'Test User',
                    }
                }
            ],
            'subject': 'Test Connection',
            'htmlbody': '<p>This is a test message</p>',
            'textbody': 'This is a test message',
        }
        
        # Make API request
        response = requests.post(
            'https://api.zeptomail.in/v1.1/email',
            data=json.dumps(test_payload),
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'Zepto Mail API connection successful',
                'response': response.json()
            }
        elif response.status_code == 401:
            return {
                'success': False,
                'message': 'Invalid API key - please check your ZEPTO_API_KEY'
            }
        else:
            return {
                'success': False,
                'message': f'API error: {response.status_code} - {response.text}'
            }
            
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'message': f'Network error: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Unexpected error: {str(e)}'
        }

def send_po_email_via_api(po, email_options: Dict[str, bool] = None) -> bool:
    """
    Send PO email using Zepto Mail API (alternative to SMTP)
    
    Args:
        po: PurchaseOrder instance
        email_options: Dict with email recipient options
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        if email_options is None:
            email_options = {
                'to_supplier': True,
                'to_po_dept': True,
                'to_cat_head': True
            }

        # Prepare email recipients
        recipients = []
        
        if email_options.get('to_supplier', True):
            recipients.append({
                'email_address': {
                    'address': po.supplier.email,
                    'name': po.supplier.contact_person
                }
            })
        
        if email_options.get('to_po_dept', True):
            recipients.append({
                'email_address': {
                    'address': getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL),
                    'name': 'Purchase Department'
                }
            })
        
        if email_options.get('to_cat_head', True):
            # Get category head emails from PO items
            for item in po.items.all():
                if item.product.category.head_email:
                    recipients.append({
                        'email_address': {
                            'address': item.product.category.head_email,
                            'name': item.product.category.head_name
                        }
                    })
        
        if not recipients:
            logger.error(f"No recipients found for PO {po.po_number}")
            return False

        # Email subject
        subject = f'Purchase Order {po.po_number} - {settings.COMPANY_NAME}'
        
        # Email content (HTML)
        html_content = render_to_string('emails/purchase_order.html', {
            'po': po,
            'items': po.items.all(),
            'company_name': settings.COMPANY_NAME,
            'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
            'company_email': getattr(settings, 'COMPANY_EMAIL', settings.DEFAULT_FROM_EMAIL),
            'po_department_email': getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL),
        })
        
        # Plain text content
        text_content = f"""Purchase Order: {po.po_number}
Supplier: {po.supplier.name}
Date: {po.created_at.strftime('%Y-%m-%d')}
Total Amount: ₹{po.total_amount}

Please review the attached purchase order details.

Best regards,
{settings.COMPANY_NAME}"""

        # Prepare API payload
        payload = {
            'bounce_address': settings.ZEPTO_FROM_EMAIL,
            'from': {
                'address': settings.ZEPTO_FROM_EMAIL,
                'name': settings.ZEPTO_FROM_NAME,
            },
            'to': recipients,
            'subject': subject,
            'htmlbody': html_content,
            'textbody': text_content,
        }
        
        # Prepare headers
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Zoho-enczapikey {settings.ZEPTO_API_KEY}',
        }
        
        # Send email via API
        response = requests.post(
            'https://api.zeptomail.in/v1.1/email',
            data=json.dumps(payload),
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            # Update PO status if it was draft
            if po.status == 'draft':
                po.status = 'sent'
                po.sent_at = timezone.now()
                po.save()
            
            logger.info(f"PO email sent successfully via API for PO {po.po_number}")
            return True
        else:
            logger.error(f"Failed to send PO email via API for {po.po_number}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send PO email via API for {po.po_number}: {str(e)}")
        return False

def validate_email_settings() -> Dict[str, any]:
    """
    Validate email settings configuration
    
    Returns:
        dict: Validation results
    """
    issues = []
    
    # Check SMTP settings
    if not hasattr(settings, 'EMAIL_HOST') or not settings.EMAIL_HOST:
        issues.append("EMAIL_HOST not configured")
    
    if not hasattr(settings, 'EMAIL_HOST_USER') or not settings.EMAIL_HOST_USER:
        issues.append("EMAIL_HOST_USER not configured")
    
    if not hasattr(settings, 'EMAIL_HOST_PASSWORD') or not settings.EMAIL_HOST_PASSWORD:
        issues.append("EMAIL_HOST_PASSWORD not configured")
    
    if not hasattr(settings, 'DEFAULT_FROM_EMAIL') or not settings.DEFAULT_FROM_EMAIL:
        issues.append("DEFAULT_FROM_EMAIL not configured")
    
    # Check Zepto Mail API settings
    if not hasattr(settings, 'ZEPTO_API_KEY') or not settings.ZEPTO_API_KEY:
        issues.append("ZEPTO_API_KEY not configured (API fallback unavailable)")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'smtp_configured': all([
            hasattr(settings, 'EMAIL_HOST') and settings.EMAIL_HOST,
            hasattr(settings, 'EMAIL_HOST_USER') and settings.EMAIL_HOST_USER,
            hasattr(settings, 'EMAIL_HOST_PASSWORD') and settings.EMAIL_HOST_PASSWORD,
        ]),
        'api_configured': hasattr(settings, 'ZEPTO_API_KEY') and settings.ZEPTO_API_KEY
    }