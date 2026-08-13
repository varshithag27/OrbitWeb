import random
from datetime import datetime, timedelta


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP, e.g. '482913'."""
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def otp_expiry(minutes: int) -> datetime:
    return datetime.utcnow() + timedelta(minutes=minutes)


def is_expired(expiry_dt: datetime) -> bool:
    if expiry_dt is None:
        return True
    return datetime.utcnow() > expiry_dt
