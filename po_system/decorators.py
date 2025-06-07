from functools import wraps
from django.conf import settings

# Set to store exempt views
login_exempt_views = set()

def login_exempt(view_func):
    """
    Decorator to mark a view function as exempt from login requirements.
    
    Usage:
        @login_exempt
        def my_public_view(request):
            # This view will be accessible without login
            return render(request, 'template.html')
    """
    login_exempt_views.add(view_func.__module__ + '.' + view_func.__name__)
    
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)
    
    return wrapped_view

def is_exempt(view_func):
    """
    Check if a view function is exempt from login requirements.
    
    Args:
        view_func: The view function to check
        
    Returns:
        bool: True if the view is exempt, False otherwise
    """
    if hasattr(view_func, '__module__') and hasattr(view_func, '__name__'):
        view_path = view_func.__module__ + '.' + view_func.__name__
        return view_path in login_exempt_views
    
    return False

# For class-based views
class LoginExemptMixin:
    """
    Mixin to mark a class-based view as exempt from login requirements.
    
    Usage:
        class MyPublicView(LoginExemptMixin, TemplateView):
            template_name = 'template.html'
    """
    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        # Mark the view as exempt
        login_exempt_views.add(cls.__module__ + '.' + cls.__name__)
        return view
