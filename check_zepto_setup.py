# check_zepto_setup.py - Check your Zepto Mail domain configuration

import requests
import json

def check_zepto_mail_domain():
    """
    Check what domains and emails are configured in your Zepto Mail account
    """
    api_key = "Zoho-enczapikey PHtE6r0PFuvsijYvoxIG5KLrRJalY9soruIzLQhA4o1GWKNWSU1cr48ow2WzqBwjUvETQPXOy44+tLqZs+uGJmnkNmkeVGqyqK3sx/VYSPOZsbq6x00Vs14bdk3eUoXtd9Jr1SDQvt7ZNA=="
    
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Zoho-enczapikey {api_key}',
    }
    
    print("🔍 Checking Zepto Mail Domain Configuration...")
    print("=" * 50)
    
    try:
        # Check domains
        print("📋 Checking domains...")
        response = requests.get(
            'https://api.zeptomail.in/v1.1/domains',
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Key is valid!")
            
            if 'data' in data:
                domains = data['data']
                print(f"\n📧 Found {len(domains)} domain(s):")
                
                for domain in domains:
                    print(f"\nDomain: {domain.get('domain_name', 'Unknown')}")
                    print(f"Status: {domain.get('domain_status', 'Unknown')}")
                    print(f"Verified: {domain.get('is_verified', False)}")
                    
                    # Check for verified emails in this domain
                    if 'from_email_addresses' in domain:
                        emails = domain['from_email_addresses']
                        print(f"Verified Emails: {len(emails)}")
                        for email in emails:
                            print(f"  - {email}")
            else:
                print("❌ No domains found in your account")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error checking domains: {e}")

if __name__ == "__main__":
    check_zepto_mail_domain()
