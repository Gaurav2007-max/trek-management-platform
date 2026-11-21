# trek-management-platform
This is a Flask application that allows users and staff to manage trekking activities at different locations.

## Local setup

```bash
python -m venv .venv
```

Activate the virtual environment, then install the dependencies:

```bash
pip install -r requirements.txt
```

Create a local `.env` file and set the Razorpay credentials, SMTP settings, and a strong Flask secret:

```text
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
FLASK_SECRET_KEY=...
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_DEFAULT_SENDER=...
MAIL_USE_TLS=true
```

Configure `MAIL_SERVER`, `MAIL_PORT`, `MAIL_DEFAULT_SENDER`, and (when required by
your provider) `MAIL_USERNAME`/`MAIL_PASSWORD` for email verification and password
reset codes. Use `MAIL_USE_SSL=true` with the provider's SSL port (typically 465)
instead of STARTTLS when required. Verification codes expire after 10 minutes.
Trek photos are optional JPG, PNG, or WebP uploads (up to 5 MB) and are stored
under `static/uploads/treks`.

Run locally with:

```bash
python -B app.py
```

Bookings are created only after Razorpay Checkout returns a valid payment signature. Trek prices are managed by an administrator and stored in INR.

## Render deployment

Create a Render Web Service connected to the GitHub repository and use:

- Runtime: `Python 3`
- Build command: `pip install -r requirements.txt`
- Start command: `PYTHONDONTWRITEBYTECODE=1 gunicorn --bind 0.0.0.0:$PORT app:app`

Add `FLASK_SECRET_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_CURRENCY=INR` under Render Environment Variables. Do not commit `.env` or Razorpay secrets.