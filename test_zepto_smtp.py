# test_zepto_smtp.py

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'po_management.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from po_system.utils import (
    test_smtp_connection, 
    send_test_email, 
    test_zepto_mail_api,
    validate_email_settings
)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_zepto_smtp_direct():
    """Test Zepto Mail SMTP directly"""
    print("=" * 60)
    print("TESTING ZEPTO MAIL SMTP DIRECTLY")
    print("=" * 60)
    
    try:
        # SMTP Configuration
        smtp_server = "smtp.zeptomail.in"
        smtp_port = 587
        username = "noreply@jeyarama.com"
        password = "PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETQPXOy44+tLqZs+uGJmnkNmkeVGqyqK3sx/VYSPOZsbq6x00Vs14bdk3eUoXtd9Jr1SDQvt7ZNA=="
        
        print(f"Connecting to {smtp_server}:{smtp_port}")
        print(f"Username: {username}")
        
        # Create SMTP connection
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.set_debuglevel(1)  # Enable debug output
        
        print("Starting TLS...")
        server.starttls()
        
        print("Logging in...")
        server.login(username, password)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Test Email from Zepto Mail SMTP'
        msg['From'] = username
        msg['To'] = 'jerish220@gmail.com'  # Change to your test email
        
        # Plain text version
        text = """
        This is a test email from your Django PO Management System using Zepto Mail SMTP.
        
        If you receive this email, your SMTP configuration is working correctly!
        
        Settings used:
        - SMTP Server: smtp.zeptomail.in
        - Port: 587
        - TLS: Enabled
        
        Best regards,
        Jeyarama Company
        """
        
        # HTML version
        html = """
        <html>
          <body>
            <h2>Test Email from Zepto Mail SMTP</h2>
            <p>This is a test email from your Django PO Management System using <strong>Zepto Mail SMTP</strong>.</p>
            <p>If you receive this email, your SMTP configuration is working correctly!</p>
            
            <h3>Settings used:</h3>
            <ul>
                <li>SMTP Server: smtp.zeptomail.in</li>
                <li>Port: 587</li>
                <li>TLS: Enabled</li>
            </ul>
            
            <p>Best regards,<br>
            <strong>Jeyarama Company</strong></p>
          </body>
        </html>
        """
        
        # Attach parts
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        print("Sending email...")
        server.send_message(msg)
        server.quit()
        
        print("✅ SUCCESS: Email sent successfully using Zepto Mail SMTP!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_django_smtp():
    """Test Django SMTP with current settings"""
    print("\n" + "=" * 60)
    print("TESTING DJANGO SMTP INTEGRATION")
    print("=" * 60)
    
    try:
        print("Current Django Email Settings:")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        # Test connection
        print("\nTesting SMTP connection...")
        success, message = test_smtp_connection()
        print(f"Connection test: {message}")
        
        if success:
            print("\nSending test email via Django...")
            success, message = send_test_email('jerish220@gmail.com')  # Change to your test email
            print(f"Email test: {message}")
            
            if success:
                print("✅ SUCCESS: Django SMTP is working!")
                return True
        
        print("❌ Django SMTP test failed")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_zepto_api():
    """Test Zepto Mail API"""
    print("\n" + "=" * 60)
    print("TESTING ZEPTO MAIL API")
    print("=" * 60)
    
    try:
        result = test_zepto_mail_api()
        if result['success']:
            print("✅ SUCCESS: Zepto Mail API is working!")
            print(f"Message: {result['message']}")
        else:
            print(f"❌ FAILED: {result['message']}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def validate_configuration():
    """Validate email configuration"""
    print("\n" + "=" * 60)
    print("VALIDATING EMAIL CONFIGURATION")
    print("=" * 60)
    
    try:
        validation = validate_email_settings()
        
        print(f"Configuration valid: {validation['valid']}")
        print(f"SMTP configured: {validation['smtp_configured']}")
        print(f"API configured: {validation['api_configured']}")
        
        if validation['issues']:
            print("\nIssues found:")
            for issue in validation['issues']:
                print(f"- {issue}")
        else:
            print("✅ No configuration issues found!")
        
        return validation['valid']
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def run_comprehensive_test():
    """Run all tests"""
    print("🚀 STARTING COMPREHENSIVE ZEPTO MAIL TEST")
    print("=" * 60)
    
    results = {
        'config_valid': False,
        'direct_smtp': False,
        'django_smtp': False,
        'api_test': False
    }
    
    # 1. Validate configuration
    results['config_valid'] = validate_configuration()
    
    # 2. Test direct SMTP
    results['direct_smtp'] = test_zepto_smtp_direct()
    
    # 3. Test Django SMTP integration
    results['django_smtp'] = test_django_smtp()
    
    # 4. Test Zepto Mail API
    results['api_test'] = test_zepto_api()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    print(f"Configuration Valid: {'✅' if results['config_valid'] else '❌'}")
    print(f"Direct SMTP Test: {'✅' if results['direct_smtp'] else '❌'}")
    print(f"Django SMTP Test: {'✅' if results['django_smtp'] else '❌'}")
    print(f"API Test: {'✅' if results['api_test'] else '❌'}")
    
    if any(results.values()):
        print("\n🎉 SUCCESS: At least one email method is working!")
        if results['django_smtp']:
            print("✅ Recommended: Use Django SMTP (already configured)")
        elif results['direct_smtp']:
            print("✅ Alternative: Direct SMTP works, check Django configuration")
        elif results['api_test']:
            print("✅ Alternative: Use Zepto Mail API as fallback")
    else:
        print("\n❌ FAILURE: No email methods are working")
        print("Please check your Zepto Mail account and credentials")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == 'direct':
            test_zepto_smtp_direct()
        elif test_type == 'django':
            test_django_smtp()
        elif test_type == 'api':
            test_zepto_api()
        elif test_type == 'config':
            validate_configuration()
        else:
            print("Usage: python test_zepto_smtp.py [direct|django|api|config]")
            print("Or run without arguments for comprehensive test")
    else:
        run_comprehensive_test()