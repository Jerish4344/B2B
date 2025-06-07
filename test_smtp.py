import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'po_management.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_smtp():
    try:
        send_mail(
            subject='Test Email from Django',
            message='This is a test email to verify SMTP configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['jerish220@gmail.com'],  # Change to your email
            fail_silently=False,
        )
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_smtp()