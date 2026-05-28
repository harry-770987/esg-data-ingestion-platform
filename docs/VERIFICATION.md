# Platform Verification & Reviewer Walkthrough Guide

This document contains step-by-step instructions to verify a live deployment and outlines a structured walk-through for evaluators to test all features of the ESG Data Ingestion Platform.

---

## 1. Deployment Verification Checklist

Verify that the cloud infrastructure services are configured and communicating correctly.

- [ ] **Health Endpoint Check**: Access `https://[backend-url]/api/status/` and verify that it returns `{"status":"online",...}` with HTTP 200.
- [ ] **SSL / Security Headers**: Confirm the server redirects HTTP to HTTPS and sets `Strict-Transport-Security`.
- [ ] **CORS Settings**: Confirm that the API blocks origins other than the registered Vercel frontend domain (returns CORS policy block in browser console if queried from unlisted domains).
- [ ] **Database Connection & Seeding**: Verify that seed logs are present in the backend stdout during the deployment cycle and that the default database tables have been successfully generated.

---

## 2. Production Verification Checklist

Verify core runtime safety measures.

- [ ] **Tenant Isolation (Mandatory)**: 
  - Execute a query to `https://[backend-url]/api/records/` with header `X-Tenant-ID: 11111111-1111-1111-1111-111111111111`. Note the returned records.
  - Switch the header to `X-Tenant-ID: 22222222-2222-2222-2222-222222222222`. Confirm that the records are completely separate and contain no overlapping UUID instances.
- [ ] **Immutability Gating**: 
  - Identify a record with `locked=true`.
  - Issue a direct `PATCH` request to update its quantity.
  - Verify that the API rejects the request with HTTP 400 or 403, and the message highlights that the record is locked for auditing.

---

## 3. Demo Walkthrough Steps

Follow these click-by-click instructions to test the platform.

### Step 1: Accessing the Console
1. Open the Vercel web URL in your browser.
2. In the top-right header, confirm the **Backend Status** badge is green and displays **ONLINE**.
3. Verify that the **Tenant** dropdown defaults to **Alpha Corporate Client**.

### Step 2: Uploading Dirty Activity Data
1. Navigate to the **Upload CSV** tab on the sidebar.
2. Under "Select Ingestion Target Category", select **SAP Fuel Procurement (Scope 1)**.
3. Drag and drop the sample file `sample_data/sap_fuel_exports.csv` into the dropzone (or click to select it).
4. Click **Start Ingestion Pipeline**.
5. Observe the success dialog listing:
   - Total rows processed: **6**
   - Successfully loaded: **2**
   - Suspicious (Warnings): **4** (these represent rows containing validation problems like negative values, extreme outliers, or missing date columns).

### Step 3: Inspecting Compliance Warnings
1. Navigate to the **Review Actions** page.
2. You will see a list of records flagged as **Suspicious** from the file upload.
3. Locate the entry with the negative quantity (`Quantity: -50.00 liters`). Click **Audit Row**.
4. Inside the modal, note the validation warning alert: `Quantity must be greater than zero`.

### Step 4: Corrections & Recalculation
1. In the open audit modal, correct the quantity from `-50.0` to `50.0`.
2. Click **Save Corrections**.
3. Observe the green success banner: `Record corrections saved successfully!`.
4. Note that the **Quality State** badge changes from **Suspicious** to **Verified Clean** because the correction resolves all pipeline assertions.

### Step 5: Approval & Locking
1. Open the audit modal for the same corrected record.
2. Enter comments in the Auditor Comments box: *"Corrected keypunch error (invoice quantity negative value typo)."*
3. Click **Approve & Lock Record**.
4. Confirm the success banner: `Record approved and locked for auditing!`.
5. The row changes to a locked state; any future edit attempts are blocked.

### Step 6: Reviewing the Audit Ledger
1. Navigate to **Audit History**.
2. Examine the timeline card corresponding to your action.
3. Observe that the entry shows:
   - The action type: `EDIT`
   - Who modified the data: `auditor` (or System Pipeline)
   - Timestamps and record IDs
   - A clear side-by-side diff:
     - `Quantity: -50.0 -> 50.0`
     - `Normalized Quantity: None -> 50.0`
     - `Cost: -90.0 -> -90.0` (if applicable)

---

## 4. Reviewer Testing Flow

Evaluators can verify robust engine bounds by testing these edge cases:

| Action Tested | Input Vector | Expected System Behavior |
| :--- | :--- | :--- |
| **Statistical Outlier Flagging** | Upload `utility_electricity_exports.csv` | The row with `850.0 MWh` is flagged as Suspicious. The warning box highlights that it exceeds the Median Absolute Deviation limit by more than 4.5 MADs. |
| **Future Date Detection** | Upload `utility_electricity_exports.csv` | The row with billing period ending in `2028-12-31` is flagged as Suspicious. The warning logs state: `Transaction date is in the future`. |
| **Malformed Header Upload** | Upload an arbitrary CSV without quantity headers | The ingestion aborts, rolling back the database transaction. The Upload Batch history logs the status as `FAILED` and shows the parser trace. |
| **Tamper Attempt on Audit Log** | Direct HTTP PATCH on a locked record | The request is rejected by model validation, preserving raw parameters. |
