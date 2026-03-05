# coderr-backend

Django REST backend for the Coderr project.

## Setup

### Virtual environment (recommended)

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Environment variables

Copy the example file to `.env` and set your secrets (do not commit `.env`):

- **Windows:** `copy .env.example .env`
- **Linux/macOS:** `cp .env.example .env`

Edit `.env` and set at least:

- **SECRET_KEY** – Django secret key (e.g. generate with:  
  `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)

Optional:

- **DEBUG** – set to `False` in production.

Settings are loaded from `.env` in the project root via `python-decouple`.

### Run the project

```bash
cd backend
python manage.py migrate
python manage.py runserver
```

### Tests

```bash
cd backend
python manage.py test
```

## Notes

- `.env` and the database are not committed (see `.gitignore`).
