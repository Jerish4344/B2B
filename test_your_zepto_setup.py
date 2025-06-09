# test_your_zepto_setup.py

import os
import django
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'po_management.settings')
django.setup()

def test_direct_smtp():
    """Test your exact Zepto Mail SMTP configuration"""
    print("🚀 Testing Your Zepto Mail SMTP Configuration")
    print("=" * 60)
    
    # Your exact credentials from the screenshot
    smtp_server = "smtp.zeptomail.in"
    smtp_port = 587
    username = "emailapikey"
    password = "PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETQPXOy44+tLqZs+uGJmnkNmkeVGqyqK3sx/VYSPOZsbq6x00Vs14bdk3eUoXtd9Jr1SDQvt7ZNA=="
    from_email = "noreply@jeyarama.com"
    
    try:
        print(f"📡 Connecting to {smtp_server}:{smtp_port}")
        print(f"👤 Username: {username}")
        print(f"📧 From: {from_email}")
        
        # Create SMTP connection
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.set_debuglevel(1)  # Show detailed connection info
        
        print("\n🔐 Starting TLS...")
        server.starttls()
        
        print("🔑 Logging in...")
        server.login(username, password)
        
        # Create test message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Test Email from Jeyarama Company PO System'
        msg['From'] = from_email
        msg['To'] = 'jerish220@gmail.com'  # Your test email
        
        # Plain text version
        text = f"""
        🎉 SUCCESS! Your Zepto Mail SMTP is working perfectly!
        
        This test email confirms that your Django PO Management System 
        can now send emails using Zepto Mail SMTP.
        
        Configuration Details:
        - SMTP Server: {smtp_server}
        - Port: {smtp_port}
        - From Email: {from_email}
        - Company: Jeyarama Company
        
        Your Purchase Order emails will now be delivered successfully!
        
        Best regards,
        Jeyarama Company IT Team
        """
        
        # HTML version
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 20px; text-align: center; border-radius: 8px;">
                    <h1>🎉 Zepto Mail SMTP Test Successful!</h1>
                    <p>Jeyarama Company PO Management System</p>
                </div>
                
                <div style="padding: 20px; background: #f9f9f9; margin: 20px 0; border-radius: 8px;">
                    <h2 style="color: #2c3e50;">✅ Configuration Verified</h2>
                    <p>Your Django PO Management System can now send emails using Zepto Mail SMTP.</p>
                    
                    <h3>📋 Configuration Details:</h3>
                    <ul>
                        <li><strong>SMTP Server:</strong> {smtp_server}</li>
                        <li><strong>Port:</strong> {smtp_port}</li>
                        <li><strong>From Email:</strong> {from_email}</li>
                        <li><strong>Company:</strong> Jeyarama Company</li>
                        <li><strong>Status:</strong> <span style="color: #27ae60;">Active ✅</span></li>
                    </ul>
                </div>
                
                <div style="padding: 20px; background: #e8f5e8; border-left: 4px solid #27ae60; margin: 20px 0;">
                    <h3 style="color: #27ae60;">🚀 Ready for Production</h3>
                    <p>Your Purchase Order emails will now be delivered successfully to:</p>
                    <ul>
                        <li>Suppliers</li>
                        <li>Purchase Department</li>
                        <li>Category Heads</li>
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px; color: #666;">
                    <p>Best regards,<br>
                    <strong>Jeyarama Company IT Team</strong></p>
                    <p><small>This is an automated test email from your PO Management System</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach parts
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        print("\n📤 Sending test email...")
        server.send_message(msg)
        server.quit()
        
        print("\n" + "=" * 60)
        print("✅ SUCCESS! Email sent successfully!")
        print("📬 Check your inbox at jerish220@gmail.com")
        print("🎉 Your Zepto Mail SMTP integration is working perfectly!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Verify your domain 'jeyarama.com' is verified in Zepto Mail")
        print("2. Check if the API token is still valid")
        print("3. Ensure 'noreply@jeyarama.com' is configured as a sender")
        print("4. Check your network firewall settings")
        return False

def test_django_integration():
    """Test Django email integration"""
    print("\n🐍 Testing Django Email Integration")
    print("=" * 60)
    
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        print("📋 Current Django Settings:")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        print("\n📤 Sending test email via Django...")
        
        send_mail(
            subject='Django Integration Test - Jeyarama Company',
            message='''
            🎉 Django Integration Test Successful!
            
            This email confirms that your Django PO Management System 
            is properly configured to send emails via Zepto Mail SMTP.
            
            Your Purchase Order system is ready to go!
            
            Best regards,
            Jeyarama Company
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['jerish220@gmail.com'],
            fail_silently=False,
        )
        
        print("✅ Django email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Django email failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Jeyarama Company - Zepto Mail SMTP Test")
    print("=" * 60)
    
    # Test 1: Direct SMTP
    smtp_success = test_direct_smtp()
    
    # Test 2: Django Integration
    django_success = test_django_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Direct SMTP Test: {'✅ PASSED' if smtp_success else '❌ FAILED'}")
    print(f"Django Integration: {'✅ PASSED' if django_success else '❌ FAILED'}")
    
    if smtp_success and django_success:
        print("\n🎉 CONGRATULATIONS!")
        print("Your Zepto Mail integration is working perfectly!")
        print("Your PO Management System is ready to send emails!")
    elif smtp_success:
        print("\n⚠️  SMTP works but Django integration needs attention")
        print("Check your Django settings configuration")
    else:
        print("\n❌ Integration needs troubleshooting")
        print("Please check your Zepto Mail configuration")
    
    print("=" * 60)