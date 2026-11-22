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
REDIS_URL=redis://localhost:6379/0
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

The Flask app serves both its pages and backend; you do not need to deploy a
separate frontend. Create a Render Web Service connected to this GitHub
repository and use:

- Runtime: `Python 3`
- Build command: `pip install -r requirements.txt`
- Start command: `PYTHONDONTWRITEBYTECODE=1 gunicorn --bind 0.0.0.0:$PORT app:app`

Add these in the Render service's Environment settings:

- `FLASK_SECRET_KEY`: a long, random secret
- `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`
- `RAZORPAY_CURRENCY=INR`
- `REDIS_URL` for Redis caching. Trek listings are cached, and database commits
  invalidate the cached data. If Redis is not configured or unavailable,
  caching is bypassed and the app continues to read from the database.
- The `MAIL_*` settings described above if email verification and password
  reset are required

For local caching, run Redis locally and set
`REDIS_URL=redis://localhost:6379/0` in `.env`; Redis is optional for local
startup.

The app uses SQLite 3 for storage. Do not commit `.env`, database files, or
payment credentials. This setup is suitable for project showcasing, but Render's
default filesystem is temporary: database changes and uploaded trek photos may
be lost after redeployments or restarts.

GitHub pushes trigger Render deployments when automatic deploys are enabled.