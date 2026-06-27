# WhatsApp Notification Setup

When a customer submits a booking enquiry, the app sends an automatic WhatsApp message to the plumber via Twilio. The message includes the customer's name, service, phone, email, and postcode.

---

## 1. Install the Twilio package

```bash
pip install twilio
```

## 2. Get Twilio credentials

1. Sign up at [twilio.com](https://www.twilio.com)
2. In the Twilio Console, find your **Account SID** and **Auth Token** on the dashboard
3. Go to **Messaging > Try it out > Send a WhatsApp message** and follow the sandbox activation steps
4. Once activated, you will have a Twilio WhatsApp number (e.g. `+14155238886`)

> **Note:** The Twilio sandbox is free for testing. To send messages to any number in production, you need an approved WhatsApp Business Profile through Twilio.

## 3. Add credentials to `.env`

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=+14155238886
```

## 4. Set the plumber's WhatsApp number

1. Go to Django Admin → **Business profiles** → edit the active profile
2. Fill in **WhatsApp number** (international format, e.g. `+447700123456`)
3. Optionally set a **WhatsApp prefilled message** (used for the "Chat on WhatsApp" link on the site)
4. Save

## 5. Verify

Submit a test booking on the site. The notification email will fire as normal, and a WhatsApp message will be sent to the number set on the BusinessProfile.

Check the logs (`logs/django.log`) for confirmation or errors:

```
INFO trades.views: WhatsApp notification sent for booking 42.
```

## How it works

- The import of `twilio` is **lazy** — it only runs inside `_send_whatsapp_notification()` when all credentials are set. The app starts and functions normally without `twilio` installed.
- If credentials are missing or the WhatsApp number is blank, the notification is silently skipped with a warning logged.
- WhatsApp sending failure does **not** roll back the booking — the enquiry is persisted regardless.
- Both the admin email and customer confirmation email are sent independently of WhatsApp.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| No WhatsApp message sent | `TWILIO_*` values not set in `.env` |
| No WhatsApp message sent | `whatsapp_number` blank on BusinessProfile |
| `ImportError: No module named 'twilio'` | Run `pip install twilio` |
| Twilio error 63016 (sandbox join) | Recipient must send a join message to the Twilio sandbox number first |
| Log says "WhatsApp notification skipped" | Credentials or WhatsApp number missing |
