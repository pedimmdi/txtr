"""
Project-level views that do not belong to a specific app.
"""
from django.shortcuts import redirect


def root_redirect(request):
    """
    Redirect the site root to the appropriate landing page.
    Authenticated users go to their feed; guests go to login.
    """
    if request.user.is_authenticated:
        return redirect('feed')
    return redirect('login')
