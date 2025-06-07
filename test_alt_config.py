import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'po_management.settings')
django.setup()

import smtplib
from email.mime.text import MIMEText

def test_multiple_configs():
    """Test multiple SMTP configurations"""
    
    configs = [
        {
            'host': 'smtp.zeptomail.in',
            'port': 587,
            'user': 'noreply@jeyarama.com',
            'password': 'PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETDQvt7ZNA==',
            'tls': True,
            'ssl': False
        },
        {
            'host': 'smtp.zeptomail.in',
            'port': 465,
            'user': 'noreply@jeyarama.com',
            'password': 'PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETDQvt7ZNA==',
            'tls': False,
            'ssl': True
        },
        {
            'host': 'smtp.zeptomail.com',  # Try .com instead of .in
            'port': 587,
            'user': 'noreply@jeyarama.com',
            'password': 'PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETDQvt7ZNA==',
            'tls': True,
            'ssl': False
        }
    ]
    
    for i, config in enumerate(configs):
        try:
            print(f"Testing Config {i+1}: {config['host']}:{config['port']}")
            
            if config['ssl']:
                server = smtplib.SMTP_SSL(config['host'], config['port'], timeout=30)
            else:
                server = smtplib.SMTP(config['host'], config['port'], timeout=30)
                if config['tls']:
                    server.starttls()
            
            server.login(config['user'], config['password'])
            
            # Send test email
            msg = MIMEText('Test email from Python')
            msg['Subject'] = f'Test Email - Config {i+1}'
            msg['From'] = config['user']
            msg['To'] = 'jerish220@gmail.com'  # Change this to your email
            
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Config {i+1} - SUCCESS!")
            print(f"   Host: {config['host']}")
            print(f"   Port: {config['port']}")
            print(f"   TLS: {config['tls']}")
            print(f"   SSL: {config['ssl']}")
            
            return config
            
        except Exception as e:
            print(f"❌ Config {i+1} - FAILED: {e}")
        
        print("-" * 30)
    
    return None

if __name__ == "__main__":
    working_config = test_multiple_configs()
    
    if working_config:
        print("\n🎉 WORKING CONFIGURATION FOUND!")
        print("Update your Django settings.py with:")
        print(f"EMAIL_HOST = '{working_config['host']}'")
        print(f"EMAIL_PORT = {working_config['port']}")
        print(f"EMAIL_USE_TLS = {working_config['tls']}")
        print(f"EMAIL_USE_SSL = {working_config['ssl']}")
    else:
        print("\n❌ No working configuration found.")
        print("Check your network/firewall settings or contact your ISP.")