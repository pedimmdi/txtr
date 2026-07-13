# posts/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from accounts.models import Profile, Follow
from posts.api.v1.views import get_annotated_posts
from hashtags.models import Hashtag


@login_required
def feed_view(request):
    """Home feed: own posts + posts from followed users."""
    following_ids = Follow.objects.filter(
        follower=request.user
    ).values_list('following_id', flat=True)

    posts_qs = get_annotated_posts(request.user).filter(
        author_id__in=list(following_ids) + [request.user.id]
    )

    paginator = Paginator(posts_qs, 20)
    posts     = paginator.get_page(request.GET.get('page', 1))

    trending_hashtags = Hashtag.objects.annotate(
        posts_count=Count('posts')
    ).order_by('-posts_count')[:5]

    # Suggest users the current user doesn't follow yet
    suggested_users = (
        Profile.objects
        .exclude(user=request.user)
        .exclude(user_id__in=list(following_ids))
        .select_related('user')
        .order_by('?')[:3]
    )

    return render(request, 'posts/feed.html', {
        'posts':             posts,
        'trending_hashtags': trending_hashtags,
        'suggested_users':   suggested_users,
    })
