# po_system/management/commands/test_email.py

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from po_system.services.email_service import email_service
from po_system.utils import (
    test_smtp_connection, 
    send_test_email, 
    test_zepto_mail_api,
    validate_email_settings
)
import sys

class Command(BaseCommand):
    help = 'Test email configuration and send test emails'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to',
        )
        parser.add_argument(
            '--method',
            type=str,
            choices=['smtp', 'api', 'auto'],
            default='auto',
            help='Email method to test (default: auto)',
        )
        parser.add_argument(
            '--check-config',
            action='store_true',
            help='Only check configuration without sending email',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Email Configuration Test Tool')
        )
        self.stdout.write('=' * 50)
        
        # Check configuration first
        self.stdout.write('\n📋 Checking email configuration...')
        validation = validate_email_settings()
        
        if validation['valid']:
            self.stdout.write(
                self.style.SUCCESS('✅ Email configuration is valid')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Email configuration has issues:')
            )
            for issue in validation['issues']:
                self.stdout.write(f'  - {issue}')
        
        self.stdout.write(f'📧 SMTP Available: {"Yes" if validation["smtp_configured"] else "No"}')
        self.stdout.write(f'🔌 API Available: {"Yes" if validation["api_configured"] else "No"}')
        
        if options['verbose']:
            self.stdout.write('\n🔧 Current Settings:')
            self.stdout.write(f'  EMAIL_HOST: {getattr(settings, "EMAIL_HOST", "Not set")}')
            self.stdout.write(f'  EMAIL_PORT: {getattr(settings, "EMAIL_PORT", "Not set")}')
            self.stdout.write(f'  EMAIL_USE_TLS: {getattr(settings, "EMAIL_USE_TLS", "Not set")}')
            self.stdout.write(f'  EMAIL_HOST_USER: {getattr(settings, "EMAIL_HOST_USER", "Not set")}')
            self.stdout.write(f'  DEFAULT_FROM_EMAIL: {getattr(settings, "DEFAULT_FROM_EMAIL", "Not set")}')
            self.stdout.write(f'  ZEPTO_FROM_EMAIL: {getattr(settings, "ZEPTO_FROM_EMAIL", "Not set")}')
            self.stdout.write(f'  COMPANY_NAME: {getattr(settings, "COMPANY_NAME", "Not set")}')
        
        # If only checking configuration, stop here
        if options['check_config']:
            return
        
        # Test email functionality
        if not options['email']:
            self.stdout.write(
                self.style.ERROR('\n❌ Please provide an email address with --email')
            )
            self.stdout.write('Example: python manage.py test_email --email test@example.com')
            return
        
        email_address = options['email']
        method = options['method']
        
        self.stdout.write(f'\n📨 Testing email to: {email_address}')
        self.stdout.write(f'📡 Method: {method}')
        
        # Test connection first
        if method in ['smtp', 'auto'] and validation['smtp_configured']:
            self.stdout.write('\n🔍 Testing SMTP connection...')
            success, message = test_smtp_connection()
            if success:
                self.stdout.write(self.style.SUCCESS(f'✅ SMTP: {message}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ SMTP: {message}'))
        
        if method in ['api', 'auto'] and validation['api_configured']:
            self.stdout.write('\n🔍 Testing API connection...')
            result = test_zepto_mail_api()
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f'✅ API: {result["message"]}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ API: {result["message"]}'))
        
        # Send test email
        self.stdout.write(f'\n📤 Sending test email to {email_address}...')
        
        try:
            success, message = email_service.send_test_email(email_address, method)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {message}')
                )
                self.stdout.write('\n🎉 Test completed successfully!')
                self.stdout.write(f'📬 Check your inbox at {email_address}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ {message}')
                )
                self.stdout.write('\n💡 Troubleshooting tips:')
                self.stdout.write('  1. Check your email credentials')
                self.stdout.write('  2. Verify your domain is configured in Zepto Mail')
                self.stdout.write('  3. Check firewall settings for port 587')
                self.stdout.write('  4. Ensure your Zepto Mail account is active')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Unexpected error: {str(e)}')
            )
        
        self.stdout.write('\n' + '=' * 50)
        
        # Additional help
        if not validation['smtp_configured'] and not validation['api_configured']:
            self.stdout.write(
                self.style.WARNING('\n⚠️  No email methods are configured!')
            )
            self.stdout.write('Please configure at least one email method:')
            self.stdout.write('\n📧 For SMTP, add to settings.py:')
            self.stdout.write("""
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.zeptomail.in'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@yourdomain.com'
EMAIL_HOST_PASSWORD = 'your-smtp-password'
DEFAULT_FROM_EMAIL = 'your-email@yourdomain.com'
            """)
            
            self.stdout.write('\n🔌 For API backup, add to settings.py:')
            self.stdout.write("""
ZEPTO_API_KEY = 'your-zepto-api-key'
ZEPTO_FROM_EMAIL = 'your-email@yourdomain.com'
ZEPTO_FROM_NAME = 'Your Company Name'
            """)

    def get_email_service_status(self):
        """Get current email service status"""
        return {
            'smtp_available': email_service.smtp_available,
            'api_available': email_service.api_available,
            'methods_available': email_service.smtp_available or email_service.api_available
        }