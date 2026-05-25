# Data Model

## Philosophy

Every row of emissions data must be fully traceable from its final
tCO₂e number back to the original source byte. Every row carries:
- Its provenance (which file, which line, when, who touched it)
- Its unit state before and after normalization
- Its scope assignment with justification
- Whether it has been analyst-approved and audit-locked

---

## Core Tables

### `Tenant`

Multi-tenancy is enforced at the database level via a `tenant_id`
foreign key on every data-bearing table. There is no cross-tenant
join anywhere in the application.

---

### `IngestionRun`

Every upload creates an IngestionRun. It records the source type,
raw payload checksum, timing, and final status. If a row later needs
to be traced to its origin, the chain is:
EmissionRow → IngestionRun → raw file.

---

### `EmissionRow`

The central fact table. One row = one discrete activity event.

**Why raw_* fields are preserved**: An auditor may ask what the
original file said. We never lose the pre-normalization state.

**Why ef_value is a snapshot**: Emission factors change annually.
We record the factor at computation time so re-running two years
later does not silently change historical numbers.

---

### `EmissionFactor`

Lookup table of activity-to-CO₂e conversion factors. Sourced from
DEFRA 2023, IEA 2022, and ICAO 2023.

---

### `EditLog`

Every manual edit to an EmissionRow after ingestion is recorded here.
This is the audit trail that auditors care about.

---

## Scope Assignment Logic

| Source                        | Default Scope | Override Condition              |
|-------------------------------|---------------|---------------------------------|
| SAP fuel (diesel, LPG, CNG)   | Scope 1       | If purchased for resale → S3   |
| SAP procurement               | Scope 3 cat1  | If electricity → Scope 2        |
| Utility electricity           | Scope 2       | If on-site solar → Scope 1      |
| Air travel                    | Scope 3 cat6  | —                               |
| Ground transport (co. vehicle)| Scope 1       | If employee-owned → Scope 3     |
| Hotel stays                   | Scope 3 cat6  | —                               |

---

## Unit Normalization

All quantities normalized before emission factor application:

- **Energy**: kWh (from gallons, liters, SCF, therms, BTU)
- **Distance**: km (from miles using 1.60934)
- **Mass**: kg (from lbs, tonnes, short tons)
- **Volume → energy**: liters of diesel → kWh at 10.7 kWh/litre

Raw value always preserved in raw_quantity / raw_unit.

---

## Multi-tenancy

- Every table has tenant_id with NOT NULL constraint
- Custom TenantManager scopes all querysets automatically
- JWT token encodes tenant_id
- File storage uses tenant/{tenant_id}/runs/{run_id}/ prefixing

---

## What This Model Does Not Handle

- Scope 3 categories 2–5, 7–15 (model supports via category field,
  ingestors only produce categories 1 and 6)
- Biogenic CO₂ separation from fossil CO₂
- Market-based vs location-based Scope 2 (location-based only)