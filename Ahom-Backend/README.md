# Events Platform — Django Backend

A small **events** backend with JWT auth, RBAC (Seeker / Facilitator), email OTP verification, event search, and enrollment management.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 + Django REST Framework |
| Auth | `djangorestframework-simplejwt` (JWT access + refresh) |
| Database | PostgreSQL 15 |
| Task Queue | Celery + Redis + django-celery-beat |
| Containerisation | Docker & Docker Compose |

---

## Quick Start (Docker)

```bash
# 1. Clone & cd into the project
cd "Ahom-Backend"

# 2. Copy env file (defaults work out of the box for Docker)
cp .env.example .env   # or use the included .env

# 3. Build & start all services
docker compose up --build -d

# 4. Run migrations (auto-runs on web start, but just in case)
docker compose exec web python manage.py migrate

# 5. Create a superuser (optional)
docker compose exec web python manage.py createsuperuser

# The API is now live at http://localhost:8000
```

### Running Tests

```bash
docker compose exec web python manage.py test
```

### Without Docker (local venv)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Point DB_HOST to your local Postgres, or use SQLite for quick tests:
# In .env set: DB_HOST=localhost

export DJANGO_SETTINGS_MODULE=config.settings
python manage.py migrate
python manage.py test
python manage.py runserver
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `insecure-dev-key…` | Django secret key |
| `DEBUG` | `True` | Debug mode |
| `ALLOWED_HOSTS` | `*` | Comma-separated hosts |
| `DB_NAME` | `events_db` | PostgreSQL database name |
| `DB_USER` | `postgres` | DB user |
| `DB_PASSWORD` | `postgres` | DB password |
| `DB_HOST` | `db` | DB host (`db` for Docker, `localhost` otherwise) |
| `DB_PORT` | `5432` | DB port |
| `REDIS_URL` | `redis://redis:6379/0` | Redis URL for Celery |
| `EMAIL_BACKEND` | `console` backend | Switch to SMTP for real emails |
| `ACCESS_TOKEN_LIFETIME_MINUTES` | `30` | JWT access token lifetime |
| `REFRESH_TOKEN_LIFETIME_MINUTES` | `1440` | JWT refresh token lifetime (24 h) |

---

## API Endpoints

### Auth (`/auth/`)

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/auth/signup/` | Register (email, password, role) | No |
| POST | `/auth/verify-email/` | Verify email with OTP | No |
| POST | `/auth/resend-otp/` | Resend OTP | No |
| POST | `/auth/login/` | Login → JWT pair | No |
| POST | `/auth/refresh/` | Rotate refresh token | No |

### Seeker (`/api/`)

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/events/search/` | Search & filter events | Seeker / Facilitator |
| POST | `/api/enrollments/enroll/` | Enroll in an event | Seeker |
| POST | `/api/enrollments/<id>/cancel/` | Cancel enrollment | Seeker (owner) |
| GET | `/api/enrollments/upcoming/` | My upcoming enrollments | Seeker |
| GET | `/api/enrollments/past/` | My past enrollments | Seeker |

#### Search Query Parameters

- `q` — full-text search on title & description
- `location` — case-insensitive contains
- `language` — exact match (case-insensitive)
- `starts_after` — ISO datetime
- `starts_before` — ISO datetime
- `ordering` — `starts_at` (default), `-starts_at`, `created_at`
- `page`, `page_size` — pagination

### Facilitator (`/api/facilitator/`)

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/facilitator/events/` | List my events (with counts) | Facilitator |
| POST | `/api/facilitator/events/` | Create event | Facilitator |
| GET | `/api/facilitator/events/<id>/` | Event detail | Facilitator (owner) |
| PATCH | `/api/facilitator/events/<id>/` | Update event | Facilitator (owner) |
| DELETE | `/api/facilitator/events/<id>/` | Delete event | Facilitator (owner) |

---

## Design Decisions & Trade-offs

### 1. Default User Model + OneToOne Profile
The spec requires using Django's built-in `User` model. A `UserProfile` with a OneToOneField stores `role` and `is_email_verified`. This avoids touching `AUTH_USER_MODEL` while still supporting RBAC cleanly.

### 2. Email as Username
Signup only accepts `email` — internally we set `username = email` since the default User model requires a username. This is transparent to the API consumer.

### 3. OTP Verification
- 6-digit numeric OTP stored in `EmailOTP` with a configurable TTL (default 5 min).
- Max 5 verification attempts per OTP to prevent brute-forcing.
- In dev mode, OTPs print to the console (console email backend). Switch `EMAIL_BACKEND` to an SMTP backend for production.

### 4. RBAC via DRF Permissions
Custom permission classes (`IsSeeker`, `IsFacilitator`, `IsEmailVerified`) keep authorization logic declarative and composable at the view level. Ownership is enforced by filtering querysets to `created_by=request.user`.

### 5. Enrollment Uniqueness
A partial unique constraint (`unique_active_enrollment`) prevents duplicate active enrollments while still allowing re-enrollment after cancellation (the canceled row remains; a new `enrolled` row can be created).

### 6. Capacity Enforcement
Capacity is checked via an annotated count at enroll time. The unique constraint acts as a second safety net at the DB level to prevent race-condition duplicates.

### 7. Celery Beat for Scheduled Emails
Two periodic tasks run every 5 minutes:
- **Follow-up**: emails seekers who enrolled ~1 hour ago.
- **Reminder**: emails seekers ~1 hour before their event starts.
Both use boolean flags (`followup_sent`, `reminder_sent`) to ensure at-most-once delivery.

### 8. Pagination & Error Format
All list endpoints return `{ count, next, previous, results }`. All errors follow `{ detail, code }` via a custom exception handler.

---

## Postman Collection

Import `postman_collection.json` into Postman. It includes collection variables (`base_url`, `access_token`, `refresh_token`) and auto-extracts tokens on login/refresh.

---

## Project Structure

```
├── config/             # Django project settings, URLs, WSGI, Celery
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── pagination.py
│   └── exceptions.py
├── accounts/           # Auth app: signup, OTP, login, RBAC
│   ├── models.py       # UserProfile, EmailOTP
│   ├── serializers.py
│   ├── views.py
│   ├── permissions.py  # IsSeeker, IsFacilitator, IsEmailVerified
│   ├── urls.py
│   └── tests.py
├── events/             # Events + Enrollments app
│   ├── models.py       # Event, Enrollment
│   ├── serializers.py
│   ├── views.py        # Seeker + Facilitator endpoints
│   ├── filters.py      # EventFilter (django-filter)
│   ├── tasks.py        # Celery tasks (follow-up, reminder)
│   ├── urls.py
│   └── tests.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── postman_collection.json
└── README.md
```
