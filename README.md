# FlowPro Plumbing Django App

Mobile-first Django website and booking enquiry flow for a premium local plumbing business.

## Local Setup

Create and activate a virtual environment, then install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a PostgreSQL database:

```sql
sudo -u postgres psql
CREATE DATABASE flowpro_db;
CREATE USER flowpro_user WITH PASSWORD 'change-me';
ALTER ROLE flowpro_user SET client_encoding TO 'utf8';
ALTER ROLE flowpro_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE flowpro_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE flowpro_db TO flowpro_user;
```

Copy `.env.example` to `.env` and set at least:

```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
DATABASE_URL=postgres://flowpro_user:change-me@localhost:5432/flowpro_db
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=website@example.com
ADMIN_NOTIFICATION_EMAIL=owner@example.com
```

Run migrations and create an admin user:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Start the site:

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the landing page and `http://127.0.0.1:8000/admin/` for enquiry management.

## Email

Development defaults to the console email backend when configured in `.env`. For production SMTP, set:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

Booking submissions are saved even if notification email delivery fails.

## Cloning for a New Client

This project is wired so a cloned copy can be reused for another trades client without editing templates for normal content changes.

After cloning and running migrations:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Open Django Admin and edit `Trades > Business profiles`.

The active business profile controls:

- Business name and split logo text
- Meta description
- Hero badge, headline, and body copy
- Phone number, telephone link, email, and service area
- Footer tagline and disclaimer
- Services section title/subtitle
- Booking section title/subtitle
- Reviews section title/subtitle
- Owner/about section copy
- Optional hero, services, about, and booking images

Inside the same Business Profile edit screen, use the inline tables to manage:

- Trust indicators
- Service cards
- Testimonials

Keep only one profile active for a single-client deployment. To prepare a new client, clone the repository, configure a new `.env`, run migrations against that client database, and edit or replace the seeded `FlowPro Plumbing` profile from Admin.

Uploaded client images are stored under `MEDIA_ROOT` and served from `MEDIA_URL`. Bundled placeholder images stay in `trades/static/trades/images/` and are collected by `collectstatic`.

## Checks

```bash
python manage.py check
python manage.py makemigrations --check
python manage.py test
```

If PostgreSQL is unavailable and you only need to run tests locally, temporarily override `DATABASE_URL` for the command:

```bash
DATABASE_URL=sqlite:///:memory: python manage.py test
```
