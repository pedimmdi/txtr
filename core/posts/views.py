# posts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponseForbidden
from accounts.models import Profile, Follow
from posts.api.v1.views import get_annotated_posts
from posts.models import Post, Bookmark, Like
from hashtags.models import Hashtag


@login_required
def feed_view(request):
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


def post_detail_view(request, pk):
    post = get_object_or_404(get_annotated_posts(request.user), pk=pk)
    return render(request, 'posts/post_detail.html', {'post': post})


@login_required
def post_edit_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        return HttpResponseForbidden()
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content and len(content) <= 1000:
            post.content = content
            post.save()
            messages.success(request, 'Post updated.')
            return redirect('post-detail', pk=post.pk)
    return render(request, 'posts/post_edit.html', {'post': post})


@login_required
def bookmarks_view(request):
    bookmarked_ids = Bookmark.objects.filter(
        user=request.user
    ).order_by('-created_at').values_list('post_id', flat=True)
    posts_qs  = get_annotated_posts(request.user).filter(id__in=bookmarked_ids)
    paginator = Paginator(posts_qs, 20)
    posts     = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'posts/bookmarks.html', {'posts': posts})


def explore_view(request):
    query = request.GET.get('search', '').strip()
    posts = users = None

    if query:
        posts_qs  = get_annotated_posts(request.user).filter(content__icontains=query)
        paginator = Paginator(posts_qs, 20)
        posts     = paginator.get_page(request.GET.get('page', 1))
        users     = Profile.objects.filter(username__icontains=query).select_related('user')[:6]

    trending_hashtags = Hashtag.objects.annotate(
        posts_count=Count('posts')
    ).order_by('-posts_count')[:10]

    following_ids = []
    if request.user.is_authenticated:
        following_ids = list(
            Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
        )

    exclude_user = request.user if request.user.is_authenticated else None
    suggested_users = (
        Profile.objects
        .exclude(user=exclude_user)
        .exclude(user_id__in=following_ids)
        .select_related('user')
        .order_by('?')[:6]
    )

    return render(request, 'posts/explore.html', {
        'query':             query,
        'posts':             posts,
        'users':             users,
        'trending_hashtags': trending_hashtags,
        'suggested_users':   suggested_users,
    })


def hashtag_posts_view(request, name):
    hashtag   = get_object_or_404(Hashtag, name=name.lower())
    posts_qs  = get_annotated_posts(request.user).filter(hashtags=hashtag)
    paginator = Paginator(posts_qs, 20)
    posts     = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'posts/hashtag_posts.html', {
        'hashtag': hashtag,
        'posts':   posts,
    })
