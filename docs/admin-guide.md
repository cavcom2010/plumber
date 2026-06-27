# Admin Guide

This guide explains how to run the FlowPro plumbing/trades app from Django Admin and what backend features are available.

## Admin Access

Open the admin area:

```text
/admin/
```

Use the superuser created with:

```bash
python manage.py createsuperuser
```

The main admin areas are:

- `Business profiles`: client branding, contact details, copy, images, WhatsApp, service cards, trust indicators, and seeded testimonials.
- `Booking enquiries`: customer booking requests submitted from the website.
- `Testimonials`: approved or pending customer reviews.

## Business Profile

For a single-client deployment, keep one `BusinessProfile` marked as active. The active profile controls the public website.

Editable business settings include:

- Business name and split logo text.
- Website meta description.
- Hero badge, headline, and body copy.
- Display phone number and clickable telephone number.
- WhatsApp number and prefilled WhatsApp message.
- Email address and service area.
- Services, booking, reviews, about, and footer copy.
- Optional hero, services, about, and booking images.
- Active/inactive status.

Use the inline sections on the same Business Profile screen to manage:

- Trust indicators shown in the trust strip.
- Service cards shown on the services page.
- Testimonials attached to that business profile.

For WhatsApp, enter the number in international format, for example:

```text
+441615550123
```

When a WhatsApp number is set, the mobile bottom nav shows `WhatsApp` instead of `Call`, and the booking page shows a `Chat on WhatsApp` button.

## Booking Enquiries

When a visitor submits the booking form, a `BookingEnquiry` is created.

Admin fields include:

- Customer name, phone, email, address, and postcode.
- Preferred date and time slot.
- Requested service.
- Issue description.
- Emergency flag.
- Status.
- Admin notes.
- Contacted timestamp.
- Testimonial job label.
- Readonly testimonial request link.
- Created and updated timestamps.

Recommended workflow:

1. Open new enquiries from `Booking enquiries`.
2. Call or email the customer.
3. Update `status` from `New` to `Contacted`, `Booked`, `Completed`, or `Cancelled`.
4. Add internal notes in `admin_notes`.
5. After completing a job, set `testimonial_job_label` to a customer-friendly job name, such as `Kitchen sink repair`.
6. Copy the readonly testimonial link into the invoice or follow-up email.

The public form uses server-side validation for required fields, UK phone numbers, UK postcodes, preferred dates, and description length. JavaScript only improves the experience; it is not trusted for validation.

## Email Notifications

Each valid booking enquiry is saved first, then the app attempts to send a notification email to `ADMIN_NOTIFICATION_EMAIL`.

If email sending fails, the customer still sees a success message and the enquiry remains saved in the database. The failure is logged for debugging.

Email provider settings are controlled from `.env`, not Admin.

Supported provider modes:

- `console`: development email printed to the terminal.
- `sender_net`: Sender.net SMTP.
- `google_workspace`: Google Workspace SMTP using an app password.
- `google_workspace_relay`: Google Workspace SMTP relay.
- `custom_smtp`: manual SMTP host/port credentials.

Fill in these `.env` values for production:

```env
EMAIL_PROVIDER=sender_net
DEFAULT_FROM_EMAIL=bookings@yourdomain.com
SERVER_EMAIL=bookings@yourdomain.com
ADMIN_NOTIFICATION_EMAIL=owner@yourdomain.com
EMAIL_HOST_USER=your_smtp_username
EMAIL_HOST_PASSWORD=your_smtp_password_or_key
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
```

For Google Workspace SMTP, use:

```env
EMAIL_PROVIDER=google_workspace
EMAIL_HOST_USER=bookings@yourdomain.com
EMAIL_HOST_PASSWORD=your_google_workspace_app_password
```

## Testimonials

Testimonials can be created manually in Admin or submitted by customers through signed links.

Signed testimonial links are generated from each `BookingEnquiry` in the readonly field:

```text
testimonial link for invoice email
```

Use this link in an invoice email after the job is complete. The endpoint is:

```text
/put/testimonial/<signed-token>/
```

Customer submissions are saved as inactive by default. Review them in Admin, then tick `is_active` when they are ready to appear on the public reviews page.

Review cards can show what job was done through `job_label`. For customer-submitted testimonials, the app copies this from the booking enquiry's `testimonial_job_label`. If that field is blank, it falls back to the booking service name.

## Static Files and Images

Bundled design assets live in:

```text
trades/static/trades/images/
```

Client-uploaded images from Admin use Django media storage:

```text
MEDIA_ROOT
MEDIA_URL
```

Use static files for reusable placeholder/design images shipped with the app. Use media uploads for client-specific hero, service, about, and booking images.

Before production deploy, run:

```bash
python manage.py collectstatic
```

## Reusing the App for Another Client

This project is designed to be cloned for different local trade clients.

For each new client:

1. Clone the project.
2. Create a new PostgreSQL database.
3. Copy `.env.example` to `.env`.
4. Set the new `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, and email settings.
5. Run migrations.
6. Create a superuser.
7. Edit the active Business Profile in Admin.
8. Replace services, trust indicators, testimonials, copy, images, phone, email, and WhatsApp details.

Keep one active `BusinessProfile` per deployed client site unless the project is later extended for true multi-tenant routing.

## Useful Commands

Run checks:

```bash
python manage.py check
```

Create migrations after model changes:

```bash
python manage.py makemigrations
```

Apply migrations:

```bash
python manage.py migrate
```

Run tests:

```bash
python manage.py test
```

Start local development server:

```bash
python manage.py runserver
```

Deploy to production:

```bash
bash deploy/start.sh
```

This installs Python dependencies, runs Django preflight checks (check, makemigrations, migrate, createcachetable, collectstatic), and gracefully restarts the systemd Gunicorn service.

For local/LAN testing, use the home deployment script instead:

```bash
bash deploy/home/start.sh
```

The home deployment script runs a self-contained Nginx + Gunicorn stack on port `8021` (or the next free port if busy).

