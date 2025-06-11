import requests
import json
import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = logging.getLogger(__name__)

class EmailService:
    """Enhanced email service that supports both API and SMTP methods"""
    
    def __init__(self):
        self.api_available = self._check_api_config()
        self.smtp_available = self._check_smtp_config()
        
    def _check_api_config(self):
        """Check if Zepto Mail API is configured"""
        return (
            hasattr(settings, 'ZEPTO_API_KEY') and 
            hasattr(settings, 'ZEPTO_FROM_EMAIL') and
            settings.ZEPTO_API_KEY and 
            settings.ZEPTO_FROM_EMAIL
        )
    
    def _check_smtp_config(self):
        """Check if SMTP is configured"""
        return (
            hasattr(settings, 'EMAIL_HOST') and 
            hasattr(settings, 'EMAIL_HOST_USER') and
            settings.EMAIL_HOST and 
            settings.EMAIL_HOST_USER
        )
    
    def send_via_api(self, from_email, from_name, to_emails, subject, html_body, text_body=None):
        """Send email using Zepto Mail API"""
        try:
            url = "https://api.zeptomail.in/v1.1/email"
            
            # Prepare recipients
            recipients = []
            for email_data in to_emails:
                if isinstance(email_data, str):
                    recipients.append({
                        "email_address": {
                            "address": email_data
                        }
                    })
                else:
                    recipients.append({
                        "email_address": {
                            "address": email_data.get('email'),
                            "name": email_data.get('name', '')
                        }
                    })
            
            payload = {
                "from": {
                    "address": from_email,
                    "name": from_name
                },
                "to": recipients,
                "subject": subject,
                "htmlbody": html_body
            }
            
            if text_body:
                payload["textbody"] = text_body
            
            headers = {
                'accept': "application/json",
                'content-type': "application/json",
                'authorization': f"Zoho-enczapikey {settings.ZEPTO_API_KEY}",
            }
            
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=30)
            
            if response.status_code in [200, 201]:
                logger.info(f"Email sent successfully via API to {len(to_emails)} recipients")
                return True, "Email sent successfully via API"
            else:
                logger.error(f"API email failed. Status: {response.status_code}, Response: {response.text}")
                return False, f"API failed: {response.text}"
                
        except Exception as e:
            logger.error(f"Exception in API email: {str(e)}")
            return False, f"API error: {str(e)}"
    
    def send_via_smtp(self, from_email, to_emails, subject, html_body, text_body=None):
        """Send email using Django SMTP backend"""
        try:
            # Prepare recipient list
            recipient_list = []
            for email_data in to_emails:
                if isinstance(email_data, str):
                    recipient_list.append(email_data)
                else:
                    recipient_list.append(email_data.get('email'))
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_body or "Please view this email in HTML format.",
                from_email=from_email,
                to=recipient_list
            )
            
            # Add HTML version
            email.attach_alternative(html_body, "text/html")
            
            # Send email
            email.send()
            
            logger.info(f"Email sent successfully via SMTP to {len(recipient_list)} recipients")
            return True, "Email sent successfully via SMTP"
            
        except Exception as e:
            logger.error(f"SMTP email failed: {str(e)}")
            return False, f"SMTP error: {str(e)}"
    
    def send_po_email(self, po, email_options=None):
        """Send purchase order email with smart fallback"""
        if email_options is None:
            email_options = {
                'to_supplier': True,
                'to_po_dept': True,
                'to_cat_head': True
            }
        
        try:
            # Try to render email content from template
            try:
                html_content = render_to_string('po_system/po_email.html', {
                    'po': po,
                    'items': po.items.all(),
                    'company_name': settings.COMPANY_NAME,
                    'company_phone': getattr(settings, 'COMPANY_PHONE', ''),
                    'company_email': getattr(settings, 'COMPANY_EMAIL', ''),
                    'po_department_email': getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.ZEPTO_FROM_EMAIL),
                })
            except Exception as template_error:
                logger.warning(f"Template not found, using fallback HTML: {template_error}")
                # Fallback HTML content
                html_content = f"""
                <html>
                <body style="font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa;">
                    <div style="max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px;">
                        <h1 style="color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 10px;">
                            {settings.COMPANY_NAME}
                        </h1>
                        <h2>Purchase Order {po.po_number}</h2>
                        
                        <div style="margin: 20px 0;">
                            <p><strong>Date:</strong> {po.created_at.strftime('%B %d, %Y')}</p>
                            <p><strong>Supplier:</strong> {po.supplier.name}</p>
                            <p><strong>Contact:</strong> {po.supplier.contact_person}</p>
                            <p><strong>Status:</strong> {po.get_status_display()}</p>
                        </div>
                        
                        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                            <thead>
                                <tr style="background-color: #f8f9fa;">
                                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Product</th>
                                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Quantity</th>
                                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Unit Price</th>
                                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join([f'''
                                <tr>
                                    <td style="border: 1px solid #ddd; padding: 12px;">{item.product.name}</td>
                                    <td style="border: 1px solid #ddd; padding: 12px;">{item.quantity} {item.product.unit}</td>
                                    <td style="border: 1px solid #ddd; padding: 12px;">₹{item.unit_price}</td>
                                    <td style="border: 1px solid #ddd; padding: 12px;">₹{item.total_price}</td>
                                </tr>
                                ''' for item in po.items.all()])}
                                <tr style="background-color: #e8f5e8; font-weight: bold;">
                                    <td colspan="3" style="border: 1px solid #ddd; padding: 12px; text-align: right;">Total Amount:</td>
                                    <td style="border: 1px solid #ddd; padding: 12px;">₹{po.total_amount}</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                            <p>Best regards,<br>
                            {settings.COMPANY_NAME}<br>
                            Email: {getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.ZEPTO_FROM_EMAIL)}<br>
                            Phone: {getattr(settings, 'COMPANY_PHONE', '')}</p>
                        </div>
                    </div>
                </body>
                </html>
                """
            
            # Plain text version
            text_content = f"""
Purchase Order: {po.po_number}
Supplier: {po.supplier.name}
Date: {po.created_at.strftime('%Y-%m-%d')}
Total Amount: ${po.total_amount}

Items:
""" + "\n".join([f"- {item.product.name}: {item.quantity} x ${item.unit_price} = ${item.total_price}" 
                 for item in po.items.all()]) + f"""

Notes: {po.notes or 'None'}

Best regards,
{settings.COMPANY_NAME}
Phone: {getattr(settings, 'COMPANY_PHONE', '')}
Email: {getattr(settings, 'PO_DEPARTMENT_EMAIL', settings.ZEPTO_FROM_EMAIL)}
            """.strip()
            
            # Prepare recipients
            recipients = []
            
            if email_options.get('to_supplier', True) and po.supplier.email:
                recipients.append({
                    'email': po.supplier.email,
                    'name': po.supplier.name
                })
            
            if email_options.get('to_po_dept', True):
                po_dept_email = getattr(settings, 'PO_DEPARTMENT_EMAIL', None)
                if po_dept_email:
                    recipients.append({
                        'email': po_dept_email,
                        'name': 'PO Department'
                    })
            
            if email_options.get('to_cat_head', True):
                # Get unique category heads
                category_heads = set()
                for item in po.items.all():
                    if item.product.category.head_email:
                        category_heads.add((
                            item.product.category.head_email,
                            item.product.category.head_name or 'Category Head'
                        ))
                
                for email, name in category_heads:
                    recipients.append({
                        'email': email,
                        'name': name
                    })
            
            if not recipients:
                return False, "No valid recipients found"
            
            subject = f'Purchase Order {po.po_number} - {settings.COMPANY_NAME}'
            
            # Try API first, then SMTP as fallback
            if self.api_available:
                success, message = self.send_via_api(
                    from_email=settings.ZEPTO_FROM_EMAIL,
                    from_name=settings.ZEPTO_FROM_NAME,
                    to_emails=recipients,
                    subject=subject,
                    html_body=html_content,
                    text_body=text_content
                )
                
                if success:
                    # Update PO status to sent
                    po.status = 'sent'
                    po.save()
                    return True, f"{message} (API method)"
            
            # Fallback to SMTP if API failed or not available
            if self.smtp_available:
                success, message = self.send_via_smtp(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_emails=recipients,
                    subject=subject,
                    html_body=html_content,
                    text_body=text_content
                )
                
                if success:
                    # Update PO status to sent
                    po.status = 'sent'
                    po.save()
                    return True, f"{message} (SMTP method)"
            
            return False, "Both API and SMTP methods failed"
            
        except Exception as e:
            logger.error(f"Exception in send_po_email: {str(e)}")
            return False, f"Unexpected error: {str(e)}"
    
    def send_test_email(self, to_email, method='auto'):
        """Send test email with specified method"""
        try:
            subject = "Test Email from PO System"
            html_content = """
            <html>
            <body>
                <h2>Test Email</h2>
                <p>This is a test email from your Purchase Order system.</p>
                <p><strong>Company:</strong> {company_name}</p>
                <p><strong>Time:</strong> {timestamp}</p>
                <p>If you received this email, your email configuration is working correctly!</p>
            </body>
            </html>
            """.format(
                company_name=settings.COMPANY_NAME,
                timestamp=timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            text_content = f"""
Test Email from PO System

Company: {settings.COMPANY_NAME}
Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

If you received this email, your email configuration is working correctly!
            """.strip()
            
            recipients = [{'email': to_email, 'name': 'Test Recipient'}]
            
            if method == 'api' and self.api_available:
                return self.send_via_api(
                    from_email=settings.ZEPTO_FROM_EMAIL,
                    from_name=settings.ZEPTO_FROM_NAME,
                    to_emails=recipients,
                    subject=subject,
                    html_body=html_content,
                    text_body=text_content
                )
            elif method == 'smtp' and self.smtp_available:
                return self.send_via_smtp(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_emails=recipients,
                    subject=subject,
                    html_body=html_content,
                    text_body=text_content
                )
            elif method == 'auto':
                # Try API first, then SMTP
                if self.api_available:
                    success, message = self.send_via_api(
                        from_email=settings.ZEPTO_FROM_EMAIL,
                        from_name=settings.ZEPTO_FROM_NAME,
                        to_emails=recipients,
                        subject=subject,
                        html_body=html_content,
                        text_body=text_content
                    )
                    if success:
                        return True, f"{message} (API)"
                
                if self.smtp_available:
                    success, message = self.send_via_smtp(
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to_emails=recipients,
                        subject=subject,
                        html_body=html_content,
                        text_body=text_content
                    )
                    if success:
                        return True, f"{message} (SMTP)"
                
                return False, "Both API and SMTP methods failed"
            else:
                return False, f"Method '{method}' not available or not configured"
                
        except Exception as e:
            logger.error(f"Exception in send_test_email: {str(e)}")
            return False, f"Test email error: {str(e)}"

# Create a global instance
email_service = EmailService()
