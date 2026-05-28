# Engineering Tradeoffs

This document details the trade-offs evaluated during the development of this ESG prototype.

---

## 1. Column-Based Tenancy vs. Schema-Based Isolation

| Approach | Pros | Cons |
| :--- | :--- | :--- |
| **Column-Based (Selected)** | Simple setup, fast migrations, works on single database, low cost. | Potential data leakage if developer forgets to filter querysets. |
| **Schema-Based Isolation** | Strict separation, independent database tables per client. | Complex migrations, slower reporting across all tenants, higher database overhead. |

* **Trade-off Decision**: We chose Column-Based tenancy. In a 4-day prototype, minimizing setup complexity is vital. We mitigate data leakage risks by structuring DRF Viewsets to always filter querysets by the header `X-Tenant-ID`.

---

## 2. Pandas Processing vs. Native Python CSV Library

| Approach | Pros | Cons |
| :--- | :--- | :--- |
| **Pandas (Selected)** | Built-in date parsers, vector-based unit conversion, standard deviation outlier helper functions. | Heavy memory consumption on massive files, adds external dependencies. |
| **Native Python CSV** | Extremely low memory footprint, zero dependencies, fast for simple row operations. | High boilerplate code for date parsing and statistical analysis. |

* **Trade-off Decision**: We chose Pandas. ESG processing relies on validation heuristics and statistical checks (such as finding anomalies 3 standard deviations from the mean). Pandas handles these calculations in a single line.

---

## 3. Synchronous Ingestion vs. Async Queue (Celery/Redis)

| Approach | Pros | Cons |
| :--- | :--- | :--- |
| **Synchronous Ingestion (Selected)**| Simple API structure, no extra servers needed, instant user feedback. | Blocked connection if files are very large (timeout risks on Render). |
| **Asynchronous (Celery)** | Non-blocking, handles extremely large datasets (GBs), highly scalable. | Demands infrastructure configuration (Redis/RabbitMQ), more complex UI state. |

* **Trade-off Decision**: We chose Synchronous Ingestion. For prototype uploads (typically 100 - 10,000 rows), synchronous execution finishes in less than 2 seconds, which is well within normal HTTP limits.

---

## 4. Built-in Audit Fields vs. Separate AuditLog Ledger

| Approach | Pros | Cons |
| :--- | :--- | :--- |
| **Separate AuditLog (Selected)** | Clear timeline history, holds previous/new snapshots, satisfies third-party audit goals. | Additional database writes, increased storage overhead. |
| **Simple Fields (e.g., modified_by)** | Zero complexity, simple columns on the primary table. | No historical traceability of previous values (overwritten on save). |

* **Trade-off Decision**: We chose a separate `AuditLog` table. Under standard compliance rules, auditing demands knowing the exact historical values before modifications occurred to prevent fraudulent adjustments of carbon numbers.
