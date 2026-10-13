# Authentication and onboarding API

The API uses Django's built-in `User` model. Registration needs only an email
address and password; the related profile is created automatically and may be
completed later. A profile is considered onboarded once both `first_name` and
`last_name` are provided. Email verification is required before login.

The email/password API login returns access and refresh JWTs in JSON. Send the
access token on protected requests as `Authorization: Bearer <access>`. Refresh
tokens rotate and are blacklisted when rotated or logged out. Django session
authentication is also enabled for browser/API clients using the Django REST
Framework login at `/api-auth/login/`; session-authenticated unsafe requests
must include a valid CSRF token.

## Local setup

Install dependencies, configure the database in `.env`, apply the migrations,
and create an administrator:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py tailwind install
.\venv\Scripts\python.exe manage.py tailwind build
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py createsuperuser
.\venv\Scripts\python.exe manage.py runserver
```

Email is printed to the development console by default. Set `EMAIL_BACKEND` to
a configured production Django email backend and `DEFAULT_FROM_EMAIL` in the
deployment environment before enabling real user signups. Production must also
set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, and
`DJANGO_ALLOWED_HOSTS=your-domain.example`; HTTPS is enforced when debug is
disabled.

## Endpoints

The signed-in HTML frontend is available at `/` after signing in at `/login/`.
It includes the dashboard, transactions, budgets, goals, analytics, and
settings. Its data is loaded from the API using the Django session and CSRF