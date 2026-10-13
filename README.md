# Balance

Balance is a Django project with a REST API, PostgreSQL configuration, and a
Tailwind CSS theme app.

## Requirements

- Python 3.12 or newer
- PostgreSQL
- Node.js and npm

## Local setup

From the repository root, create and activate a virtual environment, then
install the Python dependencies:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a local environment file and edit its PostgreSQL credentials:

```powershell
Copy-Item .env.example .env
```

Create a PostgreSQL database and user matching `DB_NAME`, `DB_USER`, and
`DB_PASSWORD` in `.env`. Then prepare the Tailwind theme and the database:

```powershell
python manage.py tailwind install
python manage.py migrate
```

Run Django and the Tailwind watcher together during development:

```powershell
python manage.py tailwind dev
```

For a Django-only server, run `python manage.py runserver`. To rebuild the
production CSS, run `python manage.py tailwind build`, then collect static files
with `python manage.py collectstatic`.

`DB_ENGINE=django.db.backends.sqlite3` can be used in `.env` for local checks
that do not require a running PostgreSQL server.
