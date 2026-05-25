# Tradeoffs

Three things I deliberately did not build, and why.

---

## 1. PDF Bill Parsing for Utility Data

**What it would enable**:
Analysts could upload the PDF electricity bills their facilities
team already receives, instead of separately exporting a CSV from
the utility portal. This matters because not all utilities have a
clean portal export, and some clients receive bills from 10+ utilities
in PDF form.

**Why I skipped it**:
PDF parsing is deceptively hard in production.

- The approach that works for BESCOM bills fails for MSEDCL bills
  because the column layout is different
- Scanned bills need OCR — a real occurrence with older utilities
- Any parser built in 4 days would be brittle and break the moment
  the utility redesigned their bill template

The right solution is a purpose-built document-AI pipeline — a
multimodal model fine-tuned on utility bill formats, with
human-in-the-loop for low-confidence extractions. That is at minimum
a week of work and the wrong bet for a prototype whose goal is to
demonstrate the normalization and review flow.

**What I did instead**:
CSV upload from the utility portal, which is available on every
portal I checked. This covers the 80% case cleanly.

**How I would add it later**:
Build a separate microservice using a vision-capable model to extract
structured fields from PDF bills. Output feeds into the same
IngestionRun pipeline with source_type = UTILITY_PDF. The core
data model does not need to change.

---

## 2. Real-Time API Pull from Concur or Navan

**What it would enable**:
Instead of the sustainability lead manually exporting a trip report
and uploading it, the system would pull new trips automatically on a
schedule (daily or weekly). This closes the gap between travel
happening and it appearing in the review queue.

**Why I skipped it**:
A real Concur or Navan API integration requires:

- Registering as an OAuth application with the platform
- The client granting OAuth access (requires their IT admin)
- Handling token refresh, pagination, and API rate limits
- Building a background task scheduler (Celery + Redis)

Each of those is a day of work on its own. The OAuth registration
alone cannot be done in 4 days because it requires Concur or Navan
to approve the application.

More importantly, the prototype is evaluating the data model and
review flow, not the plumbing for API connectivity. File upload
demonstrates the same normalization and review logic without the
OAuth ceremony.

**What I did instead**:
File upload of a JSON export in Navan trip report format. The data
model and normalization code are fully API-pull-ready. Swapping the
upload handler for a scheduled API pull is a contained change that
does not touch any core logic.

**How I would add it later**:
Add a Celery beat task that calls the Navan API every 24 hours,
stores the raw response as an IngestionRun, and runs the same
parse_travel_json parser on the result. The analyst review flow
is identical.

---

## 3. Market-Based Scope 2 Accounting

**What it would enable**:
Companies that have purchased renewable energy certificates (RECs)
or Power Purchase Agreements (PPAs) can report Scope 2 emissions
under the market-based method, which can be substantially lower than
location-based (grid average) emissions.

The GHG Protocol requires companies to report both methods if they
use market-based. For a client with a significant renewables
commitment, the difference between location-based and market-based
Scope 2 can be the difference between a good ESG story and a great
one.

**Why I skipped it**:
Market-based Scope 2 requires:

- A separate data model for energy attribute certificates
  (EACs and RECs)
- A matching algorithm pairing consumption rows with certificate rows
- Tracking which electricity is covered by which certificate,
  at what price, from which generator, for which period
- A separate reporting path that shows both methods side by side

This would double the complexity of the utility ingestion and
reporting modules. It is the most commercially important missing
feature for enterprise clients, but the wrong scope for 4 days.

**What I did instead**:
Location-based Scope 2 using IEA 2022 India grid average intensity
(0.708 kgCO2e per kWh). The system flags electricity rows in the
review UI with a note that market-based accounting may apply if
the client holds RECs.

**How I would add it later**:
Add an EnergyAttributeCertificate model with fields for certificate
type, generator, period, and kWh covered. Add a matching service
that pairs certificates against EmissionRows. Add a second
ef_market_based field to EmissionRow. The reporting view then
shows both totals. The data model already has room for this —
no migration breaking changes required.