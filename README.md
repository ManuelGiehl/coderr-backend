# Coderr Backend

Django REST API backend for the Coderr project (IT talent / offer platform). This README is a step-by-step guide to set up, run, and test the project after cloning it from GitHub.

---

## Prerequisites

- **Python 3.10+** installed and available as `python` or `python3`
- **Git**
- (Optional) **VS Code** with **Live Server** extension for testing the frontend

---

## 1. Clone the repository

```bash
git clone <repository-url>
cd coderr_backend
```

Replace `<repository-url>` with the actual GitHub URL (e.g. `https://github.com/username/coderr_backend.git`).

---

## 2. Create and activate a virtual environment

All steps below assume you are in the **project root** (the folder that contains `backend/` and, if present, `frontend/`).

### Windows (CMD)

```bash
python -m venv .venv
.venv\Scripts\activate.bat
```

### Windows (PowerShell)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` (or similar) at the start of your terminal prompt. **Keep this terminal open and the venv active** for all following commands.

---

## 3. Install backend dependencies

From the **project root** (with venv active):

```bash
pip install -r backend/requirements.txt
```

If you get `ModuleNotFoundError: No module named 'decouple'` later, the venv was not active or dependencies were not installed.

---

## 4. Environment variables (.env)

The backend reads configuration from a `.env` file in the **project root**. This file is not in the repo for security reasons.

**4.1** Copy the example file:

- **Windows (CMD):**  
  `copy .env.example .env`
- **Windows (PowerShell):**  
  `Copy-Item .env.example .env`
- **Linux / macOS:**  
  `cp .env.example .env`

**4.2** Generate a Django secret key (optional but recommended):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output.

**4.3** Open `.env` in an editor and set at least:

- `SECRET_KEY=<paste-the-generated-key-here>`

You can leave `DEBUG` commented out (default is `True` for development). For production, set `DEBUG=False`.

**Do not commit `.env`** — it is listed in `.gitignore`.

---

## 5. Run database migrations

From the **project root** with the **venv active**:

```bash
cd backend
python manage.py migrate
cd ..
```

You should see a list of applied migrations. This creates/updates the SQLite database at `backend/db.sqlite3` (this file is also in `.gitignore`).

---

## 6. (Optional) Create guest users for demo login

To use the frontend’s guest login (customer / provider), create the demo users once:

```bash
cd backend
python manage.py create_guest_users
cd ..
```

This creates:

- **Customer:** username `andrey`, password `asdasd`
- **Provider:** username `kevin`, password `asdasd24`

You can run this command again later to reset their passwords if needed.

---

## 7. Start the backend server

From the **project root** with the **venv active**:

```bash
cd backend
python manage.py runserver
```

Leave this terminal running. You should see something like:

- `Starting development server at http://127.0.0.1:8000/`

The API is available at **http://127.0.0.1:8000/api/**.

To stop the server: press `Ctrl+C` in that terminal.

---

## 8. Run the tests

Open a **new terminal**, go to the project root, activate the venv (see step 2), then:

```bash
cd backend
python manage.py test
```

All tests should pass. To run only a specific app’s tests, for example:

```bash
python manage.py test offers_app
```

---

## 9. Quick check that the API works

With the backend running (step 7), open in a browser:

- **http://127.0.0.1:8000/api/base-info/**

You should see JSON similar to:

```json
{"review_count": 0, "average_rating": 0.0, "business_profile_count": 1, "offer_count": 0}
```

If you see “Unable to connect” or a blank page, the server is not running or not reachable.

---

## 10. Testing with the frontend (if available)

If the repository includes a `frontend/` folder:

1. **Start the backend** (step 7) and leave it running.
2. **Serve the frontend over HTTP** — do not open `index.html` via `file://` (the browser will block API requests).
   - In VS Code: right‑click `frontend/index.html` → **Open with Live Server**. The URL will look like `http://127.0.0.1:5500/` or similar.
3. Use the site: search offers, log in (e.g. with guest user `kevin` / `asdasd24`), create an offer, etc.

If you see “Einige Daten konnten nicht geladen werden” or login fails:

- Ensure the backend is running at **http://127.0.0.1:8000/**.
- Ensure the frontend is opened via Live Server (URL starting with `http://`), not `file://`.
- In the browser (F12 → Network / Console), check for failed requests to `127.0.0.1:8000` or CORS errors.

---

## Summary checklist (after clone)

| Step | Action |
|------|--------|
| 1 | Clone repo, `cd` into project root |
| 2 | Create venv (`.venv`) and activate it |
| 3 | `pip install -r backend/requirements.txt` |
| 4 | Copy `.env.example` to `.env`, set `SECRET_KEY` |
| 5 | `cd backend` → `python manage.py migrate` → `cd ..` |
| 6 | (Optional) `cd backend` → `python manage.py create_guest_users` → `cd ..` |
| 7 | `cd backend` → `python manage.py runserver` (keep running) |
| 8 | In another terminal: `cd backend` → `python manage.py test` |
| 9 | Open http://127.0.0.1:8000/api/base-info/ in browser |
| 10 | (If frontend exists) Open `frontend/index.html` with Live Server |

---

## Notes

- **Database:** The SQLite file `backend/db.sqlite3` and the `backend/media/` folder are not committed. Each developer gets a fresh DB after `migrate` and optional `create_guest_users`.
- **API base URL:** The frontend expects the API at `http://127.0.0.1:8000/api/` (see `frontend/shared/scripts/config.js`). If you change the backend port, update that config.
- **CORS:** In development, CORS is permissive when `DEBUG=True` so the frontend on another port can call the API.
