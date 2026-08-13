import re
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from utils.otp_utils import generate_otp, otp_expiry, is_expired
from utils.email_utils import send_email_otp
from utils.sms_utils import send_sms_otp

app = Flask(__name__)
app.config.from_object(Config)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[Config.MONGO_DB_NAME]
users = db.users

try:
    client.admin.command("ping")
    users.create_index("email", unique=True)
except Exception as exc:
    raise SystemExit(
        "Cannot connect to MongoDB. Start MongoDB locally or set MONGO_URI in .env "
        "to a MongoDB Atlas connection string.\n"
        f"Current MONGO_URI: {Config.MONGO_URI}\n"
        f"Error: {exc}"
    ) from exc

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[1-9]\d{7,14}$")  # loose E.164-ish check


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def issue_and_send_otp(user_doc, channel):
    """Generate a fresh OTP, save it on the user doc, and dispatch it."""
    otp = generate_otp()
    expiry = otp_expiry(Config.OTP_EXPIRY_MINUTES)

    users.update_one(
        {"_id": user_doc["_id"]},
        {"$set": {"otp": otp, "otp_expiry": expiry}},
    )

    sent = False
    if channel in ("email", "both") and user_doc.get("email"):
        sent = send_email_otp(user_doc["email"], otp) or sent
    if channel in ("sms", "both") and user_doc.get("phone"):
        sent = send_sms_otp(user_doc["phone"], otp) or sent

    # Dev fallback: if no real provider is configured, print to server console
    # so the flow is still testable end-to-end before credentials are set up.
    if not sent:
        print(f"[DEV OTP FALLBACK] OTP for {user_doc.get('email') or user_doc.get('phone')}: {otp}")

    return sent


# ---------------------------------------------------------------------------
# Routes: home
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Routes: register
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not name or not email or not password:
        flash("Name, email and password are required.", "error")
        return redirect(url_for("register"))

    if not EMAIL_RE.match(email):
        flash("Please enter a valid email address.", "error")
        return redirect(url_for("register"))

    if phone and not PHONE_RE.match(phone):
        flash("Please enter a valid phone number in international format, e.g. +919876543210.", "error")
        return redirect(url_for("register"))

    if len(password) < 8:
        flash("Password must be at least 8 characters.", "error")
        return redirect(url_for("register"))

    if password != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("register"))

    if users.find_one({"email": email}):
        flash("An account with this email already exists.", "error")
        return redirect(url_for("register"))

    user_doc = {
        "name": name,
        "email": email,
        "phone": phone or None,
        "password_hash": generate_password_hash(password),
        "is_verified": False,
        "otp": None,
        "otp_expiry": None,
        "created_at": datetime.utcnow(),
    }
    result = users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    channel = "both" if phone else "email"
    issue_and_send_otp(user_doc, channel)

    session["pending_user_id"] = str(user_doc["_id"])
    flash("Account created. Enter the code we sent you to verify your account.", "success")
    return redirect(url_for("verify_otp"))


# ---------------------------------------------------------------------------
# Routes: OTP verification
# ---------------------------------------------------------------------------
@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    from bson import ObjectId

    pending_id = session.get("pending_user_id")
    if not pending_id:
        return redirect(url_for("login"))

    user_doc = users.find_one({"_id": ObjectId(pending_id)})
    if not user_doc:
        session.pop("pending_user_id", None)
        return redirect(url_for("register"))

    if request.method == "GET":
        masked_email = user_doc.get("email", "")
        return render_template("verify_otp.html", email=masked_email)

    entered_otp = "".join(
        request.form.get(f"digit{i}", "") for i in range(1, 7)
    ) or request.form.get("otp", "").strip()

    if not entered_otp:
        flash("Please enter the verification code.", "error")
        return redirect(url_for("verify_otp"))

    if is_expired(user_doc.get("otp_expiry")):
        flash("Code expired. Please request a new one.", "error")
        return redirect(url_for("verify_otp"))

    if entered_otp != user_doc.get("otp"):
        flash("Incorrect code. Please try again.", "error")
        return redirect(url_for("verify_otp"))

    users.update_one(
        {"_id": user_doc["_id"]},
        {"$set": {"is_verified": True, "otp": None, "otp_expiry": None}},
    )

    session.pop("pending_user_id", None)
    session["user_id"] = str(user_doc["_id"])
    flash("Account verified! Welcome.", "success")
    return redirect(url_for("dashboard"))


@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    from bson import ObjectId

    pending_id = session.get("pending_user_id")
    if not pending_id:
        return jsonify({"ok": False, "message": "Session expired, please register again."}), 400

    user_doc = users.find_one({"_id": ObjectId(pending_id)})
    if not user_doc:
        return jsonify({"ok": False, "message": "User not found."}), 404

    channel = "both" if user_doc.get("phone") else "email"
    issue_and_send_otp(user_doc, channel)
    return jsonify({"ok": True, "message": "A new code has been sent."})


# ---------------------------------------------------------------------------
# Routes: login / logout
# ---------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user_doc = users.find_one({"email": email})
    if not user_doc or not check_password_hash(user_doc["password_hash"], password):
        flash("Invalid email or password.", "error")
        return redirect(url_for("login"))

    if not user_doc.get("is_verified"):
        # Re-trigger OTP flow so unverified users can finish onboarding.
        session["pending_user_id"] = str(user_doc["_id"])
        channel = "both" if user_doc.get("phone") else "email"
        issue_and_send_otp(user_doc, channel)
        flash("Please verify your account. We've sent you a new code.", "error")
        return redirect(url_for("verify_otp"))

    session["user_id"] = str(user_doc["_id"])
    flash(f"Welcome back, {user_doc['name']}!", "success")
    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Routes: dashboard (protected)
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    from bson import ObjectId
    user_doc = users.find_one({"_id": ObjectId(session["user_id"])})
    return render_template("dashboard.html", user=user_doc)


if __name__ == "__main__":
    print(f" * Open on this PC:     http://127.0.0.1:{Config.PORT}")
    print(f" * Open from another device on the same Wi-Fi: http://<this-pc-ip>:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=True)
