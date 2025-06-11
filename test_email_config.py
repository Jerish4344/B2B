# test_email_config.py - Run this to test your email configuration

import smtplib
import ssl
import json
import requests
from email.message import EmailMessage

# Your Zepto Mail credentials
SMTP_SERVER = "smtp.zeptomail.in"
SMTP_PORT = 587
USERNAME = "emailapikey"
PASSWORD = "PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETQPXOy44+tLqZs+uGJmnkNmkeVGqyqK3sx/VYSPOZsbq6x00Vs14bdk3eUoXtd9Jr1SDQvt7ZNA=="

# IMPORTANT: Replace with your verified email addresses
FROM_EMAIL = "admin@jeyarama.com"  # Must be verified in Zepto Mail
TO_EMAIL = "jerish@jcrc.in"

# API Configuration
API_KEY = "PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETQPXOy44+tLqZs+uGJmnkNmkeVGqyqK3sx/VYSPOZsbq6x00Vs14bdk3eUoXtd9Jr1SDQvt7ZNA=="

def test_smtp():
    """Test SMTP connection"""
    print("Testing SMTP connection...")
    
    try:
        msg = EmailMessage()
        msg['Subject'] = "Test Email via SMTP"
        msg['From'] = FROM_EMAIL
        msg['To'] = TO_EMAIL
        msg.set_content("This is a test email sent via SMTP.")
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(USERNAME, PASSWORD)
            server.send_message(msg)
        
        print("✅ SMTP test successful!")
        return True
        
    except Exception as e:
        print(f"❌ SMTP test failed: {e}")
        return False

def test_api():
    """Test API connection"""
    print("Testing API connection...")
    
    try:
        payload = {
            'bounce_address': FROM_EMAIL,
            'from': {
                'address': FROM_EMAIL,
                'name': 'Jeyarama Company',
            },
            'to': [
                {
                    'email_address': {
                        'address': TO_EMAIL,
                        'name': 'Test User'
                    }
                }
            ],
            'subject': 'Test Email via API',
            'textbody': 'This is a test email sent via API.',
            'htmlbody': '<p>This is a test email sent via API.</p>'
        }
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Zoho-enczapikey {API_KEY}',
        }
        
        response = requests.post(
            'https://api.zeptomail.in/v1.1/email',
            data=json.dumps(payload),
            headers=headers,
            timeout=60
        )
        
        if response.status_code == 200:
            print("✅ API test successful!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ API test failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    print("🧪 Testing Zepto Mail Configuration")
    print("=" * 50)
    
    print(f"FROM_EMAIL: {FROM_EMAIL}")
    print(f"TO_EMAIL: {TO_EMAIL}")
    print()
    
    # Test SMTP first
    smtp_success = test_smtp()
    print()
    
    # Test API
    api_success = test_api()
    print()
    
    # Summary
    print("📋 Test Summary:")
    print(f"SMTP: {'✅ Working' if smtp_success else '❌ Failed'}")
    print(f"API: {'✅ Working' if api_success else '❌ Failed'}")
    
    if not smtp_success and not api_success:
        print("\n⚠️  Both methods failed. Please check:")
        print("1. Domain verification in Zepto Mail")
        print("2. Email address verification")
        print("3. API key validity")
    elif smtp_success or api_success:
        print("\n🎉 At least one method is working!")

if __name__ == "__main__":
    main()
