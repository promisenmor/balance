# Authentication and onboarding API

The API uses Django's built-in `User` model. Registration needs only an email
address and password; the related profile is created automatically and may be
completed later. A profile is considered onboarded once both `first_name` and
`last_name` are provided. Email verification is required before login.

Access and refresh JWTs are returned in JSON. Send the access token on protected
requests as `Authorization: Bearer <access>`. Refresh tokens rotate and are
blacklisted when rotated or logged out.

## Local setup

Install dependencies, generate the initial app migration, and migrate:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py makemigrations core
.\venv\Scripts\python.exe manage.py migrate
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
| `GET` | `/api/auth/user/` | Access JWT | Retrieve the authenticated user and their profile |
| `GET`, `PATCH` | `/api/auth/profile/` | Access JWT | Retrieve or update the authenticated user's profile |
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

Invalid input and invalid credentials return HTTP `400` with validation
details. Invalid or expired email-verification keys return HTTP `404`.
Unauthenticated protected requests return HTTP `401`; unverified accounts
cannot log in. Passwords are processed by Django's password validators and
hashers.
