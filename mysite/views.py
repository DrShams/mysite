from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse

def custom_logout_view(request):
    """Custom logout view that supports both GET and POST methods."""
    if request.user.is_authenticated:
        logout(request)
    return redirect(reverse('ads:all'))  # Redirect to ads page after logout
