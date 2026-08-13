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

## How to run

You need **Python 3.10+** and a **MongoDB** database (local or [Atlas](https://www.mongodb.com/cloud/atlas/register)).

```bash
git clone https://github.com/varshithag27/OrbitWeb.git
cd OrbitWeb
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env         # macOS/Linux: cp .env.example .env
```

Open `.env` and set:

- `MONGO_URI` — `mongodb://localhost:27017/` **or** your Atlas connection string
- `SMTP_USERNAME` / `SMTP_PASSWORD` — optional. For Gmail, use an [App Password](https://myaccount.google.com/apppasswords), not your normal password
- `TWILIO_*` — optional. Leave blank for email-only / local testing

If SMTP and Twilio are empty, the OTP is printed in the terminal as `[DEV OTP FALLBACK]`.

```bash
python app.py
```

Open **http://127.0.0.1:5000**, create an account, enter the OTP, then log in.

If PowerShell blocks `activate`, run `venv\Scripts\python.exe app.py` instead.

## Project structure
```
├── app.py                 # Flask routes: register, login, OTP verify/resend, dashboard
├── config.py              # Loads settings from .env
├── utils/
│   ├── otp_utils.py       # OTP generation & expiry logic
│   ├── email_utils.py     # Real SMTP email sending
│   └── sms_utils.py       # Real Twilio SMS sending
├── templates/             # Jinja2 HTML (login, register, OTP, dashboard)
├── static/css/style.css   # Design system + animations
├── static/js/script.js    # OTP box behavior, resend cooldown, toasts
└── requirements.txt
```

## Notes
- Demo-grade: for production add rate-limiting, HTTPS, CSRF, and password reset.
- Passwords are hashed with Werkzeug; never stored as plaintext.
- Do not commit `.env`.
