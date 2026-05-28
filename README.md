# ESG Data Ingestion & Auditing Platform

A high-integrity prototype of an ESG (Environmental, Social, and Governance) data ingestion pipeline and review system. Designed to parse disparate activity exports (SAP Fuel records, Utility Bills, Travel Portals), normalize carbon-accounting parameters to standard metrics, isolate tenants, and provide an immutable audit log for compliance validation.

---

## 1. Project Overview & Architecture

### System Architecture
The platform is designed around a decoupled Single Page Application (SPA) frontend and a RESTful backend API:

```
+------------------------------------------+
|            React Frontend                |  Vercel Edge Network
|    (Tenant Swapping, Dashboard, Inbox)   |
+------------------------------------------+
                     |  HTTPS REST Requests
                     v  (with X-Tenant-ID Header)
+------------------------------------------+
|            Django REST API               |  Render Python Runtime
|  (HasTenantPermission, Ingestion API)    |
+------------------------------------------+
                     |  OR-Mapping
                     v
+-----------------------+  +---------------+
|    Pandas Pipeline    |  |  PostgreSQL   |  Render Managed DB
| (MAD Outlier Detection|  | (Normalized   |  (Atomic Transactions)
|  & Unit Normalizer)   |  |  Data, Logs)  |
+-----------------------+  +---------------+
```

### Components
1. **Django Backend (`/backend`)**: Exposes REST endpoints, validates tenant permissions, handles transaction-safe bulk insert tasks, and enforces model-level data locks.
2. **Pandas Ingestion Engine (`/backend/ingestion`)**: Automatically maps headers, parses timestamps, standardizes units (Gallons/Liters to `L`, MWh to `kWh`, Miles to `km`), and executes Median Absolute Deviation (MAD) anomaly checks.
3. **React Frontend (`/frontend`)**: Responsive audit console styled with Tailwind CSS and Lucide React icons, featuring tenant-isolated views, loading states, and edit modals.

---

## 2. API Specifications

All endpoints require the custom header `X-Tenant-ID` containing a tenant UUID (e.g. `11111111-1111-1111-1111-111111111111`) to enforce data isolation.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/status/` | Health check endpoint (does not require tenant header). |
| `GET` | `/api/records/` | List and filter normalized emission records. |
| `POST` | `/api/batches/upload/` | Ingest activity CSV data. Parameters: `file` (multipart), `source_type` (`SAP_FUEL`, `UTILITY_ELEC`, `TRAVEL_CORP`). |
| `PATCH`| `/api/records/{id}/` | Update physical values of a record (fails if record is locked). |
| `POST` | `/api/records/{id}/approve/` | Approve a record. Sets `approved=True` and `locked=True`. Logs event in `ApprovalHistory`. |
| `POST` | `/api/records/{id}/reject/` | Reject a record. Resets approval state. |
| `POST` | `/api/records/{id}/unlock/` | Unlock a locked record (requires audit comments, adds event to `AuditLog`). |
| `GET` | `/api/audit-logs/` | Fetch the tenant's immutable change ledger. |

---

## 3. Local Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- SQLite or PostgreSQL

### Backend Setup
1. Navigate to `/backend` and create a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   ./venv/Scripts/activate # On Windows
   source venv/bin/activate # On Unix
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up the local database and seed test accounts:
   ```bash
   python manage.py migrate
   python manage.py seed_data
   ```
4. Start the development server:
   ```bash
   python manage.py runserver
   ```

### Frontend Setup
1. Navigate to `/frontend` and install packages:
   ```bash
   cd ../frontend
   npm install
   ```
2. Run the development server:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser.

---

## 4. Production Deployment Instructions

For complete step-by-step production setup, refer to [DEPLOYMENT.md](file:///c:/Users/ASUS/Desktop/assignment2/docs/DEPLOYMENT.md).

* **Backend**: Deployed to **Render** using [render.yaml](file:///c:/Users/ASUS/Desktop/assignment2/render.yaml) and [Procfile](file:///c:/Users/ASUS/Desktop/assignment2/backend/Procfile).
* **Frontend**: Deployed to **Vercel** with build environment pointing `VITE_API_BASE_URL` to the Render app API.

---

## 5. Engineering Assumptions & Tradeoffs

See the comprehensive documents in `/docs` for detailed analysis:
- **Data Schema & Models**: [MODEL.md](file:///c:/Users/ASUS/Desktop/assignment2/docs/MODEL.md)
- **Architecture & Pipeline Choices**: [DECISIONS.md](file:///c:/Users/ASUS/Desktop/assignment2/docs/DECISIONS.md)
- **Evaluated Tradeoffs**: [TRADEOFFS.md](file:///c:/Users/ASUS/Desktop/assignment2/docs/TRADEOFFS.md)
- **Source System Mapping Standards**: [SOURCES.md](file:///c:/Users/ASUS/Desktop/assignment2/docs/SOURCES.md)

### Key Decisions
* **Tenancy**: Column-based tenant mapping (`tenant_id` foreign key) was chosen over independent database schemas to fit a rapid 4-day prototyping cycle, keeping migration complexity low.
* **Sync Pipeline**: Synchronous CSV processing via Pandas. For records up to 10k rows, execution finishes in under 2 seconds, which is optimal for web requests without introducing Celery queue complexity.
* **Database Locking**: Model-level validation overrides are utilized to ensure that once a carbon record is approved, it cannot be modified by any raw SQL updates without an unlock audit trail.
