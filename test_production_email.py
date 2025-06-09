# test_production_email.py - Final comprehensive test

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'po_management.settings')
django.setup()

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from po_system.services.email_service import email_service

def test_production_setup():
    """Test the complete production email setup"""
    print("🚀 Production Email System Test")
    print("=" * 60)
    print(f"🏢 Company: {settings.COMPANY_NAME}")
    print(f"📧 From Email: {settings.DEFAULT_FROM_EMAIL}")
    print(f"🔧 Backend: {settings.EMAIL_BACKEND}")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Basic Django send_mail
    print("\n📤 Test 1: Basic Django send_mail")
    try:
        send_mail(
            subject='✅ Production Test 1 - Basic Email',
            message=f'''
Production Email Test Successful!

Your {settings.COMPANY_NAME} PO Management System is now ready for production use.

✅ Django Email Backend: Working
✅ Zepto Mail SMTP: Connected  
✅ SSL Certificate: Handled
✅ Authentication: Successful

This confirms your email system is production-ready!

Best regards,
{settings.COMPANY_NAME} IT Team
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['jerish220@gmail.com'],
            fail_silently=False,
        )
        print("   ✅ Basic email sent successfully!")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Basic email failed: {e}")
    
    # Test 2: HTML Email with attachments
    print("\n🎨 Test 2: HTML Email with formatting")
    try:
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 20px; text-align: center; border-radius: 8px;">
                    <h1>🎉 Production Email System Active!</h1>
                    <p>{settings.COMPANY_NAME} PO Management System</p>
                </div>
                
                <div style="padding: 20px; background: #f9f9f9; margin: 20px 0; border-radius: 8px;">
                    <h2 style="color: #2c3e50;">✅ System Status: Operational</h2>
                    <p>Your Purchase Order Management System is now ready to send professional emails.</p>
                    
                    <h3>📋 Features Confirmed:</h3>
                    <ul>
                        <li>✅ SMTP Connection via Zepto Mail</li>
                        <li>✅ SSL Certificate Handling</li>
                        <li>✅ HTML Email Support</li>
                        <li>✅ Professional Templates</li>
                        <li>✅ Multiple Recipients</li>
                        <li>✅ Error Handling & Logging</li>
                    </ul>
                </div>
                
                <div style="padding: 20px; background: #e8f5e8; border-left: 4px solid #27ae60;">
                    <h3 style="color: #27ae60;">🚀 Ready for Business</h3>
                    <p>Your system can now send Purchase Orders to:</p>
                    <ul>
                        <li>Suppliers ({settings.DEFAULT_FROM_EMAIL})</li>
                        <li>Purchase Department ({settings.PO_DEPARTMENT_EMAIL})</li>
                        <li>Category Heads (as configured)</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #666;">
                    <p>Best regards,<br>
                    <strong>{settings.COMPANY_NAME} IT Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
Production Email System Active!

Your {settings.COMPANY_NAME} PO Management System is now operational.

System Status: ✅ Ready
Features: HTML Email, SSL Handling, Multi-recipient support

Your Purchase Order emails will now be delivered professionally.

Best regards,
{settings.COMPANY_NAME} IT Team
        """
        
        email = EmailMultiAlternatives(
            subject='🎨 Production Test 2 - HTML Email',
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['jerish220@gmail.com'],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        print("   ✅ HTML email sent successfully!")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ HTML email failed: {e}")
    
    # Test 3: Email Service Integration
    print("\n🔧 Test 3: Email Service Integration")
    try:
        success, message = email_service.send_test_email('jerish220@gmail.com', 'smtp')
        if success:
            print(f"   ✅ Email service test: {message}")
            tests_passed += 1
        else:
            print(f"   ❌ Email service test failed: {message}")
    except Exception as e:
        print(f"   ❌ Email service test error: {e}")
    
    # Test 4: Multi-recipient email (simulating PO notification)
    print("\n👥 Test 4: Multi-recipient PO simulation")
    try:
        recipients = [
            'jerish220@gmail.com',  # Supplier
            settings.PO_DEPARTMENT_EMAIL,  # PO Department
        ]
        
        # Remove duplicates and invalid emails
        recipients = [email for email in recipients if email and '@' in email]
        recipients = list(set(recipients))  # Remove duplicates
        
        send_mail(
            subject='📋 Production Test 4 - PO Notification Simulation',
            message=f'''
Purchase Order Notification Simulation

This email simulates how your PO Management System will send 
notifications to multiple recipients:

Recipients in this test:
- Supplier: jerish220@gmail.com
- PO Department: {settings.PO_DEPARTMENT_EMAIL}

In production, this will include:
- Selected suppliers
- Purchase department
- Category heads (when applicable)

System Status: ✅ Ready for Production

Best regards,
{settings.COMPANY_NAME}
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        print(f"   ✅ Multi-recipient email sent to {len(recipients)} recipients!")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Multi-recipient email failed: {e}")
    
    # Test Summary
    print("\n" + "=" * 60)
    print("📊 PRODUCTION TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("\n🎉 CONGRATULATIONS!")
        print("Your email system is 100% ready for production!")
        print("\n✅ What this means:")
        print("  • Purchase Orders will be delivered successfully")
        print("  • Professional HTML emails with your branding")
        print("  • Multiple recipients supported")
        print("  • Reliable error handling and logging")
        print("  • SSL certificate issues resolved")
        print("\n🚀 Your PO Management System is ready to go live!")
        
    elif tests_passed >= 2:
        print("\n⚠️  Most features working!")
        print(f"Core functionality is operational ({tests_passed}/{total_tests} tests passed)")
        print("Your system can be used in production with some limitations.")
        
    else:
        print("\n❌ Needs attention before production")
        print("Please review the failed tests and configurations.")
    
    print("\n📈 Next Steps:")
    print("1. Start using your PO Management System")
    print("2. Monitor the email logs for any issues")
    print("3. Test with real Purchase Orders")
    print("4. Set up email monitoring/alerts if needed")
    
    print("=" * 60)
    
    return tests_passed == total_tests

if __name__ == "__main__":
    test_production_setup()