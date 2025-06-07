from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.conf import settings
from django.contrib import messages

from .decorators import login_exempt_views

class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to view any page other
    than those explicitly exempted using the login_exempt decorator.
    
    If the user is not authenticated, they will be redirected to the login page.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # List of URL names that should be accessible without login
        self.exempt_urls = [
            'po_system:login',
            'po_system:register',
            'admin:login',
        ]

    def __call__(self, request):
        # Get the view function for the current request
        resolver = resolve(request.path_info)
        view_func = resolver.func
        view_path = view_func.__module__ + '.' + view_func.__name__
        
        # Check if the user is authenticated or if the view is exempt
        if not request.user.is_authenticated:
            # Check if the current URL is exempt
            current_url_name = resolver.view_name
            
            if (view_path in login_exempt_views or 
                current_url_name in self.exempt_urls or
                request.path_info.startswith('/admin/') or
                request.path_info.startswith('/static/') or
                request.path_info.startswith('/media/')):
                # Allow access to exempt views
                return self.get_response(request)
            else:
                # Redirect to login page with next parameter
                login_url = reverse('po_system:login')
                next_url = request.path_info
                redirect_url = f"{login_url}?next={next_url}"
                
                # Add a message to inform the user
                messages.info(request, "Please log in to access this page.")
                
                return redirect(redirect_url)
        
        # User is authenticated, proceed normally
        return self.get_response(request)
