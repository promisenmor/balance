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

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/registration/` | None | Register with `email`, `password1`, and `password2`; sends verification email |
| `POST` | `/api/auth/registration/verify-email/` | None | Verify with `{"key": "<email key>"}` |
| `POST` | `/api/auth/registration/resend-email/` | None | Resend verification with `{"email": "<address>"}` |
| `POST` | `/api/auth/login/` | None | Login with `email` and `password`; returns `access`, `refresh`, and user details |
| `POST` | `/api/auth/token/refresh/` | None | Exchange a `refresh` token for a rotated pair |
| `POST` | `/api/auth/logout/` | Access JWT | Submit the current `refresh` token to revoke it |
| `GET` | `/api/auth/user/` | Access JWT or session | Retrieve the authenticated user and their profile |
| `GET`, `PATCH` | `/api/auth/profile/` | Access JWT or session | Retrieve or update the authenticated user's profile |
| `GET`, `POST` | `/api/transactions/` | Access JWT or session | List or create the user's transactions |
| `GET`, `PATCH`, `PUT`, `DELETE` | `/api/transactions/<id>/` | Access JWT or session | Retrieve, update, or delete an owned transaction |
| `GET`, `POST` | `/api/budgets/` | Access JWT or session | List budgets with spending and alert status, or create one |
| `GET`, `PATCH`, `PUT`, `DELETE` | `/api/budgets/<id>/` | Access JWT or session | Retrieve, update, or delete an owned budget |
| `GET`, `POST` | `/api/goals/` | Access JWT or session | List or create the user's savings goals |
| `GET`, `PATCH`, `PUT`, `DELETE` | `/api/goals/<id>/` | Access JWT or session | Retrieve, update, or delete an owned goal |
| `GET`, `POST` | `/api/reminders/` | Access JWT or session | List or create the user's reminders |
| `GET`, `PATCH`, `PUT`, `DELETE` | `/api/reminders/<id>/` | Access JWT or session | Retrieve, update, or delete an owned reminder |
| `GET` | `/api/dashboard/` | Access JWT or session | Retrieve totals, recent transactions, goals, and budget alerts |
| `POST` | `/api/auth/password/change/` | Access JWT | Change password with `old_password`, `new_password1`, and `new_password2` |
| `POST` | `/api/auth/password/reset/` | None | Request a reset email with `email` |
| `POST` | `/api/auth/password/reset/confirm/` | None | Confirm reset with `uid`, `token`, `new_password1`, and `new_password2` |

The reset email opens a small password form at the confirmation URL. API clients
can instead read `uid` and `token` from that URL and submit them with the new
password to the confirmation endpoint.

Registration example:

```json
{
  "email": "ada@example.com",
  "password1": "a-strong-unique-password",
  "password2": "a-strong-unique-password"
}
```

Profile completion example:

```http
PATCH /api/auth/profile/
Authorization: Bearer <access>
Content-Type: application/json
```

```json
{
  "first_name": "Ada",
  "last_name": "Okafor"
}
```

The profile response includes `is_onboarded`, derived from the presence of both
names. Email, user ownership, timestamps, and onboarding status are read-only.
The profile API does not collect KYC identifiers or transaction PINs.

Transactions require a positive amount and are assigned to the authenticated
user. Budgets are per category and calendar week (Monday through Sunday), month,
or year. Expense transactions are never blocked by a budget; budget responses
and the dashboard report `none`, `warning` (at least 80% used), or `exceeded`
(at least 100% used), along with spending, remaining amount, and period dates.
Income does not count toward a spending budget. Reminders can be managed through
the API, but no background notification delivery is configured.

Invalid input and invalid credentials return HTTP `400` with validation
details. Invalid or expired email-verification keys return HTTP `404`.
Unauthenticated protected requests return HTTP `401`; unverified accounts
cannot log in. Passwords are processed by Django's password validators and
hashers.
