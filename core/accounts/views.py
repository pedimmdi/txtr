import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from accounts.forms import RegisterForm, LoginForm
from accounts.models import User, Profile, Follow
from posts.models import Post, Like
from posts.api.v1.views import get_annotated_posts


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



def profile_view(request, username):
    """Public profile page with posts, reposts, and likes tabs."""
    profile        = get_object_or_404(Profile, username=username)
    is_own_profile = request.user.is_authenticated and request.user == profile.user

    is_following = (
        request.user.is_authenticated and
        Follow.objects.filter(follower=request.user, following=profile.user).exists()
    )

    follows_you = False
    if request.user.is_authenticated and not is_own_profile:
        follows_you = Follow.objects.filter(
            follower=profile.user,
            following=request.user
        ).exists()

    # Posts tab — excludes reposts
    posts_qs    = get_annotated_posts(request.user).filter(
        author=profile.user, original_post=None
    )
    paginator   = Paginator(posts_qs, 20)
    posts       = paginator.get_page(request.GET.get('page', 1))
    posts_count = Post.objects.filter(author=profile.user, original_post=None).count()

    # Reposts tab
    reposts = get_annotated_posts(request.user).filter(
        author=profile.user, original_post__isnull=False
    )

    # Likes tab
    liked_ids   = Like.objects.filter(user=profile.user).values_list('post_id', flat=True)
    liked_posts = get_annotated_posts(request.user).filter(id__in=liked_ids)

    followers_count = Follow.objects.filter(following=profile.user).count()
    following_count = Follow.objects.filter(follower=profile.user).count()

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'is_own_profile': is_own_profile,
        'is_following': is_following,
        'follows_you': follows_you,
        'posts': posts,
        'posts_count': posts_count,
        'reposts': reposts,
        'liked_posts': liked_posts,
        'followers_count': followers_count,
        'following_count': following_count,
    })


@login_required
def profile_edit_view(request):
    """Handle edit profile form submission."""
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        bio      = request.POST.get('bio', '').strip()
        image    = request.FILES.get('image')

        if username and re.match(r'^\w+$', username):
            if Profile.objects.filter(username=username).exclude(pk=profile.pk).exists():
                messages.error(request, 'Username is already taken.')
                return redirect('profile', username=profile.username)
            profile.username = username

        profile.bio = bio[:200]
        if image:
            profile.image = image
        profile.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile', username=profile.username)

    return redirect('profile', username=profile.username)
