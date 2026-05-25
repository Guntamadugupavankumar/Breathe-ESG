# Decisions

Every ambiguity I resolved, what I chose, and why.

---

## SAP: Format Choice

**Ambiguity**: SAP exposes data via IDoc, OData, BAPI, and flat-file
exports. Which one?

**Choice**: SAP flat-file export in tab-separated CSV format,
specifically the output from MB51 (material document list) or ME2M
(purchase orders by material) transactions.

**Why not IDoc**: Requires setting up ALE/EDI integration with the
client's SAP landscape. Takes weeks of IT involvement and SAP Basis
expertise. Not realistic for an onboarding prototype.

**Why not OData/BAPI**: Requires the client's SAP to expose an API
endpoint outside their corporate firewall. Most enterprise clients
will not open their SAP system to external SaaS without significant
IT and security sign-off.

**Why flat-file**: This is what actually happens. A sustainability
lead asks IT to schedule a monthly report export. IT drops a file on
a shared drive. The sustainability team uploads it manually. This is
the 80% case at enterprise clients.

**What I handled**:
- MB51-style flat file with columns: MANDT, WERKS, MATNR, BWART,
  MENGE, MEINS, BLDAT, KOSTL
- German and English column header variants
- Movement types: 201, 261, 551 (consumption postings only)
- Units: L, GL, GLI, KG, TO, SCF, MCF, M3

**What I ignored**:
- IDoc segment parsing
- OData $batch queries
- Material valuation and costs
- Full 800-column MM standard structure

**What I'd ask the PM**:
"Can you get a sample export from the client's SAP before we build?
Which transaction code does their team use? Are they on S/4HANA or
ECC? The field layouts differ between versions."

---

## SAP: Plant Code Lookup

**Ambiguity**: SAP plant codes (WERKS) are four-character codes
meaningful only within that client's configuration. Without a lookup
table we cannot determine geography for emission factors.

**Choice**: The ingestion UI asks the user to upload a
plant-code-to-region mapping CSV alongside the SAP file. If no
mapping is provided, plant codes are stored as-is and the row is
flagged for analyst review.

**What I'd ask the PM**:
"Does the client have an existing plant master data export? Can IT
provide the T001W table dump?"

---

## Utility: Ingestion Mechanism

**Ambiguity**: Utility data comes from portal CSV exports, PDF bills,
or utility APIs. Which to support?

**Choice**: Portal CSV export.

**Why not PDF**: PDF parsing is fragile. Each utility has a different
bill layout. Scanned bills need OCR. Any parser built in 4 days would
break the moment the utility redesigned their bill template. In
production this needs a dedicated document-AI pipeline.

**Why not API**: APIs exist only at large US utilities (Green Button).
Not available for BESCOM, MSEDCL, Tata Power, or most Indian and
European utilities.

**Why CSV**: Nearly every utility portal offers CSV export. BESCOM,
MSEDCL, and national equivalents all have it. This is the most
realistic starting point.

**What I handled**:
- BESCOM-style CSV with meter_id, billing_period_start,
  billing_period_end, consumption_kwh, tariff_code
- Billing periods that don't align with calendar months
- Multi-meter sites (multiple rows per consumer)

**What I ignored**:
- kVAh vs kWh distinction (MSEDCL exports kVAh)
- Time-of-use tariff structures
- Estimated vs actual meter readings
- Green Button API format

**What I'd ask the PM**:
"Which utilities does this client use? I need a sample export from
each — they all have slightly different column names."

---

## Travel: API vs File Upload

**Ambiguity**: Concur and Navan have APIs. Should I pull from the
API directly or let users upload an export?

**Choice**: File upload of a JSON export.

**Why not API**: Requires OAuth client registration with the travel
platform. Needs client IT involvement and legal review of data-sharing
agreements. OAuth registration alone cannot be done in 4 days because
it requires Concur/Navan to approve the app.

**Why file upload**: Both Concur and Navan allow exporting trip
reports as JSON. The data model and normalization code are
API-pull-ready — swapping the upload handler for a scheduled pull is
a contained change that does not touch core logic.

**Format chosen**: Navan-style trip report JSON with trip_id,
traveler_email, and segments array (flight, hotel, ground).

**Distance handling**: When distance_km is absent, great-circle
distance is computed from IATA airport codes using the OpenFlights
coordinate dataset. Route factor of 1.09 applied per ICAO methodology.

**What I ignored**:
- Per-employee allocation for multi-traveler bookings
- Trip purpose codes (business vs personal)
- Car rental fleet type (EV vs petrol)
- Rail emission factors

**What I'd ask the PM**:
"Is the client on Concur or Navan? Can you get a sample trip export
from their last quarter? Do they want per-employee or aggregate
emissions?"

---

## Review and Approval Flow

**Ambiguity**: "Approve rows before they go to auditors" — row-by-row
or batch?

**Choice**: Both.
- Analysts can approve individual rows
- Analysts can bulk-approve all PENDING rows in a run
- A row can be rejected (returns to PENDING with required reason)
- A row can be flagged (marks suspicious, keeps in flow)

Once approved and locked, audit_locked = true and the row becomes
read-only at the API level. The only way to change a locked row is to
create a new IngestionRun that supersedes it.

---

## Emission Factors

**Choice**: Bundled static table seeded from:
- DEFRA 2023 (UK, used as global default for fuel)
- IEA 2022 grid intensity (India national average: 0.708 kgCO2e/kWh)
- ICAO 2023 (aviation: 0.1153 kgCO2e per passenger-km)

No EF management UI built. Factors loaded via Django management
command. In production this would be a versioned managed dataset with
a UI for the Breathe ESG team to update annually.

---

## Authentication

**Choice**: JWT via djangorestframework-simplejwt. Token lifetime 8
hours with 7-day refresh. No SSO/SAML for the prototype.

In production, enterprise clients would need SSO integration
(Okta, Azure AD, Google Workspace).

---

## Deployment

**Choice**: Railway for backend (Django + SQLite), Vercel for
frontend (React + Vite).

Railway was chosen because it supports Python out of the box with
zero configuration, gives a persistent filesystem for SQLite, and
has a free tier sufficient for a prototype demo.

Vercel was chosen for the frontend because it deploys Vite/React
apps with a single command and provides instant CDN-backed hosting.