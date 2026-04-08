# CICD — Docker

Stack: **FastAPI** (`backend`), **React static assets** (`frontend`), and **nginx** as the **only** reverse proxy (routes `/` → frontend, `/api/` → backend).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (includes Docker Compose v2)

## Run with Docker Compose

From the repository root:

```bash
docker compose up --build
```

- **App (via proxy):** http://localhost:80 — use this for the UI; API calls go to `/api` on the same host.
- **Backend (direct):** http://localhost:8000 — optional, for debugging.

Stop:

```bash
docker compose down
```

Detached:

```bash
docker compose up -d --build
```

## Build images manually

**Backend:**

```bash
docker build -t fastapi-app:local ./fastapi-app
docker run --rm -p 8000:8000 fastapi-app:local
```

**Frontend** (static only; build context is `frontend/`):

```bash
docker build -t frontend:local ./frontend
docker run --rm -p 8080:80 frontend:local
```

**Proxy nginx** (expects `frontend` and `backend` hostnames — use with Compose or a shared network):

```bash
docker build -t nginx-proxy:local ./nginx
```

## Notes

- `docker-compose.yml` uses `akkii/fastapi-app:latest` for the backend. To run your local API code:

```bash
docker build -t akkii/fastapi-app:latest ./fastapi-app
docker compose up --build
```

- The React app uses `REACT_APP_API_BASE_URL` at build time (default `/api` in `frontend/src/App.js`). With the proxy, `/api` is correct.

## Troubleshooting

- **Port in use:** Change `"80:80"` or `"8000:8000"` in `docker-compose.yml`.
- **Backend not updating:** Rebuild and tag `akkii/fastapi-app:latest` as above, or point `backend.image` at your registry tag.
