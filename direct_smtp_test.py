# direct_smtp_test.py - Test SMTP without API

import smtplib
import ssl
from email.message import EmailMessage

def test_smtp_variations():
    """Test different SMTP configurations"""
    
    # Configuration variations to try
    configs = [
        {
            'name': 'Original Config',
            'host': 'smtp.zeptomail.in',
            'port': 587,
            'username': 'emailapikey',
            'password': 'PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETQPXOy44+tLqZs+uGJmnkNmkeVGqyqK3sx/VYSPOZsbq6x00Vs14bdk3eUoXtd9Jr1SDQvt7ZNA==',
            'from_email': 'noreply@jeyarama.com'
        },
        {
            'name': 'Alternative Config 1',
            'host': 'smtp.zeptomail.in',
            'port': 587,
            'username': 'noreply@jeyarama.com',  # Try using email as username
            'password': 'PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETQPXOy44+tLqZs+uGJmnkNmkeVGqyqK3sx/VYSPOZsbq6x00Vs14bdk3eUoXtd9Jr1SDQvt7ZNA==',
            'from_email': 'noreply@jeyarama.com'
        },
        {
            'name': 'Alternative Config 2 (Port 465)',
            'host': 'smtp.zeptomail.in',
            'port': 465,
            'username': 'emailapikey',
            'password': 'PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETQPXOy44+tLqZs+uGJmnkNmkeVGqyqK3sx/VYSPOZsbq6x00Vs14bdk3eUoXtd9Jr1SDQvt7ZNA==',
            'from_email': 'noreply@jeyarama.com'
        }
    ]
    
    to_email = 'jerish@jcrc.in'
    
    for config in configs:
        print(f"\n🧪 Testing: {config['name']}")
        print(f"Host: {config['host']}:{config['port']}")
        print(f"Username: {config['username']}")
        print(f"From: {config['from_email']}")
        
        try:
            msg = EmailMessage()
            msg['Subject'] = f"Test Email - {config['name']}"
            msg['From'] = config['from_email']
            msg['To'] = to_email
            msg.set_content(f"This is a test email using {config['name']} configuration.")
            
            if config['port'] == 465:
                # SSL connection
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(config['host'], config['port'], context=context) as server:
                    server.login(config['username'], config['password'])
                    server.send_message(msg)
            else:
                # TLS connection
                context = ssl.create_default_context()
                # Disable certificate verification for testing
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with smtplib.SMTP(config['host'], config['port']) as server:
                    server.starttls(context=context)
                    server.login(config['username'], config['password'])
                    server.send_message(msg)
            
            print("✅ SUCCESS!")
            return config  # Return the working config
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
    
    print("\n❌ All configurations failed!")
    return None

def test_network_connectivity():
    """Test if we can reach the SMTP server"""
    import socket
    
    print("🌐 Testing network connectivity...")
    
    hosts_ports = [
        ('smtp.zeptomail.in', 587),
        ('smtp.zeptomail.in', 465),
        ('smtp.zeptomail.in', 25),
    ]
    
    for host, port in hosts_ports:
        try:
            socket.create_connection((host, port), timeout=10)
            print(f"✅ Can connect to {host}:{port}")
        except Exception as e:
            print(f"❌ Cannot connect to {host}:{port} - {e}")

if __name__ == "__main__":
    print("🔧 SMTP Configuration Tester")
    print("=" * 50)
    
    # Test network first
    test_network_connectivity()
    print()
    
    # Test different SMTP configs
    working_config = test_smtp_variations()
    
    if working_config:
        print(f"\n🎉 Found working configuration: {working_config['name']}")
        print("\nUpdate your Django settings.py with:")
        print(f"EMAIL_HOST = '{working_config['host']}'")
        print(f"EMAIL_PORT = {working_config['port']}")
        print(f"EMAIL_HOST_USER = '{working_config['username']}'")
        print(f"EMAIL_HOST_PASSWORD = '{working_config['password']}'")
        print(f"DEFAULT_FROM_EMAIL = '{working_config['from_email']}'")
        
        if working_config['port'] == 465:
            print("EMAIL_USE_SSL = True")
            print("EMAIL_USE_TLS = False")
        else:
            print("EMAIL_USE_TLS = True")
            print("EMAIL_USE_SSL = False")
