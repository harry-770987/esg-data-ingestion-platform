# Architecture Design Decisions

This document outlines key technical decisions made during the design and construction of the ESG Ingestion and Review Platform.

---

## 1. Unified Table vs. Table-per-Activity

### Context
ESG data comes in diverse formats: utility bills contain meter readings and demand charges, corporate travel has routes and cabin classes, and fuel procurement logs vehicle types and volume.

### Decision
We use a single unified `EmissionRecord` table that contains normalized fields (`normalized_quantity`, `normalized_unit`) and a generic `raw_data` JSONB column.

### Rationale
* **Consistency**: Carbon calculators require a standard interface of (Quantity, Unit, Fuel/Activity Type) to apply emission factors. A unified table simplifies this.
* **Auditability**: Keeping the raw row inside the `raw_data` JSON column preserves the source structure without cluttering the main query fields.
* **Flexibility**: New data sources can be mapped through the pipeline and written to `EmissionRecord` without needing schema migrations for every new vendor format.

---

## 2. Multi-Tenancy Strategy

### Context
Corporate compliance platforms must isolate client datasets to avoid legal issues and data leakage.

### Decision
We use a **Shared Database, Shared Schema (Tenant Column)** architecture. All queries filter by `tenant_id`.

### Rationale
* **Resource Optimization**: Perfect for a prototype/early-stage product. It keeps DB connection counts low and infrastructure simple.
* **Ease of Implementation**: Easily enforced in Django using query managers or request middleware.
* **Scalability**: For larger workloads, indices on `tenant_id` keep queries fast. Transition to tenant-specific schemas or separate databases is straightforward if compliance demands it.

---

## 3. Database-Level Lock Enforcement

### Context
Under auditing frameworks (e.g., GHG Protocol, CSRD), once carbon records are approved and reported, they must be legally immutable.

### Decision
We enforce locking checks during the `clean()` phase of the Django model lifecycle. If `locked` is True, updates to other fields are blocked.

### Rationale
* **Security**: Enforcing this at the model layer ensures that imports, manual API updates, admin panel changes, and bulk edits all pass through the security validation.
* **Transparency**: By separating the "lock" toggle from edit capabilities, analysts can trace which audit record is frozen and explicitly audit when a record was unlocked (`action="UNLOCK"` in AuditLog).

---

## 4. Ingestion Mechanism: Stateless Sync Pipelines

### Context
CSVs must be processed, cleaned, validated, normalized, and logged.

### Decision
We process CSVs synchronously inside a Django API call using Pandas.

### Rationale
* **Simplicity**: Avoids the operational overhead of Celery, Redis, or RabbitMQ for the initial prototype.
* **Immediate Feedback**: Users get instant validation, row count tallies, and error lists.
* **Scalability**: If file sizes exceed ~50MB or timeout risks arise, we can transition this design to Celery background tasks with minimal restructuring because the logic is encapsulated inside stateless pipeline helper classes.

---

## 5. Features Intentionally Skipped (Prototype Boundaries)

### A. Automated Carbon Emission Factor API Lookups
* **Decision**: We normalize physical activity metrics (e.g. `L`, `kWh`, `km`) but do not compute carbon equivalents (CO2e) automatically by querying external factor APIs (e.g., Climatiq, EPA).
* **Rationale**: Downstream carbon calculation is distinct from data ingestion. Factoring computations requires managing API keys, handling external service downtime, and dealing with geographical factor shifts. Physical normalizations are constant, and keeping calculations deferred keeps this prototype simple, deterministic, and self-contained.

### B. Persistent Cloud File Store (AWS S3 / Azure Blob Storage)
* **Decision**: We do not store raw uploaded CSV files as file objects on disk or cloud storage. Instead, the raw row contents are archived inside the `raw_data` JSONB field on the `EmissionRecord` model.
* **Rationale**: Storing raw lines in JSONB allows auditors to see the source inputs immediately alongside the normalized fields without making network roundtrips to an S3 bucket. It simplifies database backups and removes cloud-storage credentials setup.

### C. Asynchronous Task Queue (Celery / Redis / RabbitMQ)
* **Decision**: Ingestion runs synchronously in the thread handling the HTTP upload request.
* **Rationale**: For prototype loads (typically < 10,000 rows), Pandas processes data in under 2 seconds. Avoiding Celery eliminates extra services from the local install, keeping it interview-defensible and easy to run in a single container.

### D. Fine-Grained Role-Based Access Control (RBAC)
* **Decision**: We enforce strict tenant isolation via the `X-Tenant-ID` request header, but we do not distinguish roles (e.g., Ingestion Operator vs Auditor) inside a single tenant.
* **Rationale**: For a 4-day prototype, multi-tenant database isolation is the priority. Role-based API gating can be layered on top via JWT/OAuth permissions without changing the core database schema.
