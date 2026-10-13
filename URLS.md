# Application URLs

This is the route index for the Balance frontend, API, authentication, and
supporting tools. Paths are relative to the site's root URL. Routes marked
authenticated require a signed-in user or a valid access token, as indicated.

## Frontend

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET`, `POST` | `/login/` | None | Sign in to the web app |
| `POST` | `/logout/` | Session | Sign out of the web app |
| `GET` | `/` | Session | Dashboard |
| `GET` | `/transactions/` | Session | Manage transactions |
| `GET` | `/budgets/` | Session | Manage budgets |
| `GET` | `/goals/` | Session | Manage savings goals |
| `GET` | `/analytics/` | Session | View spending and cash-flow analytics |
| `GET` | `/settings/` | Session | Edit profile and reminders |

## API

### Balance resources

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET`, `PATCH` | `/api/auth/profile/` | Access token or session | Read or update the current user's profile |
| `GET`, `POST` | `/api/transactions/` | Access token or session | List or create transactions |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/transactions/<id>/` | Access token or session | Read, replace, update, or delete an owned transaction |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/transactions/<id>` | Access token or session | Legacy detail route without a trailing slash |
| `GET`, `POST` | `/api/goal/`, `/api/goals/` | Access token or session | List or create savings goals |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/goal/<id>/`, `/api/goals/<id>/` | Access token or session | Read, replace, update, or delete an owned goal |
| `GET`, `POST` | `/api/budgets/` | Access token or session | List or create budgets |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/budgets/<id>/` | Access token or session | Read, replace, update, or delete an owned budget |
| `GET`, `POST` | `/api/reminders/` | Access token or session | List or create reminders |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/reminders/<id>/` | Access token or session | Read, replace, update, or delete an owned reminder |
| `GET` | `/api/dashboard/` | Access token or session | Read totals, recent transactions, goals, and budget alerts |

### Authentication and account management

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/auth/registration/` | None | Register with an email and password |
| `POST` | `/api/auth/registration/verify-email/` | None | Verify an email using its confirmation key |
| `POST` | `/api/auth/registration/resend-email/` | None | Resend an email confirmation |
| `GET` | `/api/auth/registration/account-email-verification-sent/` | None | Email-verification notice page |
| `GET` | `/api/auth/registration/account-confirm-email/<key>/` | None | Email-confirmation landing page |
| `POST` | `/api/auth/login/` | None | Sign in and receive access and refresh tokens |
| `POST` | `/api/auth/token/refresh/` | None | Rotate tokens using a refresh token |
| `POST` | `/api/auth/token/verify/` | None | Check whether an access token is valid |
| `POST` | `/api/auth/logout/` | Access token | Revoke the submitted refresh token |
| `GET` | `/api/auth/user/` | Access token or session | Read the current user and profile |
| `POST` | `/api/auth/password/change/` | Access token | Change the current user's password |
| `POST` | `/api/auth/password/reset/` | None | Request a password-reset email |
| `GET`, `POST` | `/api/auth/password/reset/confirm/` (optional trailing slash) | None | Display the reset form or submit a password reset |

The Django REST Framework session login/logout pages are available at
`/api-auth/login/` and `/api-auth/logout/`.

## Administration and API tools

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET`, other admin actions | `/admin/` | Django staff account | Django administration |
| `GET` | `/api/schema/` | None | OpenAPI schema |
| `GET` | `/api/docs/` | None | Interactive Swagger API documentation |

For authentication behavior, request examples, and setup details, see
[AUTHENTICATION.md](./AUTHENTICATION.md). The API schema and interactive docs
are also available at `/api/schema/` and `/api/docs/`.
