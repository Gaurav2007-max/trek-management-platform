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
- `MYSQL_HOST`, `MYSQL_PORT=3306`, `MYSQL_USER`, `MYSQL_PASSWORD`, and
  `MYSQL_DATABASE` for a Hostinger MySQL database. Use the remote hostname and
  database/user names shown in hPanel, not `localhost`.
- `REDIS_URL` for Redis caching. Trek listings are cached, and database commits
  invalidate the cached data. If Redis is not configured or unavailable,
  caching is bypassed and the app continues to read from the database.
- The `MAIL_*` settings described above if email verification and password
  reset are required

For local caching, run Redis locally and set
`REDIS_URL=redis://localhost:6379/0` in `.env`; Redis is optional for local
startup.

When `MYSQL_HOST` is set, the app creates/uses its MySQL tables. Without it, the
app continues to use SQLite locally. The SQLite database is not copied to
Hostinger automatically; migrate any existing production data before switching.
Do not commit `.env` or database/payment credentials.

In Hostinger hPanel, create the MySQL database and user, then enable remote
connections for the Render service's outbound IP address(es). Do not allow
connections from all IP addresses. Render's outbound IP options depend on the
service plan; if Hostinger cannot allowlist the IPs available to your Render
service, a direct database connection will not work. Confirm remote MySQL
access is enabled for your Hostinger plan before deploying.

To use a Hostinger domain with the Render app, add the domain under the Render
service's Custom Domains settings and enter the DNS records Render provides in
Hostinger's DNS Zone Editor. The app's uploaded trek photos are stored on disk;
Render's default filesystem is temporary, so configure persistent storage for
`static/uploads/treks` if uploaded photos must survive redeploys.

GitHub pushes trigger Render deployments when automatic deploys are enabled.