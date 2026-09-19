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

Create a local `.env` file and set the Razorpay live credentials and a strong Flask secret:

```text
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
FLASK_SECRET_KEY=...
```

Run locally with:

```bash
python app.py
```

Bookings are created only after Razorpay Checkout returns a valid payment signature. Trek prices are managed by an administrator and stored in INR.

## Render deployment

Create a Render Web Service connected to the GitHub repository and use:

- Runtime: `Python 3`
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`

Add `FLASK_SECRET_KEY`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and `RAZORPAY_CURRENCY=INR` under Render Environment Variables. Do not commit `.env` or Razorpay secrets.