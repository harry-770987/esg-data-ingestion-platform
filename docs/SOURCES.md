# Source Ingestion & Mapping Specifications

This document defines how raw data from our three target systems (SAP, Electricity Utilities, and Travel Portals) maps to our unified database schema.

---

## 1. SAP Fuel / Procurement Exports

* **Scope**: Scope 1 (Direct Emissions from fuel combustion)
* **Default Category**: `SCOPE_1_FUEL`

### Expected CSV Layout
```csv
InvoiceNo,PostingDate,Vendor,FuelType,Quantity,Unit,Cost
INV-990812,2026-05-01,FuelCorp,Diesel,120.00,gallons,450.00
INV-990813,05/12/2026,QuickGas,Petrol,500.00,liters,900.00
```

### Mapping Matrix
| Raw CSV Field | Normalized DB Field | Notes |
| :--- | :--- | :--- |
| `PostingDate` | `transaction_date` | Date parser standardizes to `YYYY-MM-DD` |
| `FuelType` | `activity_type` | E.g. "Diesel", "Petrol" |
| `Quantity` | `quantity` | Raw numeric quantity |
| `Unit` | `unit` | E.g. "gallons", "liters" |
| **Formula-driven** | `normalized_quantity` | Converts gallons to liters (`liters = gallons * 3.78541`) |
| **Static** | `normalized_unit` | Set to `'L'` (Liters) for all Scope 1 Fuel |

---

## 2. Utility Electricity Data

* **Scope**: Scope 2 (Indirect Emissions from purchased electricity)
* **Default Category**: `SCOPE_2_ELEC`

### Expected CSV Layout
```csv
BillingPeriodStart,BillingPeriodEnd,AccountNo,MeterID,UsageQuantity,UsageUnit,TotalCharge
2026-04-01,2026-04-30,ELEC-993,M-101,15.2,MWh,2280.00
2026-05-01,2026-05-31,ELEC-993,M-101,14800,kWh,2220.00
```

### Mapping Matrix
| Raw CSV Field | Normalized DB Field | Notes |
| :--- | :--- | :--- |
| `BillingPeriodEnd` | `transaction_date` | Used as the primary emission transaction date |
| **Static** | `activity_type` | Set to `"Electricity"` |
| `UsageQuantity` | `quantity` | Raw quantity |
| `UsageUnit` | `unit` | E.g. "MWh", "kWh" |
| **Formula-driven** | `normalized_quantity` | Converts MWh to kWh (`kWh = MWh * 1000`) |
| **Static** | `normalized_unit` | Set to `'kWh'` (Kilowatt-hours) |

---

## 3. Corporate Travel Platform Exports (Concur/Expedia)

* **Scope**: Scope 3 (Other indirect emissions: Business Travel)
* **Default Category**: `SCOPE_3_TRAVEL`

### Expected CSV Layout
```csv
BookingID,EmployeeID,TravelDate,Departure,Arrival,Distance,DistanceUnit,TransportType
BK-3301,EMP-882,2026-05-15,SFO,JFK,2586.00,miles,Flight
BK-3302,EMP-104,2026-05-18,LHR,CDG,348.00,km,Train
```

### Mapping Matrix
| Raw CSV Field | Normalized DB Field | Notes |
| :--- | :--- | :--- |
| `TravelDate` | `transaction_date` | Date of the trip |
| `TransportType` | `activity_type` | E.g. "Flight", "Train", "Taxi" |
| `Distance` | `quantity` | Raw distance traveled |
| `DistanceUnit` | `unit` | E.g. "miles", "km" |
| **Formula-driven** | `normalized_quantity` | Converts miles to km (`km = miles * 1.60934`) |
| **Static** | `normalized_unit` | Set to `'km'` (Kilometers) |
