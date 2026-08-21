# txtr

[![Tests](https://github.com/pedimmdi/txtr/actions/workflows/tests.yml/badge.svg)](https://github.com/pedimmdi/txtr/actions/workflows/tests.yml)

A Twitter-like social network built with **Django**, **Django REST Framework**, and **Django Channels**. Text-only posts, follows, likes, bookmarks, reposts, comments, hashtags, notifications, and direct messages — with a dark-themed template UI and realtime delivery over WebSockets.

---

## Features

- **Authentication** — JWT register/login/logout + session auth for the UI
- **Profiles** — Custom user model, avatar, bio, public profiles
- **Follow system** — Follow/unfollow with follower/following lists
- **Posts** — Create/edit/delete text posts (up to 1000 characters)
- **Home feed** — Posts from people you follow (+ your own)
- **Explore** — Public post stream, search, trending hashtags, suggestions
- **Likes & bookmarks** — Toggle APIs and UI without full page reloads
- **Reposts** — Pure repost and quote repost
- **Comments** — Top-level comments + one level of replies + comment likes
- **Hashtags & mentions** — Extracted from content; mentions create notifications
- **Notifications** — Likes, comments, replies, follows, reposts, mentions; **live unread badge via WebSocket**
- **Direct messages** — Conversations, reply quotes, forward post to DM; **live delivery via WebSocket**
- **Search / ordering / pagination / throttling** — Across list APIs

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12+, Django 5.x |
| API | Django REST Framework + SimpleJWT |
| Realtime | Django Channels + Redis channel layer |
| Cache | django-redis (Redis) / LocMem fallback |
| Database | SQLite (simple local) or PostgreSQL (Docker / recommended) |
| Config | django-environ |
| Tests | pytest, pytest-django, pytest-cov |
| CI | GitHub Actions |
| Containers | Docker Compose (web + Postgres + Redis) |

---

## Project structure

```text
txtr/
├── core/                      # Django project root (manage.py lives here)
│   ├── core/                  # settings, urls, asgi, consumers, pagination
│   ├── accounts/
│   ├── posts/
│   ├── comments/
│   ├── hashtags/
│   ├── notifications/
│   ├── direct_messages/
│   ├── templates/
│   ├── static/
│   ├── tests/                 # smoke + shared fixtures
│   ├── .env.example
│   └── pytest.ini
├── .github/workflows/tests.yml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Getting started

### Option A — Local (SQLite)

```bash
git clone https://github.com/pedimmdi/txtr.git
cd txtr

python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate

pip install -r requirements.txt

cp core/.env.example core/.env
# Set SECRET_KEY (and DEBUG/ALLOWED_HOSTS as needed)

cd core
python manage.py migrate
python manage.py createsuperuser   # optional
python manage.py runserver
```

Open http://127.0.0.1:8000/

Without `DATABASE_URL` / `REDIS_URL`, the app uses **SQLite** and **LocMem** cache. Channels falls back to an in-memory channel layer (fine for single-process dev).

### Option B — Docker Compose (PostgreSQL + Redis)

Requires Docker Desktop (or Docker Engine + Compose).

```bash
git clone https://github.com/pedimmdi/txtr.git
cd txtr

cp core/.env.example core/.env
# Set at least SECRET_KEY in core/.env

docker compose up --build
```

Services:

| Service | Role |
|---|---|
| `web` | Django on port 8000 (migrate on start) |
| `db` | PostgreSQL 16 |
| `redis` | Redis 7 (cache + Channels) |

Compose injects:

```text
DATABASE_URL=postgres://txtr:txtr@db:5432/txtr
REDIS_URL=redis://redis:6379/0
```

---

## Environment variables

Copy `core/.env.example` → `core/.env`:

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Django secret |
| `DEBUG` | Yes | `True` / `False` |
| `ALLOWED_HOSTS` | Yes | Comma-separated, e.g. `localhost,127.0.0.1,web` |
| `DATABASE_URL` | No | If set → Postgres (or other DB URL). Default → SQLite |
| `REDIS_URL` | No | If set → Redis cache + channel layer. Default → LocMem / InMemory |

---

## Realtime (WebSockets)

Authenticated browser sessions can connect to:

| Endpoint | Purpose |
|---|---|
| `ws://<host>/ws/dm/<username>/` | Live DM delivery for that conversation |
| `ws://<host>/ws/notifications/` | Live unread notification count |
| `ws://<host>/ws/ping/` | Connectivity check (`ping` → `pong`) |

**Design:** message **create/validation** stays on REST (`POST /api/v1/dm/...`). After save, the server `group_send`s to the shared DM room so open clients update without polling. Notification badges use a personal group `notifications_<user_id>`.

---

## Testing

```bash
cd core
pytest
```

- ~48 API tests across accounts, posts, comments, DMs, notifications, hashtags
- Coverage via **pytest-cov** (terminal report after each run)
- CI runs the same suite on every push/PR to `main`

---

## API overview

All HTTP APIs are under `/api/v1/`.

### Authentication

| Method | Endpoint | Auth |
|---|---|---|
| POST | `/accounts/register/` | No |
| POST | `/accounts/login/` | No |
| POST | `/accounts/logout/` | Yes |
| POST | `/api/token/refresh/` | No |

### Profiles & social

| Method | Endpoint | Auth |
|---|---|---|
| GET / PUT | `/accounts/profile/` | Yes |
| GET | `/accounts/users/<username>/` | No |
| POST | `/accounts/users/<username>/follow/` | Yes |
| GET | `/accounts/users/` | No |
| GET | `/accounts/users/<username>/followers/` | No |
| GET | `/accounts/users/<username>/following/` | No |

### Posts

| Method | Endpoint | Auth |
|---|---|---|
| GET / POST | `/posts/` | Read: no / Write: yes |
| GET | `/posts/feed/` | Yes |
| GET | `/posts/bookmarks/` | Yes |
| GET / PUT / PATCH / DELETE | `/posts/<pk>/` | Write: author |
| POST | `/posts/<pk>/like/` | Yes |
| POST | `/posts/<pk>/bookmark/` | Yes |
| POST | `/posts/<pk>/repost/` | Yes |
| POST | `/posts/<pk>/quote/` | Yes |
| GET | `/posts/users/<username>/` | No |

### Comments

| Method | Endpoint | Auth |
|---|---|---|
| GET / POST | `/posts/<post_pk>/comments/` | Write: yes |
| GET / PATCH / DELETE | `/posts/<post_pk>/comments/<pk>/` | Write: author |
| GET / POST | `/posts/<post_pk>/comments/<pk>/replies/` | Write: yes |
| POST | `/posts/<post_pk>/comments/<pk>/like/` | Yes |

### Hashtags / notifications / DMs

| Method | Endpoint | Auth |
|---|---|---|
| GET | `/hashtags/` | No |
| GET | `/hashtags/<name>/posts/` | No |
| GET | `/notifications/` | Yes |
| GET | `/notifications/unread-count/` | Yes |
| POST | `/notifications/<pk>/read/` | Yes |
| POST | `/notifications/read-all/` | Yes |
| GET | `/dm/` | Yes |
| GET / POST | `/dm/<username>/` | Yes |
| DELETE | `/dm/<username>/<pk>/` | Yes (sender) |

Common query params on list endpoints: `?search=`, `?ordering=`, `?page=`, `?page_size=`.

---

## Throttling (selected)

| Scope | Limit |
|---|---|
| Auth (login/register) | 5 / minute |
| Post create | 20 / hour |
| Likes | 60 / minute |
| Follows | 30 / minute |
| Comment create | 30 / hour |
| Authenticated user | 1000 / hour |
| Anonymous | 100 / hour |

---

## License

This project is open source and available under the [MIT License](LICENSE).
