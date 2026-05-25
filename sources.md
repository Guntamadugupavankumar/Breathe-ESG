# Sources

For each source: what I researched, what I learned, what the sample
data looks like, and what would break in a real deployment.

---

## Source 1: SAP Fuel and Procurement

### What I Researched

SAP's Materials Management (MM) module is where fuel and procurement
data lives. I focused on two transaction outputs:

- **MB51** (Material document list): Goods movements. This is where
  fuel consumption appears — when a plant posts a goods issue for
  diesel against a cost center, it shows up here.
- **ME2M** (Purchase orders by material): Procurement view. Shows
  purchase orders for materials with quantities and units.

The export format from these transactions via the Download to
spreadsheet button is a tab-separated or semicolon-separated flat
file. In some SAP configurations (particularly German-origin
installations), column headers are in German: MENGE (quantity),
MEINS (unit of measure), WERKS (plant), BLDAT (document date),
BWART (movement type).

### What I Learned

- SAP units of measure are SAP-internal codes, not ISO standard:
  L = liters, GL = US gallons, SCF = standard cubic feet,
  KG = kilograms, TO = metric tons
- Movement type 261 = goods issue to production (consumption),
  101 = goods receipt from purchase order. Only consumption
  movements matter for Scope 1
- Dates in YYYYMMDD format with no separator: 20240315
- Plant codes (WERKS) are client-specific four-character strings
  meaningless without a plant master table
- Material numbers (MATNR) are also client-specific and need a
  material-to-fuel-type mapping

### Sample Data and Why It Looks This Way

- DI-HSD = High-speed diesel (client material code)
- NG-CNG = Compressed natural gas
- LPG-BT = LPG for kitchen (Scope 1 but not energy combustion)
- Two plants: 1001 = Bangalore manufacturing, 2001 = Chennai warehouse
- 1,500 to 2,200 liters of diesel per fortnight is realistic for
  a mid-size Indian manufacturing plant
- Movement type 261 throughout: consumption postings only

### What Would Break in Real Deployment

1. **Custom UOM codes**: If the client configured CUB for cubic
   meters or GAL for imperial gallons, our lookup table misses them
   and flags every row

2. **Material number mapping**: We need a client-provided mapping
   from their material numbers to fuel types. Incomplete mapping
   means rows with no emission factor

3. **Plant hierarchy**: A large client with 50+ plants across
   geographies needs per-plant grid intensity for any Scope 2
   electricity in this export

4. **Non-standard movement types**: If the client uses Z61 or Z201
   as custom goods issue types, our filter misses them

5. **Currency fields**: Some exports include cost fields. If they
   shift column index unexpectedly, parsing breaks

---

## Source 2: Utility Electricity

### What I Researched

I looked at portal CSV exports from three utilities:

- **BESCOM** (Bangalore Electricity Supply Company): Portal at
  bescom.org offers consumption history CSV downloads
- **MSEDCL** (Maharashtra State Electricity Distribution):
  Mahavitaran portal offers similar CSV but uses kVAh not kWh
- **Green Button Alliance**: US standard XML format used by large
  American utilities and the ESPI API

### What I Learned

- Billing periods do not align with calendar months. BESCOM bill
  cycles fall on the 12th of each month, so a January bill covers
  December 12 to January 12
- Some exports give cumulative meter readings (previous and current)
  rather than consumption directly — you must subtract
- High-tension connections used by large industrial clients have
  separate demand charges (kVA) and energy charges (kWh)
- Multi-meter sites export as separate files per meter or as a
  combined file with a meter ID column
- MSEDCL uses kVAh which includes reactive power — converting to
  kWh requires knowing the power factor

### Sample Data and Why It Looks This Way
- Two meters (MT001, MT002) for same consumer — common for a
  factory with main connection and separate office connection
- Billing periods start on the 12th, not the 1st
- prev_reading + consumption = curr_reading verifiable:
  45230 + 1550 = 46780 correct
- February period runs to March 14 — a correction cycle catch-up
- HT-2A = BESCOM High Tension tariff category 2A (industrial)
- 1,550 kWh per month for MT001 is realistic for a mid-size
  industrial facility

### What Would Break in Real Deployment

1. **kVAh vs kWh**: MSEDCL exports kVAh. Without the power factor
   we cannot accurately convert. Need client's average power factor
   or use default 0.9 with a flag

2. **Multi-utility, multi-site**: Large enterprise with offices
   across 10 Indian states has a different utility per state, each
   with a different CSV format. We handle one format only

3. **Estimated readings**: Many exports flag estimated readings with
   an E marker when the meter reader did not get access. These are
   corrected in the following bill and should be flagged separately

4. **T&D losses**: Scope 2 factors should include transmission and
   distribution losses. IEA factors include average T&D loss but
   precise reporting may require per-utility loss data

---

## Source 3: Corporate Travel

### What I Researched

I read the Navan (formerly TripActions) developer documentation and
the Concur Travel API documentation. Both offer RESTful APIs for
pulling trip reports, expense reports, and booking data.

Key insight: travel platforms expose booking data, not actual travel.
A booking can be changed or cancelled after export. This creates a
delta problem — a June export might include May trips that were
rebooked.

I also researched ICAO's Carbon Emissions Calculator methodology:
distance uses great-circle with a 1.09 route factor for indirect
routing, adjusted by aircraft type and passenger load factor.

### What I Learned

- Distance is not always in the API response. Navan includes it for
  car rentals and some rail. Flights often only have airport codes
- Class of service matters significantly: business class is 2.8x
  the economy emission factor per ICAO (seat pitch allocation)
- Hotel emissions use spend-based approach — cost times EF per
  dollar — which is imprecise but the only option without
  property-level energy data
- Ground transport often listed as company car or taxi without
  vehicle type — electric vs petrol makes a large difference

### Sample Data and Why It Looks This Way

```json
[
  {
    "trip_id": "T-20240301-001",
    "traveler_email": "priya.s@acme.com",
    "segments": [
      {
        "segment_id": "S001",
        "type": "flight",
        "origin": "BLR",
        "destination": "DEL",
        "departure_date": "2024-03-01",
        "class_of_service": "economy",
        "distance_km": null,
        "carrier": "6E",
        "amount": 8500,
        "currency": "INR"
      },
      {
        "segment_id": "S002",
        "type": "hotel",
        "city": "New Delhi",
        "check_in": "2024-03-01",
        "check_out": "2024-03-03",
        "nights": 2,
        "amount": 12000,
        "currency": "INR"
      }
    ]
  }
]
```

- BLR to DEL is a realistic Indian domestic route (1,740 km
  great-circle, 1,897 km with route factor)
- distance_km is null on flights — we compute from IATA codes
- Carrier 6E = IndiGo, realistic for Indian domestic business travel
- Hotel with no property name — spend-based EF applied
- economy class applies 1.0x ICAO seat factor vs 2.8x for business

### What Would Break in Real Deployment

1. **Airport code gaps**: Our database has ~20 major airports. It
   misses private airfields, regional airports, and mixes IATA with
   ICAO codes in some booking systems

2. **Cancelled and amended trips**: A June export may contain May
   trips rebooked in June. Without delta detection on trip_id and
   segment_id we double-count

3. **Rail emission factors**: Indian Railways has a very low emission
   factor (grid-fed electric traction). We have no per-route rail
   factors

4. **Hotel physical data**: Spend-based hotel EF is a 2x to 5x
   approximation. For clients with significant hotel spend in
   low-energy markets like Scandinavia this massively overstates
   Scope 3 Category 6

5. **Multi-leg connections**: A BLR to LHR via DEL booking comes
   through as two segments. Without knowing they are connected we
   may count them as independent trips