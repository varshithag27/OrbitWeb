from config import Config

_client = None
if Config.SMS_ENABLED:
    from twilio.rest import Client
    _client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)


def send_sms_otp(to_phone: str, otp: str) -> bool:
    """
    Sends a real OTP SMS via Twilio. Requires TWILIO_* env vars.
    Returns True on success, False on failure/disabled.
    Phone numbers must be in E.164 format, e.g. +919876543210.
    """
    if not Config.SMS_ENABLED:
        print(f"[SMS DISABLED] Would send OTP {otp} to {to_phone}")
        return False

    try:
        _client.messages.create(
            body=f"Your verification code is {otp}. It expires in "
                 f"{Config.OTP_EXPIRY_MINUTES} minutes.",
            from_=Config.TWILIO_PHONE_NUMBER,
            to=to_phone,
        )
        return True
    except Exception as e:
        print(f"[SMS ERROR] {e}")
        return False
