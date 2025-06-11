# po_system/email_backends.py - API-Only Backend

import json
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class APIOnlyEmailBackend:
    """
    Email backend that only uses APIs (no SMTP)
    Works when SMTP ports are blocked
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        self.fail_silently = fail_silently
    
    def open(self):
        return True
    
    def close(self):
        pass
    
    def send_messages(self, email_messages):
        """Send emails using various API services"""
        
        sent_count = 0
        
        for message in email_messages:
            # Try different API services in order of preference
            success = (
                self._try_sendgrid_api(message) or
                self._try_mailgun_api(message) or 
                self._try_gmail_api(message)
            )
            
            if success:
                sent_count += 1
            elif not self.fail_silently:
                raise Exception("All email APIs failed")
        
        return sent_count
    
    def _try_sendgrid_api(self, message):
        """Try SendGrid API (if you have API key)"""
        
        api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        if not api_key:
            return False
        
        try:
            payload = {
                "personalizations": [
                    {
                        "to": [{"email": recipient} for recipient in message.to],
                        "subject": message.subject
                    }
                ],
                "from": {"email": getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')},
                "content": [
                    {
                        "type": "text/plain",
                        "value": message.body
                    }
                ]
            }
            
            # Add HTML content if available
            for alternative in getattr(message, 'alternatives', []):
                if alternative[1] == 'text/html':
                    payload["content"].append({
                        "type": "text/html",
                        "value": alternative[0]
                    })
                    break
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                'https://api.sendgrid.com/v3/mail/send',
                data=json.dumps(payload),
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 202:
                logger.info(f"Email sent via SendGrid API to {message.to}")
                return True
            else:
                logger.error(f"SendGrid API failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid API error: {e}")
            return False
    
    def _try_mailgun_api(self, message):
        """Try Mailgun API (if you have API key)"""
        
        api_key = getattr(settings, 'MAILGUN_API_KEY', None)
        domain = getattr(settings, 'MAILGUN_DOMAIN', None)
        
        if not api_key or not domain:
            return False
        
        try:
            data = {
                'from': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                'to': message.to,
                'subject': message.subject,
                'text': message.body
            }
            
            # Add HTML content if available
            for alternative in getattr(message, 'alternatives', []):
                if alternative[1] == 'text/html':
                    data['html'] = alternative[0]
                    break
            
            response = requests.post(
                f'https://api.mailgun.net/v3/{domain}/messages',
                auth=('api', api_key),
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Email sent via Mailgun API to {message.to}")
                return True
            else:
                logger.error(f"Mailgun API failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Mailgun API error: {e}")
            return False
    
    def _try_gmail_api(self, message):
        """Try Gmail API (requires OAuth setup)"""
        
        # Gmail API requires OAuth2 setup which is more complex
        # For now, return False
        # You would need to implement OAuth2 flow for Gmail API
        return False


# Simple Gmail SMTP backend for testing
class GmailSMTPBackend:
    """
    Simple Gmail SMTP backend
    """
    
    def __init__(self, fail_silently=False, **kwargs):
        self.fail_silently = fail_silently
    
    def open(self):
        return True
    
    def close(self):
        pass
    
    def send_messages(self, email_messages):
        """Send emails via Gmail SMTP"""
        
        import smtplib
        import ssl
        from email.message import EmailMessage
        
        gmail_user = getattr(settings, 'GMAIL_USER', None)
        gmail_password = getattr(settings, 'GMAIL_PASSWORD', None)
        
        if not gmail_user or not gmail_password:
            if not self.fail_silently:
                raise Exception("Gmail credentials not configured")
            return 0
        
        sent_count = 0
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls(context=context)
                server.login(gmail_user, gmail_password)
                
                for message in email_messages:
                    try:
                        # Convert Django EmailMessage to standard EmailMessage
                        msg = EmailMessage()
                        msg['Subject'] = message.subject
                        msg['From'] = gmail_user
                        msg['To'] = ', '.join(message.to)
                        msg.set_content(message.body)
                        
                        # Add HTML content if available
                        for alternative in getattr(message, 'alternatives', []):
                            if alternative[1] == 'text/html':
                                msg.add_alternative(alternative[0], subtype='html')
                                break
                        
                        server.send_message(msg)
                        sent_count += 1
                        logger.info(f"Email sent via Gmail to {message.to}")
                        
                    except Exception as e:
                        logger.error(f"Failed to send email via Gmail: {e}")
                        if not self.fail_silently:
                            raise
                            
        except Exception as e:
            logger.error(f"Gmail SMTP connection failed: {e}")
            if not self.fail_silently:
                raise
        
        return sent_count
