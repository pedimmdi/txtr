from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """
    Strict throttle for login and register endpoints.
    Applied per IP address (unauthenticated context).
    """
    scope = 'auth'


class PostCreateRateThrottle(UserRateThrottle):
    """Throttle for post creation — prevents spam posts."""
    scope = 'post_create'


class LikeRateThrottle(UserRateThrottle):
    """Throttle for like/unlike actions."""
    scope = 'likes'


class FollowRateThrottle(UserRateThrottle):
    """Throttle for follow/unfollow actions."""
    scope = 'follows'


class CommentCreateRateThrottle(UserRateThrottle):
    """Throttle for comment and reply creation."""
    scope = 'comment_create'