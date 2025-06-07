import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
import json
import logging

# Set up logging
logger = logging.getLogger(__name__)

def send_po_email(po, supplier_email):
    """Send PO email using Django SMTP"""
    try:
        # Email subject
        subject = f'Purchase Order {po.po_number} - {settings.COMPANY_NAME}'
        
        # Email content
        html_content = render_to_string('po_system/email/po_email.html', {
            'po': po,
            'company_name': settings.COMPANY_NAME,
            'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
            'po_department_email': getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL),
        })
        
        # Plain text version
        text_content = f"""
        Purchase Order: {po.po_number}
        Supplier: {po.supplier.name}
        Date: {po.created_at.strftime('%Y-%m-%d')}
        Total Amount: ${po.total_amount}
        
        Please review the attached purchase order.
        
        Best regards,
        {settings.COMPANY_NAME}
        """
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[supplier_email],
            reply_to=[getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL)]
        )
        
        # Add HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"PO email sent successfully to {supplier_email}")
        return True, "Email sent successfully"
        
    except Exception as e:
        logger.error(f"Failed to send PO email: {str(e)}")
        return False, f"Failed to send email: {str(e)}"

def test_zepto_mail_connection():
    """Test Zepto Mail configuration and connectivity
    
    Returns:
        dict: Test results with status and message
    """
    try:
        # Check settings
        if not hasattr(settings, 'ZEPTO_API_KEY') or not settings.ZEPTO_API_KEY:
            return {
                'success': False,
                'message': 'ZEPTO_API_KEY not configured in settings'
            }
        
        if settings.ZEPTO_API_KEY == 'your_zepto_api_key':
            return {
                'success': False,
                'message': 'Please update ZEPTO_API_KEY with your actual API key'
            }
        
        # Test API connection (this is a simple test - Zepto doesn't have a dedicated test endpoint)
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'authorization': f'Zoho-enczapikey {settings.ZEPTO_API_KEY}',
        }
        
        # Simple test payload
        test_payload = {
            'from': {
                'address': settings.ZEPTO_FROM_EMAIL,
                'name': settings.ZEPTO_FROM_NAME,
            },
            'to': [
                {
                    'email_address': {
                        'address': 'test@example.com',  # This won't actually send
                        'name': 'Test User',
                    }
                }
            ],
            'subject': 'Test Connection',
            'textbody': 'This is a test message',
        }
        
        response = requests.post(
            'https://api.zeptomail.in/v1.1/email',
            data=json.dumps(test_payload),
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'Zepto Mail connection successful'
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