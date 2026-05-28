# Production Deployment Guide & Checklist

This document details the environment variables, build settings, initialization commands, and verification steps necessary to host the ESG Data Ingestion Platform in a production environment.

---

## 1. Environment Variable Templates

### Backend (Render / Platform Environment)
Configure these variables in your host console. Do not commit these values to source control.

| Variable Name | Required | Description / Example |
| :--- | :--- | :--- |
| `DEBUG` | Yes | Set to `false` in production. |
| `SECRET_KEY` | Yes | A cryptographically secure, high-entropy string. |
| `DATABASE_URL` | Yes | The PostgreSQL connection string: `postgresql://[user]:[password]@[host]/[database]` |
| `ALLOWED_HOSTS` | Yes | Comma-separated list of hostnames: `esg-backend-api.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | Yes | Comma-separated list of frontend URLs: `https://esg-compliance-platform.vercel.app` |
| `SECURE_SSL_REDIRECT` | No | Set to `true` to force HTTP -> HTTPS redirect. Defaults to `true` if `DEBUG=false`. |

### Frontend (Vercel Build Environment)
Injected during the production build cycle.

| Variable Name | Required | Description / Example |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | Yes | Endpoint of the live Django service: `https://esg-backend-api.onrender.com/api` |

---

## 2. Production Initialization Commands

Run these commands to verify, initialize, and seed the production environment.

### Database Migrations
Execute standard migrations to build tables:
```bash
python manage.py migrate --noinput
```

### Static Resource Collection
Gather Django Admin assets for static serving:
```bash
python manage.py collectstatic --noinput
```

### Database Seeding
Create default isolation tenants, database sources, and the standard auditor user:
```bash
python manage.py seed_data
```

### Create Additional Superusers (Optional)
Provision a custom admin account for Django backend management:
```bash
python manage.py createsuperuser
```

---

## 3. Production Deployment Checklist

### Pre-Deployment
- [ ] Verify that all backend tests pass locally (`python manage.py test` runs clean).
- [ ] Confirm `frontend` builds successfully (`npm run build` is free of type/bundling errors).
- [ ] Add the Vercel production deployment URL to the backend's `CORS_ALLOWED_ORIGINS` list.
- [ ] Confirm `.env` files are in `.gitignore` and not pushed to public repositories.

### Backend Provisioning (Render)
- [ ] Create a web service using `render.yaml` blueprint or link the repository to a new Python service.
- [ ] Verify database connection is active (Postgres cluster healthy).
- [ ] Check deployment logs to ensure static files were collected, and migrations executed successfully during build.
- [ ] Run the database seed script using the Render Shell or one-time job console.

### Frontend Provisioning (Vercel)
- [ ] Connect the repo and set root folder to `frontend`.
- [ ] Inject the environment variable `VITE_API_BASE_URL`.
- [ ] Trigger the build and confirm static route redirection configurations are applied.

### Post-Deployment Verification
- [ ] Query the backend health check `https://[backend-url]/api/status/` and confirm response is `{"status": "online"}`.
- [ ] Open the frontend URL, verify SSL certificate is active, and inspect the console to ensure no CORS or network connection blockages occur.
- [ ] Switch between tenants to verify data isolation.
