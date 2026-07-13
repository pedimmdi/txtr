# txtr

A minimal, Twitter-like social network built with Django and Django REST Framework. Text-only posts, real-time notifications, direct messaging, and a clean dark-themed UI.

---

## Features

- **Authentication** — JWT-based register, login, logout, and token refresh
- **Profiles** — Custom user model with profile picture and bio
- **Follow System** — Follow/unfollow users, view followers and following lists
- **Posts** — Create, edit, delete text posts (up to 1000 characters)
- **Feed** — Personalized home feed from followed users
- **Likes** — Like/unlike posts and comments
- **Bookmarks** — Save posts for later
- **Reposts** — Pure repost and quote repost (like Retweet / Quote Tweet)
- **Comments** — Nested comments with one level of replies
- **Hashtags** — Auto-extracted from post content via regex
- **Mentions** — @username mentions trigger notifications (on create and update)
- **Notifications** — Real-time-ready notifications for likes, comments, replies, follows, reposts, and mentions
- **Direct Messages** — Private conversations between two users
- **Search** — Full-text search on posts and username search
- **Ordering** — Sort posts by date or like count
- **Throttling** — Rate limiting on sensitive endpoints (login, register, post creation, likes)
- **Pagination** — Page-based pagination across all list endpoints

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, Django 5.x |
| API | Django REST Framework |
| Auth | djangorestframework-simplejwt |
| Environment | django-environ |
| Database | SQLite (dev) / PostgreSQL (prod-ready) |

---

## Project Structure

```
txtr/
├── core/
│   ├── core/               ← Django settings, root URLs
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── pagination.py
│   │   └── throttles.py
│   ├── accounts/           ← Custom user, profiles, follow system
│   ├── posts/              ← Posts, likes, bookmarks, reposts
│   ├── comments/           ← Comments, replies, comment likes
│   ├── hashtags/           ← Hashtag extraction and search
│   ├── notifications/      ← Notification system via signals
│   └── direct_messages/    ← Private messaging
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/pedimmdi/txtr.git
cd txtr

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and fill in your SECRET_KEY and DEBUG values

# 5. Apply migrations
cd core
python manage.py migrate

# 6. Create a superuser (optional)
python manage.py createsuperuser

# 7. Run the development server
python manage.py runserver
```

### Environment Variables

Create a `.env` file in the `core/` directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
```

---

## API Reference

All endpoints are prefixed with `/api/v1/`.

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/accounts/register/` | Register a new user | No |
| POST | `/accounts/login/` | Login and receive JWT tokens | No |
| POST | `/accounts/logout/` | Blacklist refresh token | Yes |
| POST | `/api/token/refresh/` | Refresh access token | No |

### Profiles

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET / PATCH | `/accounts/profile/` | View or update own profile | Yes |
| GET | `/accounts/profile/<username>/` | View any user's profile | No |
| POST | `/accounts/follow/<username>/` | Follow or unfollow a user | Yes |
| GET | `/accounts/users/` | Search users by username | No |
| GET | `/accounts/<username>/followers/` | List followers | No |
| GET | `/accounts/<username>/following/` | List following | No |

### Posts

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/posts/` | List all posts | No |
| POST | `/posts/` | Create a post | Yes |
| GET | `/posts/feed/` | Home feed | Yes |
| GET | `/posts/bookmarks/` | Bookmarked posts | Yes |
| GET | `/posts/<pk>/` | Post detail | No |
| PUT / PATCH | `/posts/<pk>/` | Edit a post | Yes (author) |
| DELETE | `/posts/<pk>/` | Delete a post | Yes (author) |
| POST | `/posts/<pk>/like/` | Like / unlike | Yes |
| POST | `/posts/<pk>/bookmark/` | Bookmark / unbookmark | Yes |
| POST | `/posts/<pk>/repost/` | Repost / undo repost | Yes |
| POST | `/posts/<pk>/quote/` | Quote repost | Yes |
| GET | `/posts/users/<username>/` | User's post timeline | No |

### Comments

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/posts/<post_pk>/comments/` | List comments | No |
| POST | `/posts/<post_pk>/comments/` | Add a comment | Yes |
| GET / PATCH / DELETE | `/posts/<post_pk>/comments/<pk>/` | Comment detail | No / Yes (author) |
| GET | `/posts/<post_pk>/comments/<pk>/replies/` | List replies | No |
| POST | `/posts/<post_pk>/comments/<pk>/replies/` | Add a reply | Yes |
| POST | `/posts/<post_pk>/comments/<pk>/like/` | Like / unlike comment | Yes |

### Hashtags

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/hashtags/` | List all hashtags (trending first) | No |
| GET | `/hashtags/<name>/posts/` | Posts with a specific hashtag | No |

### Notifications

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/notifications/` | List notifications (unread first) | Yes |
| GET | `/notifications/unread-count/` | Count of unread notifications | Yes |
| POST | `/notifications/<pk>/read/` | Mark one as read | Yes |
| POST | `/notifications/read-all/` | Mark all as read | Yes |

### Direct Messages

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| GET | `/dm/` | List all conversations | Yes |
| GET | `/dm/<username>/` | View messages with a user | Yes |
| POST | `/dm/<username>/` | Send a message | Yes |
| DELETE | `/dm/<username>/<msg_pk>/` | Delete a message | Yes (sender) |

### Filters

Most list endpoints support:

```
?search=<text>              # full-text search
?ordering=created_date      # sort ascending
?ordering=-created_date     # sort descending (default)
?ordering=-likes_count      # sort by popularity
?page=2                     # pagination
?page_size=20               # custom page size
```

---

## Throttling

| Endpoint | Limit |
|---|---|
| Login / Register | 5 requests / minute |
| Post creation | 20 requests / hour |
| Like / Unlike | 60 requests / minute |
| Follow / Unfollow | 30 requests / minute |
| Comment creation | 30 requests / hour |
| Authenticated users | 1000 requests / hour |
| Anonymous users | 100 requests / hour |

---

## License

This project is open source and available under the [MIT License](LICENSE).