from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from accounts.forms import RegisterForm, LoginForm
from accounts.models import User, Profile


def register_view(request):
    """Template-based registration with session login."""
    if request.user.is_authenticated:
        return redirect('feed')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = User(email=form.cleaned_data['email'])
        user.set_password(form.cleaned_data['password1'])
        user.save()

        # Profile auto-created via signal — just set the username
        Profile.objects.filter(user=user).update(
            username=form.cleaned_data['username']
        )

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f"Welcome to txtr, {form.cleaned_data['username']}!")
        return redirect('feed')

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Template-based login with session auth."""
    if request.user.is_authenticated:
        return redirect('feed')

    form = LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # form.user is set inside LoginForm.clean() after authenticate()
        login(request, form.user, backend='django.contrib.auth.backends.ModelBackend')

        # Respect ?next= redirect parameter (e.g., from login_required decorator)
        next_url = request.POST.get('next') or request.GET.get('next') or 'feed'
        return redirect(next_url)

    return render(request, 'accounts/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def logout_view(request):
    """Log out and redirect to login page."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'You have been logged out.')
    return redirect('login')
