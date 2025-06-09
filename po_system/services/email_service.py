# po_system/services/email_service.py

import logging
import json
import requests
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)

class EmailService:
    """
    Email service class that handles both SMTP and API email sending
    """
    
    def __init__(self):
        self.smtp_available = self._check_smtp_config()
        self.api_available = self._check_api_config()
        
    def _check_smtp_config(self) -> bool:
        """Check if SMTP configuration is available"""
        required_settings = [
            'EMAIL_HOST', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL'
        ]
        return all(hasattr(settings, setting) and getattr(settings, setting) 
                  for setting in required_settings)
    
    def _check_api_config(self) -> bool:
        """Check if API configuration is available"""
        return (hasattr(settings, 'ZEPTO_API_KEY') and 
                settings.ZEPTO_API_KEY and 
                hasattr(settings, 'ZEPTO_FROM_EMAIL') and 
                settings.ZEPTO_FROM_EMAIL)
    
    def send_po_email(self, po, email_options: Optional[Dict[str, bool]] = None) -> Tuple[bool, str]:
        """
        Send purchase order email using the best available method
        
        Args:
            po: PurchaseOrder instance
            email_options: Dict with recipient options
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if email_options is None:
            email_options = {
                'to_supplier': True,
                'to_po_dept': True,
                'to_cat_head': True
            }
        
        # Get recipients
        recipients = self._get_recipients(po, email_options)
        if not recipients:
            return False, "No recipients found"
        
        # Try SMTP first, then fall back to API
        if self.smtp_available:
            success, message = self._send_via_smtp(po, recipients)
            if success:
                return True, f"Email sent via SMTP to {len(recipients)} recipients"
            else:
                logger.warning(f"SMTP failed for PO {po.po_number}: {message}")
        
        if self.api_available:
            success, message = self._send_via_api(po, recipients)
            if success:
                return True, f"Email sent via API to {len(recipients)} recipients"
            else:
                logger.error(f"API also failed for PO {po.po_number}: {message}")
                return False, f"Both SMTP and API failed. Last error: {message}"
        
        return False, "No email method available"
    
    def _get_recipients(self, po, email_options: Dict[str, bool]) -> List[Dict[str, str]]:
        """Get list of email recipients based on options"""
        recipients = []
        
        # Supplier email
        if email_options.get('to_supplier', True) and po.supplier.email:
            recipients.append({
                'email': po.supplier.email,
                'name': po.supplier.contact_person or po.supplier.name
            })
        
        # PO Department email
        if email_options.get('to_po_dept', True):
            po_email = getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL)
            recipients.append({
                'email': po_email,
                'name': 'Purchase Department'
            })
        
        # Category head emails
        if email_options.get('to_cat_head', True):
            category_heads = {}
            for item in po.items.all():
                if item.product.category.head_email:
                    category_heads[item.product.category.head_email] = item.product.category.head_name
            
            for email, name in category_heads.items():
                recipients.append({
                    'email': email,
                    'name': name or 'Category Head'
                })
        
        # Remove duplicates
        seen = set()
        unique_recipients = []
        for recipient in recipients:
            if recipient['email'] not in seen:
                seen.add(recipient['email'])
                unique_recipients.append(recipient)
        
        return unique_recipients
    
    def _send_via_smtp(self, po, recipients: List[Dict[str, str]]) -> Tuple[bool, str]:
        """Send email via SMTP"""
        try:
            # Prepare email content
            subject = f'Purchase Order {po.po_number} - {settings.COMPANY_NAME}'
            
            # HTML content
            html_content = render_to_string('emails/purchase_order.html', {
                'po': po,
                'items': po.items.all(),
                'company_name': settings.COMPANY_NAME,
                'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
                'company_email': getattr(settings, 'COMPANY_EMAIL', settings.DEFAULT_FROM_EMAIL),
                'po_department_email': getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL),
            })
            
            # Text content
            text_content = self._generate_text_content(po)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[r['email'] for r in recipients],
                reply_to=[getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL)]
            )
            
            # Add HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            # Update PO status
            self._update_po_status(po)
            
            logger.info(f"PO {po.po_number} sent via SMTP to {[r['email'] for r in recipients]}")
            return True, "Email sent successfully via SMTP"
            
        except Exception as e:
            logger.error(f"SMTP sending failed for PO {po.po_number}: {str(e)}")
            return False, str(e)
    
    def _send_via_api(self, po, recipients: List[Dict[str, str]]) -> Tuple[bool, str]:
        """Send email via Zepto Mail API"""
        try:
            # Prepare recipients for API
            api_recipients = []
            for recipient in recipients:
                api_recipients.append({
                    'email_address': {
                        'address': recipient['email'],
                        'name': recipient['name']
                    }
                })
            
            # Prepare email content
            subject = f'Purchase Order {po.po_number} - {settings.COMPANY_NAME}'
            
            # HTML content
            html_content = render_to_string('emails/purchase_order.html', {
                'po': po,
                'items': po.items.all(),
                'company_name': settings.COMPANY_NAME,
                'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
                'company_email': getattr(settings, 'COMPANY_EMAIL', settings.DEFAULT_FROM_EMAIL),
                'po_department_email': getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL),
            })
            
            # Text content
            text_content = self._generate_text_content(po)
            
            # Prepare API payload
            payload = {
                'bounce_address': settings.ZEPTO_FROM_EMAIL,
                'from': {
                    'address': settings.ZEPTO_FROM_EMAIL,
                    'name': getattr(settings, 'ZEPTO_FROM_NAME', settings.COMPANY_NAME),
                },
                'to': api_recipients,
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
                # Update PO status
                self._update_po_status(po)
                
                logger.info(f"PO {po.po_number} sent via API to {[r['email'] for r in recipients]}")
                return True, "Email sent successfully via API"
            else:
                error_msg = f"API returned {response.status_code}: {response.text}"
                logger.error(f"API sending failed for PO {po.po_number}: {error_msg}")
                return False, error_msg
                
        except Exception as e:
            logger.error(f"API sending failed for PO {po.po_number}: {str(e)}")
            return False, str(e)
    
    def _generate_text_content(self, po) -> str:
        """Generate plain text email content"""
        text_content = f"""
Purchase Order: {po.po_number}
Supplier: {po.supplier.name}
Contact: {po.supplier.contact_person}
Date: {po.created_at.strftime('%B %d, %Y')}

Order Items:
"""
        for item in po.items.all():
            text_content += f"- {item.product.name}: {item.quantity} {item.product.unit} @ ₹{item.unit_price} = ₹{item.total_price}\n"
        
        text_content += f"""
Total Amount: ₹{po.total_amount}

Supplier Details:
Name: {po.supplier.name}
Contact Person: {po.supplier.contact_person}
Email: {po.supplier.email}
Phone: {po.supplier.phone}
Address: {po.supplier.address}

Please confirm receipt of this purchase order and provide delivery timeline.

For any queries, please contact our purchase department at {getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.DEFAULT_FROM_EMAIL)}

Best regards,
{settings.COMPANY_NAME}
{getattr(settings, 'COMPANY_PHONE', '')}
        """
        return text_content.strip()
    
    def _update_po_status(self, po):
        """Update PO status after successful email sending"""
        if po.status == 'draft':
            po.status = 'sent'
            po.sent_at = timezone.now()
            po.save()
    
    def send_test_email(self, recipient_email: str, method: str = 'auto') -> Tuple[bool, str]:
        """
        Send a test email
        
        Args:
            recipient_email: Email address to send test to
            method: 'smtp', 'api', or 'auto'
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        subject = f'Test Email from {settings.COMPANY_NAME} PO System'
        
        html_content = f"""
        <html>
        <body>
            <h2>Test Email from {settings.COMPANY_NAME}</h2>
            <p>This is a test email from your Purchase Order Management System.</p>
            <p>If you received this email, your email configuration is working correctly!</p>
            
            <h3>System Information:</h3>
            <ul>
                <li>Company: {settings.COMPANY_NAME}</li>
                <li>From Email: {settings.DEFAULT_FROM_EMAIL}</li>
                <li>SMTP Available: {'Yes' if self.smtp_available else 'No'}</li>
                <li>API Available: {'Yes' if self.api_available else 'No'}</li>
                <li>Test Time: {timezone.now()}</li>
            </ul>
            
            <p>Best regards,<br>
            <strong>{settings.COMPANY_NAME} IT Team</strong></p>
        </body>
        </html>
        """
        
        text_content = f"""
Test Email from {settings.COMPANY_NAME}

This is a test email from your Purchase Order Management System.

If you received this email, your email configuration is working correctly!

System Information:
- Company: {settings.COMPANY_NAME}
- From Email: {settings.DEFAULT_FROM_EMAIL}
- SMTP Available: {'Yes' if self.smtp_available else 'No'}
- API Available: {'Yes' if self.api_available else 'No'}
- Test Time: {timezone.now()}

Best regards,
{settings.COMPANY_NAME} IT Team
        """
        
        recipients = [{'email': recipient_email, 'name': 'Test User'}]
        
        if method == 'smtp' or (method == 'auto' and self.smtp_available):
            try:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient_email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                return True, "Test email sent successfully via SMTP"
            except Exception as e:
                if method == 'smtp':
                    return False, f"SMTP test failed: {str(e)}"
                # Continue to API if auto mode
        
        if method == 'api' or (method == 'auto' and self.api_available):
            try:
                payload = {
                    'bounce_address': settings.ZEPTO_FROM_EMAIL,
                    'from': {
                        'address': settings.ZEPTO_FROM_EMAIL,
                        'name': getattr(settings, 'ZEPTO_FROM_NAME', settings.COMPANY_NAME),
                    },
                    'to': [{
                        'email_address': {
                            'address': recipient_email,
                            'name': 'Test User'
                        }
                    }],
                    'subject': subject,
                    'htmlbody': html_content,
                    'textbody': text_content,
                }
                
                headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'Authorization': f'Zoho-enczapikey {settings.ZEPTO_API_KEY}',
                }
                
                response = requests.post(
                    'https://api.zeptomail.in/v1.1/email',
                    data=json.dumps(payload),
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    return True, "Test email sent successfully via API"
                else:
                    return False, f"API test failed: {response.status_code} - {response.text}"
                    
            except Exception as e:
                return False, f"API test failed: {str(e)}"
        
        return False, "No email method available"

# Create global instance
email_service = EmailService()