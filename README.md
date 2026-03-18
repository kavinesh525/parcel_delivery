# parcel_delivery

Optimized path planning using AI.

## Overview

This repository contains two main parts:

- **Backend**: API server (likely Python/FastAPI) that provides routing/path planning endpoints.
- **UI**: Frontend application (likely React/Vite or similar) that consumes the backend API.

Adjust the paths/commands below if your project structure differs.

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (includes `npm` or `pnpm`)
- Git

---

## Backend (API)

### 1) Install dependencies

From the repo root:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If you don’t have `requirements.txt`, install the packages used by the backend (e.g., `fastapi`, `uvicorn`, etc.):

```bash
pip install fastapi uvicorn
```

### 2) Run the backend

From the repo root, run the server (adjust the module name if different):

```bash
uvicorn main:app --reload
```

If your entrypoint is in a different file (e.g., `app.py`, `server.py`, `api.py`), replace `main:app` accordingly.

By default, the server will be available at:

- `http://127.0.0.1:8000`

---

## Frontend (UI)

### 1) Install dependencies

Change into the frontend directory (replace `frontend` with the actual folder name if different):

```bash
cd frontend
npm install
```

If it’s a Vite project and the folder is named `ui` or `client`, use that path.

### 2) Run the UI

```bash
npm run dev
```

This will typically start the UI at:

- `http://localhost:5173`

Make sure the backend is running and that the frontend is configured to call the backend URL (e.g., `http://localhost:8000`).

---

## Notes

- If CORS is enabled on the backend, ensure the frontend origin (`http://localhost:5173`) is allowed.
- Update `README.md` if folder names or entrypoints differ from the assumptions above.
