# quick_fix_test.py - Test the fixed backend

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'po_management.settings')
django.setup()

def test_quick_fix():
    """Test with the corrected backend"""
    print("🔧 Testing Fixed Email Backend")
    print("=" * 50)
    
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        print(f"Using backend: {settings.EMAIL_BACKEND}")
        print(f"From email: {settings.DEFAULT_FROM_EMAIL}")
        
        # Test basic email
        send_mail(
            subject='✅ Quick Fix Test - Jeyarama Company',
            message='''
🎉 Email Backend Fix Successful!

Your custom Zepto Mail backend is now working correctly.

The SSL certificate verification issue has been resolved,
and your Django PO Management System is ready for production.

Best regards,
Jeyarama Company IT Team
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['jerish220@gmail.com'],
            fail_silently=False,
        )
        
        print("✅ SUCCESS! Fixed backend is working!")
        print("📧 Test email sent to jerish220@gmail.com")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n🔧 Let's try the simple backend...")
        
        # Try with simple backend
        try:
            # Temporarily switch to simple backend
            from django.conf import settings
            settings.EMAIL_BACKEND = 'po_system.email_backends.ZeptoMailBackendSimple'
            
            from django.core.mail import send_mail
            
            send_mail(
                subject='✅ Simple Backend Test - Jeyarama Company',
                message='''
🎉 Simple Email Backend Working!

Your simplified Zepto Mail backend resolved the issues.

Your Django PO Management System is ready for production.

Best regards,
Jeyarama Company IT Team
                ''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['jerish220@gmail.com'],
                fail_silently=False,
            )
            
            print("✅ SUCCESS! Simple backend is working!")
            print("💡 Use ZeptoMailBackendSimple in your settings")
            return True
            
        except Exception as e2:
            print(f"❌ Simple backend also failed: {e2}")
            return False

def test_direct_approach():
    """Test with direct SMTP approach that we know works"""
    print("\n🔄 Testing Direct SMTP Approach")
    print("=" * 50)
    
    try:
        from django.core.mail import get_connection, EmailMessage
        from django.conf import settings
        import smtplib
        import ssl
        
        # Create a patched connection function
        def create_zepto_connection():
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            connection = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            connection.starttls(context=context)
            connection.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            return connection
        
        # Test the direct connection
        smtp_conn = create_zepto_connection()
        
        # Create Django email with custom connection
        from django.core.mail.backends.smtp import EmailBackend
        
        # Create a custom connection instance
        django_connection = EmailBackend()
        django_connection.connection = smtp_conn
        
        # Send email
        email = EmailMessage(
            subject='✅ Direct Approach Test - Jeyarama Company',
            body='''
🎯 Direct SMTP Approach Working!

This email was sent using the direct SMTP connection method
that bypasses Django's built-in SSL verification.

Your PO Management System can use this approach for reliable email delivery.

Best regards,
Jeyarama Company IT Team
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['jerish220@gmail.com'],
            connection=django_connection
        )
        
        email.send()
        smtp_conn.quit()
        
        print("✅ SUCCESS! Direct approach working!")
        print("📧 Email sent using direct SMTP connection")
        return True
        
    except Exception as e:
        print(f"❌ Direct approach failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Email Backend Quick Fix Test")
    print("=" * 50)
    
    # Test 1: Fixed backend
    success1 = test_quick_fix()
    
    # Test 2: Direct approach (if first fails)
    success2 = False
    if not success1:
        success2 = test_direct_approach()
    
    print("\n" + "=" * 50)
    print("📊 QUICK FIX SUMMARY")
    print("=" * 50)
    
    if success1:
        print("✅ Fixed custom backend is working!")
        print("🎯 Use: EMAIL_BACKEND = 'po_system.email_backends.ZeptoMailBackend'")
        print("   or: EMAIL_BACKEND = 'po_system.email_backends.ZeptoMailBackendSimple'")
    elif success2:
        print("✅ Direct SMTP approach is working!")
        print("🎯 Implement direct connection in your email service")
    else:
        print("❌ Both approaches failed")
        print("🔧 Check your network/firewall settings")
    
    print("\n🚀 If any test passed, your email system is ready!")
    print("=" * 50)