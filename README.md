# Orbit — Full-Stack Login/Register with Real OTP

A Flask + MongoDB authentication system with **real** email OTP (SMTP) and
optional real SMS OTP (Twilio), plus a dynamic, animated login/register UI.

## Features
- Register with name, email, optional phone, password (hashed with Werkzeug)
- Real 6-digit OTP sent to email (and SMS if a phone + Twilio are configured)
- OTP auto-advancing input boxes, resend with cooldown, expiry (default 5 min)
- Login blocks unverified accounts and re-sends a fresh OTP automatically
- Session-based auth, protected dashboard route
- MongoDB storage via PyMongo, works with local MongoDB or MongoDB Atlas (free tier)

## 1. Install prerequisites
- Python 3.10+
- MongoDB running locally (`mongod`) **or** a free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register) cluster

```bash
cd fbauth
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure environment variables
Copy the example file and fill in real credentials:

```bash
cp .env.example .env
```

- `MONGO_URI` — local (`mongodb://localhost:27017/`) or your Atlas connection string
- `SMTP_USERNAME` / `SMTP_PASSWORD` — for **real email OTP**. With Gmail:
  1. Turn on 2-Step Verification on the Google account
  2. Create an App Password at https://myaccount.google.com/apppasswords
  3. Use that 16-character password as `SMTP_PASSWORD` (not your normal password)
- `TWILIO_*` — optional, for **real SMS OTP**. Sign up free at
  https://www.twilio.com/try-twilio to get a trial number, Account SID, and
  Auth Token. Leave these blank to run email-only — the app still works fully.

If neither SMTP nor Twilio is configured, the app falls back to printing the
OTP to the server console so you can still test the full flow locally.

## 3. Run it

```bash
python app.py
```

Visit **http://localhost:5000** — you'll land on the login page. Click
"Create new account" to register, then check your email (and phone, if
provided) for the verification code.

## Project structure
```
fbauth/
├── app.py                 # Flask routes: register, login, OTP verify/resend, dashboard
├── config.py               # Loads settings from .env
├── utils/
│   ├── otp_utils.py         # OTP generation & expiry logic
│   ├── email_utils.py       # Real SMTP email sending
│   └── sms_utils.py         # Real Twilio SMS sending
├── templates/                # Jinja2 HTML (login, register, OTP, dashboard)
├── static/css/style.css      # Design system + animations
├── static/js/script.js       # OTP box behavior, resend cooldown, toasts
└── requirements.txt
```

## Notes & next steps
- This is a demo-grade implementation: for production, add rate-limiting on
  OTP requests, HTTPS, CSRF protection (e.g. Flask-WTF), and a proper
  password-reset flow.
- The OTP is stored in the `users` collection alongside the user document —
  for higher-volume apps, consider a separate `otps` collection with a TTL
  index so MongoDB auto-expires old codes.
- Passwords are hashed with Werkzeug's PBKDF2-based `generate_password_hash`;
  never store plaintext passwords.
