import csv
import json
import io
import math
from datetime import datetime, date
from decimal import Decimal


# ── SAP UNIT CONVERSIONS ─────────────────────────────────────────────────────

SAP_UOM_TO_LITERS = {
    'L': 1.0, 'LTR': 1.0,
    'GL': 3.78541,
    'GAL': 3.78541,
    'GLI': 4.54609,
}

SAP_UOM_TO_KG = {
    'KG': 1.0, 'KGM': 1.0,
    'TO': 1000.0, 'T': 1000.0,
    'LB': 0.453592,
}

SAP_UOM_TO_SCF = {
    'SCF': 1.0,
    'MCF': 1000.0,
    'M3': 35.3147,
}


# ── FUEL EMISSION FACTORS (kgCO2e per unit) ──────────────────────────────────

FUEL_FACTORS = {
    'diesel': {'unit': 'liter', 'factor': Decimal('2.68')},
    'petrol': {'unit': 'liter', 'factor': Decimal('2.31')},
    'lpg':    {'unit': 'kg',    'factor': Decimal('1.51')},
    'cng':    {'unit': 'scf',   'factor': Decimal('0.0543')},
}

MATERIAL_FUEL_MAP = {
    'DI-HSD': 'diesel', 'HSD': 'diesel', 'DIESEL': 'diesel',
    'MS-PET': 'petrol', 'PETROL': 'petrol', 'GASOLINE': 'petrol',
    'LPG': 'lpg', 'LPG-BT': 'lpg', 'LPG-IND': 'lpg',
    'NG-CNG': 'cng', 'CNG': 'cng', 'NAT-GAS': 'cng',
}

SAP_CONSUMPTION_MOVEMENT_TYPES = {
    '201', '261', '551', '601', 'Z61', 'Z201'
}

SAP_FIELD_ALIASES = {
    'MENGE': 'quantity', 'Quantity': 'quantity', 'QUANTITY': 'quantity',
    'MEINS': 'uom', 'Unit': 'uom', 'UOM': 'uom',
    'WERKS': 'plant', 'Plant': 'plant', 'PLANT': 'plant',
    'MATNR': 'material', 'Material': 'material', 'MATERIAL': 'material',
    'BWART': 'mvt_type', 'Movement Type': 'mvt_type', 'MVT': 'mvt_type',
    'BLDAT': 'doc_date', 'Document Date': 'doc_date', 'Date': 'doc_date',
    'KOSTL': 'cost_center', 'Cost Center': 'cost_center',
}


def _parse_sap_date(raw):
    for fmt in ('%Y%m%d', '%d.%m.%Y', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def parse_sap_flat_file(file_content, source_ref_prefix='line'):
    rows, errors = [], []

    delimiter = '\t' if '\t' in file_content[:500] else ';'
    if delimiter not in file_content[:500]:
        delimiter = ','

    reader = csv.DictReader(io.StringIO(file_content), delimiter=delimiter)

    for line_num, raw_row in enumerate(reader, start=2):
        col_map = {h: SAP_FIELD_ALIASES.get(h, h) for h in raw_row.keys()}
        row = {col_map.get(k, k): v for k, v in raw_row.items()}

        mvt_type = row.get('mvt_type', '').strip()
        if mvt_type and mvt_type not in SAP_CONSUMPTION_MOVEMENT_TYPES:
            continue

        material = row.get('material', '').strip().upper()
        fuel_type = MATERIAL_FUEL_MAP.get(material)

        if not fuel_type:
            errors.append({
                'row': line_num,
                'field': 'material',
                'message': f'Unknown material code: {material!r}. Flagged for review.'
            })

        try:
            quantity = Decimal(row.get('quantity', '0').replace(',', '.'))
        except Exception:
            errors.append({
                'row': line_num,
                'field': 'quantity',
                'message': f'Cannot parse quantity: {row.get("quantity")!r}'
            })
            continue

        uom = row.get('uom', '').strip().upper()
        doc_date = _parse_sap_date(row.get('doc_date', ''))

        kgco2e = None
        ef_value = None

        if fuel_type:
            info = FUEL_FACTORS[fuel_type]
            if info['unit'] == 'liter' and uom in SAP_UOM_TO_LITERS:
                liters = quantity * Decimal(str(SAP_UOM_TO_LITERS[uom]))
                kgco2e = liters * info['factor']
                ef_value = info['factor']
            elif info['unit'] == 'kg' and uom in SAP_UOM_TO_KG:
                kg = quantity * Decimal(str(SAP_UOM_TO_KG[uom]))
                kgco2e = kg * info['factor']
                ef_value = info['factor']
            elif info['unit'] == 'scf' and uom in SAP_UOM_TO_SCF:
                scf = quantity * Decimal(str(SAP_UOM_TO_SCF[uom]))
                kgco2e = scf * info['factor']
                ef_value = info['factor']
            else:
                errors.append({
                    'row': line_num,
                    'field': 'uom',
                    'message': f'Cannot convert {uom!r} for {fuel_type}.'
                })

        flagged = fuel_type is None or kgco2e is None

        rows.append({
            'source_row_ref': f'{source_ref_prefix} {line_num}',
            'scope': 'SCOPE_1',
            'scope_justification': (
                'Stationary combustion of fuel at owned facility '
                '(GHG Protocol Scope 1)'
            ),
            'category': 'Stationary combustion',
            'subcategory': fuel_type or f'Unknown ({material})',
            'raw_quantity': quantity,
            'raw_unit': uom,
            'raw_date_str': row.get('doc_date', ''),
            'quantity_kgco2e': kgco2e,
            'activity_date': doc_date,
            'ef_value': ef_value,
            'ef_source': 'DEFRA 2023',
            'review_status': 'FLAGGED' if flagged else 'PENDING',
            'flagged_reason': (
                'Unknown material or unit — manual review required'
                if flagged else ''
            ),
        })

    return rows, errors


# ── UTILITY CSV PARSER ────────────────────────────────────────────────────────

INDIA_GRID_EF = Decimal('0.708')

UTILITY_FIELD_ALIASES = {
    'consumer_no': 'consumer_no', 'Consumer No': 'consumer_no',
    'meter_id': 'meter_id', 'Meter ID': 'meter_id',
    'billing_period_start': 'period_start', 'From Date': 'period_start',
    'billing_period_end': 'period_end', 'To Date': 'period_end',
    'consumption_kwh': 'kwh', 'Consumption kWh': 'kwh',
    'Units': 'kwh', 'kWh': 'kwh',
    'tariff_code': 'tariff',
}


def _parse_date(s):
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def parse_utility_csv(file_content, source_ref_prefix='row'):
    rows, errors = [], []
    reader = csv.DictReader(io.StringIO(file_content))

    for line_num, raw_row in enumerate(reader, start=2):
        col_map = {k: UTILITY_FIELD_ALIASES.get(k, k) for k in raw_row.keys()}
        row = {col_map.get(k, k): v for k, v in raw_row.items()}

        try:
            kwh = Decimal(row.get('kwh', '0').replace(',', ''))
        except Exception:
            errors.append({
                'row': line_num,
                'field': 'kwh',
                'message': 'Cannot parse kWh value'
            })
            continue

        period_start = _parse_date(row.get('period_start', ''))
        period_end = _parse_date(row.get('period_end', ''))
        kgco2e = kwh * INDIA_GRID_EF

        flagged = period_start is None or period_end is None
        if flagged:
            errors.append({
                'row': line_num,
                'field': 'date',
                'message': 'Could not parse billing period dates'
            })

        rows.append({
            'source_row_ref': f'{source_ref_prefix} {line_num}',
            'scope': 'SCOPE_2',
            'scope_justification': (
                'Purchased electricity from grid '
                '(GHG Protocol Scope 2, location-based)'
            ),
            'category': 'Purchased electricity',
            'subcategory': (
                f"Grid electricity — India "
                f"({row.get('tariff', 'unknown tariff')})"
            ),
            'raw_quantity': kwh,
            'raw_unit': 'kWh',
            'raw_date_str': (
                f"{row.get('period_start','')} to {row.get('period_end','')}"
            ),
            'quantity_kgco2e': kgco2e,
            'period_start': period_start,
            'period_end': period_end,
            'ef_value': INDIA_GRID_EF,
            'ef_source': 'IEA 2022 — India national grid average',
            'review_status': 'FLAGGED' if flagged else 'PENDING',
            'flagged_reason': (
                'Missing billing period dates' if flagged else ''
            ),
        })

    return rows, errors


# ── TRAVEL JSON PARSER ────────────────────────────────────────────────────────

AIRPORT_COORDS = {
    'BLR': (13.1986, 77.7066), 'DEL': (28.5562, 77.1000),
    'BOM': (19.0896, 72.8656), 'MAA': (12.9941, 80.1709),
    'HYD': (17.2403, 78.4294), 'CCU': (22.6547, 88.4467),
    'AMD': (23.0772, 72.6347), 'COK': (10.1520, 76.4019),
    'LHR': (51.4775, -0.4614), 'CDG': (49.0097, 2.5479),
    'FRA': (50.0379, 8.5622), 'DXB': (25.2532, 55.3657),
    'SIN': (1.3644, 103.9915), 'BKK': (13.6811, 100.7472),
    'JFK': (40.6398, -73.7789), 'LAX': (33.9425, -118.4081),
    'NRT': (35.7653, 140.3857), 'SYD': (-33.9399, 151.1753),
}

CLASS_FACTORS = {
    'economy': Decimal('1.0'),
    'premium_economy': Decimal('1.6'),
    'business': Decimal('2.8'),
    'first': Decimal('4.0'),
}

FLIGHT_EF = Decimal('0.1153')
HOTEL_EF  = Decimal('31.4')


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def parse_travel_json(file_content, source_ref_prefix='trip'):
    rows, errors = [], []

    try:
        trips = json.loads(file_content)
    except json.JSONDecodeError as e:
        return [], [{'row': 0, 'field': 'json', 'message': f'JSON error: {e}'}]

    if isinstance(trips, dict):
        trips = [trips]

    for trip in trips:
        trip_id = trip.get('trip_id', 'unknown')

        for seg in trip.get('segments', []):
            seg_id  = seg.get('segment_id', 'unknown')
            seg_type = seg.get('type', '').lower()

            if seg_type == 'flight':
                origin = seg.get('origin', '').upper()
                dest   = seg.get('destination', '').upper()
                dep_str = seg.get('departure_date', '')
                dep_date = _parse_date(dep_str)

                distance_km = seg.get('distance_km')
                flagged = False
                flagged_reason = ''

                if not distance_km:
                    co = AIRPORT_COORDS.get(origin)
                    cd = AIRPORT_COORDS.get(dest)
                    if co and cd:
                        distance_km = _haversine_km(*co, *cd) * 1.09
                    else:
                        flagged = True
                        flagged_reason = (
                            f'Airport {origin}/{dest} not in lookup — '
                            f'distance unknown'
                        )
                        errors.append({
                            'row': f'{trip_id}/{seg_id}',
                            'field': 'airport',
                            'message': flagged_reason
                        })

                svc = (seg.get('class_of_service') or 'economy').lower()
                class_factor = CLASS_FACTORS.get(svc, Decimal('1.0'))

                kgco2e = None
                if distance_km:
                    kgco2e = (
                        Decimal(str(round(distance_km, 2)))
                        * FLIGHT_EF
                        * class_factor
                    )

                rows.append({
                    'source_row_ref': f'{source_ref_prefix} {trip_id}/{seg_id}',
                    'scope': 'SCOPE_3',
                    'scope_justification': (
                        'Business air travel '
                        '(GHG Protocol Scope 3, Category 6)'
                    ),
                    'category': 'Business travel',
                    'subcategory': f'Flight {origin}→{dest} ({svc})',
                    'raw_quantity': (
                        Decimal(str(round(distance_km, 2)))
                        if distance_km else None
                    ),
                    'raw_unit': 'km',
                    'raw_date_str': dep_str,
                    'quantity_kgco2e': kgco2e,
                    'activity_date': dep_date,
                    'ef_value': FLIGHT_EF,
                    'ef_source': 'ICAO 2023 (economy base)',
                    'review_status': 'FLAGGED' if flagged else 'PENDING',
                    'flagged_reason': flagged_reason,
                })

            elif seg_type == 'hotel':
                nights = seg.get('nights', 1)
                check_in_str = seg.get('check_in', '')
                check_in = _parse_date(check_in_str)
                kgco2e = Decimal(str(nights)) * HOTEL_EF

                rows.append({
                    'source_row_ref': f'{source_ref_prefix} {trip_id}/{seg_id}',
                    'scope': 'SCOPE_3',
                    'scope_justification': (
                        'Hotel stay during business travel '
                        '(GHG Protocol Scope 3, Category 6)'
                    ),
                    'category': 'Business travel',
                    'subcategory': (
                        f"Hotel — {seg.get('city','unknown')} "
                        f"({nights} nights)"
                    ),
                    'raw_quantity': Decimal(str(nights)),
                    'raw_unit': 'nights',
                    'raw_date_str': check_in_str,
                    'quantity_kgco2e': kgco2e,
                    'activity_date': check_in,
                    'ef_value': HOTEL_EF,
                    'ef_source': 'DEFRA 2023 Scope 3 Cat 6',
                    'review_status': 'PENDING',
                    'flagged_reason': '',
                })

    return rows, errors