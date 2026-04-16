# Sessions Marketplace

A full-stack web application where users can sign in via OAuth, browse sessions, and book them. Creators can create and manage sessions with a dedicated dashboard.

## Tech Stack

| Layer          | Technology                              |
| -------------- | --------------------------------------- |
| Frontend       | React 18 + Vite + Tailwind CSS         |
| Backend        | Django 5.1 + Django REST Framework      |
| Database       | PostgreSQL 16                           |
| Auth           | Google / GitHub OAuth → JWT (SimpleJWT) |
| Payments       | Stripe (test mode, optional)            |
| Infrastructure | Docker Compose + Nginx reverse proxy    |

## Architecture

```
┌──────────────────────────────────────────────────┐
│                    Nginx (:80)                    │
│      /api/* → backend   /* → frontend            │
├────────────────────┬─────────────────────────────┤
│  Frontend (:3000)  │    Backend (:8000)           │
│  React + Vite      │    Django + DRF + Gunicorn   │
│  (serve static)    │                              │
└────────────────────┴──────────┬──────────────────┘
                                │
                       PostgreSQL (:5432)
```

## Quick Start

### 1. Clone the repository

```bash
git clone <repo-url>
cd sessions-marketplace
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `DJANGO_SECRET_KEY` – any random string (50+ chars)
- `POSTGRES_PASSWORD` – a strong database password
- OAuth credentials (see below)

### 3. Start with Docker

```bash
docker-compose up --build
```

The app will be available at **http://localhost**.

## OAuth Client Setup

### Google OAuth

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create a new **OAuth 2.0 Client ID** (Web application)
3. Add **Authorized JavaScript origins**: `http://localhost`
4. Add **Authorized redirect URIs**: `http://localhost/auth/callback`
5. Copy the Client ID and Client Secret to `.env`:
   ```
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-client-secret
   VITE_GOOGLE_CLIENT_ID=your-client-id
   ```

### GitHub OAuth

1. Go to [GitHub → Settings → Developer settings → OAuth Apps](https://github.com/settings/developers)
2. Create a new OAuth App
3. Set **Homepage URL**: `http://localhost`
4. Set **Authorization callback URL**: `http://localhost/auth/callback`
5. Copy the Client ID and Client Secret to `.env`:
   ```
   GITHUB_CLIENT_ID=your-client-id
   GITHUB_CLIENT_SECRET=your-client-secret
   VITE_GITHUB_CLIENT_ID=your-client-id
   ```

## Demo Flow

### As a User (browse & book):

1. Visit **http://localhost** → see the public session catalog
2. Click **Sign In** → authenticate via Google or GitHub
3. Browse sessions and click on one to see details
4. Click **Book Now** to book a free session (or pay via Stripe for paid ones)
5. Go to **Dashboard** to see your active and past bookings
6. Cancel a booking from the dashboard if needed

### As a Creator (create & manage):

1. Sign in, then go to **Profile** → change your role to **Creator**
2. The **Creator** link appears in the navbar — click it
3. Click **New Session** → fill in title, description, date, price, etc.
4. The session appears in the public catalog for users to book
5. View all bookings for your sessions in the **Bookings** tab

## API Endpoints

### Authentication
| Method | Endpoint                   | Description                    |
| ------ | -------------------------- | ------------------------------ |
| POST   | `/api/auth/google/`        | Exchange Google code for JWT   |
| POST   | `/api/auth/github/`        | Exchange GitHub code for JWT   |
| POST   | `/api/auth/token/refresh/` | Refresh JWT access token       |
| GET    | `/api/auth/profile/`       | Get current user profile       |
| PATCH  | `/api/auth/profile/`       | Update profile (name, role...) |

### Sessions
| Method | Endpoint              | Description                        |
| ------ | --------------------- | ---------------------------------- |
| GET    | `/api/sessions/`      | List published sessions (public)   |
| POST   | `/api/sessions/`      | Create session (creator only)      |
| GET    | `/api/sessions/:id/`  | Session detail                     |
| PATCH  | `/api/sessions/:id/`  | Update session (owner only)        |
| DELETE | `/api/sessions/:id/`  | Delete session (owner only)        |
| GET    | `/api/sessions/mine/` | List current creator's sessions    |

### Bookings
| Method | Endpoint                | Description                          |
| ------ | ----------------------- | ------------------------------------ |
| GET    | `/api/bookings/`        | List current user's bookings         |
| POST   | `/api/bookings/`        | Create a booking                     |
| GET    | `/api/bookings/:id/`    | Booking detail                       |
| DELETE | `/api/bookings/:id/`    | Cancel a booking                     |
| GET    | `/api/bookings/creator/`| List bookings for creator's sessions |

### Payments (Bonus)
| Method | Endpoint                | Description                      |
| ------ | ----------------------- | -------------------------------- |
| POST   | `/api/payments/checkout/` | Create Stripe checkout session |
| POST   | `/api/payments/webhook/`  | Stripe webhook handler         |

## Bonus Features

- **Stripe Integration**: Set `STRIPE_SECRET_KEY` and `STRIPE_PUBLIC_KEY` in `.env` to enable paid sessions with Stripe Checkout (test mode)
- **Rate Limiting**: Auth and booking endpoints are rate-limited (20 req/min for auth, 10 req/min for bookings) via `django-ratelimit`
- **Role-based Access Control**: Creator-only endpoints are enforced both in the backend (permissions) and frontend (route guards)

## Project Structure

```
├── docker-compose.yml          # Multi-container orchestration
├── .env.example                # Environment variable template
├── nginx/
│   └── default.conf            # Reverse proxy configuration
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── config/                 # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── apps/
│       ├── accounts/           # User model, OAuth, JWT, profile
│       ├── sessions_app/       # Session CRUD
│       ├── bookings/           # Booking logic
│       └── payments/           # Stripe integration
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── api.js              # Axios client with JWT interceptor
        ├── context/AuthContext  # Auth state management
        ├── components/         # Navbar, SessionCard, etc.
        └── pages/              # Home, Login, Dashboard, etc.
```

## Development (without Docker)

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgres://user:pass@localhost:5432/sessions_marketplace
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```
