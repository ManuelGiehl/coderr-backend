# coderr-backend

Django REST backend for the Coderr project.

## Setup

### Virtual environment (recommended)

```bash
python -m venv .venv
# Windows CMD:
.venv\Scripts\activate.bat
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
# source .venv/bin/activate
pip install -r backend/requirements.txt
```
You must activate the venv before running `manage.py`; otherwise you get `ModuleNotFoundError: No module named 'decouple'`.

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

**Important:** Activate the virtual environment first, then run from `backend/`:

```bash
# From project root (e.g. coderr_backend):

# Windows CMD:
.venv\Scripts\activate.bat
cd backend
python manage.py runserver

# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
cd backend
python manage.py runserver
```
You should see `(.venv)` at the start of your prompt when the venv is active.

Backend runs at **http://127.0.0.1:8000/**.

### Tests

```bash
cd backend
python manage.py test
```

## Guest users (demo login)

To use the frontend’s guest login (Kunde/Anbieter), create the demo users once:

```bash
cd backend
python manage.py create_guest_users
```

This creates:

- **Kunde:** username `andrey`, password `asdasd`
- **Anbieter:** username `kevin`, password `asdasd24`

Credentials must match `frontend/shared/scripts/config.js` (GUEST_LOGINS). You can run the command again to reset their passwords if needed.

## Testing with the frontend

1. **Start the backend** (with venv activated, see above).
2. **Open the frontend with Live Server** in VS Code (right‑click `frontend/index.html` → “Open with Live Server”). Do **not** open `index.html` by double‑clicking (file://) – the browser will block requests to the API.
3. In the browser, the start page calls `GET /api/base-info/`. If that fails, you see **“Einige Daten konnten nicht geladen werden”** and login will also fail.

**If you see “Einige Daten konnten nicht geladen werden” or login does not work:**

- **Backend running?** In a new terminal: venv aktivieren → `cd backend` → `python manage.py runserver`. Leave this running.
- **API erreichbar?** In the browser open http://127.0.0.1:8000/api/base-info/ – you should see JSON like `{"review_count": 0, "average_rating": 0.0, ...}`. If you get “Unable to connect” or a blank page, the backend is not running or not reachable.
- **Frontend per Live Server?** The address bar should start with `http://127.0.0.1:55xx/` or similar, **not** `file:///`. If you use file://, the browser blocks the API requests.
- **F12 → Network (or Console):** Check for failed (red) requests to `127.0.0.1:8000` or CORS errors.

## Notes

- `.env` and the database are not committed (see `.gitignore`).
