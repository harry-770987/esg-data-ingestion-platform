# Database Model Documentation

This document describes the schema, database relations, and validation rules for the ESG Data Ingestion Platform.

---

## Entity Relationship Overview

The data model uses a standard normalized relational structure to support strict enterprise auditability, multi-tenancy, and review states.

```
+------------+        +---------------+        +-------------+
|   Tenant   |<-------|  DataSource   |<-------| UploadBatch |
+------------+        +---------------+        +-------------+
      ^                      ^                        ^
      |                      |                        |
      +--------------+-------+-------+----------------+
                     |
            +----------------+
            | EmissionRecord |
            +----------------+
              ^            ^
              |            |
         +----------+ +-----------------+
         | AuditLog | | ApprovalHistory |
         +----------+ +-----------------+
```

---

## Model Explanations & Schema

### 1. Tenant
* **Purpose**: Isolates all database records to a specific client company.
* **Key Fields**:
  * `id`: UUID (Primary Key). Prevents sequential enumeration security vulnerabilities.
  * `name`: Unique CharField naming the organization.

### 2. DataSource
* **Purpose**: Represents the source origin. Used by compliance auditors to verify raw records back to system of origin (e.g., utility bill vs. ERP system).
* **Key Fields**:
  * `tenant`: ForeignKey (Tenant).
  * `source_type`: Choice field restricted to `SAP_FUEL` (Scope 1), `UTILITY_ELEC` (Scope 2), `TRAVEL_CORP` (Scope 3).
  * `is_active`: Boolean flag indicating if ingestion from this source is active.
* **Uniqueness Constraints**: A tenant cannot have duplicate data sources with the exact same name (`unique_together = ('tenant', 'name')`).

### 3. UploadBatch
* **Purpose**: Tracks a single file import execution. Used to manage files, count rows, log processing errors, and execute bulk rollbacks.
* **Key Fields**:
  * `status`: Choiced string tracking batch progression (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`).
  * `total_rows`, `processed_rows`, `failed_rows`: Numerical counters used in dashboards.
  * `error_summary`: Text field logging execution stack traces.

### 4. EmissionRecord
* **Purpose**: The unified, normalized target table containing activity data for carbon calculations.
* **Key Fields**:
  * `tenant` & `data_source` & `upload_batch`: Reference fields establishing complete provenance.
  * `category` & `scope`: Business classification (e.g. Scope 1, Scope 2, Scope 3).
  * `quantity` & `unit`: Raw data parsed from the file.
  * `normalized_quantity` & `normalized_unit`: System-converted values mapped to standard units (e.g. `kWh`, `L`, `km`).
  * `suspicious`: Flag indicating row-level validation anomalies (e.g., negative values, outlier amounts).
  * `suspicious_reasons`: JSON list containing specific reasons for suspicion.
  * `approved` / `locked`: Triggers for locking the record.
  * `raw_data`: JSON field saving the exact key-value pairs of the original CSV row.
* **Locking Enforcement**: Enforced at the model level via `clean()` and `save()`. If the record is locked (`locked=True`), any attempt to edit data fields is blocked. The only permitted action is an unlock request.

### 5. AuditLog
* **Purpose**: Complete immutable transaction log showing who edited what fields. Necessary for carbon accounting audits (PwC/EY readiness).
* **Key Fields**:
  * `emission_record`: Pointer to the altered record.
  * `changed_by`: Reference to the modifying User.
  * `action`: Action type (`CREATE`, `EDIT`, `LOCK`, `UNLOCK`).
  * `previous_values` / `new_values`: JSON snapshots containing old and new key-value states.

### 6. ApprovalHistory
* **Purpose**: Captures sign-offs, rejections, and qualitative comments from analysts.
* **Key Fields**:
  * `action`: Action type (`APPROVE`, `REJECT`).
  * `comments`: Qualitative text describing reasons for rejection or verification checks.
