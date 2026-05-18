"""
cervifail/data.py
=================
Loads the 20-patient dataset with strict type enforcement to prevent math errors.
"""

import csv
import os
from model import PatientInput

# Exact CSV column headers based on your dataset
COL_ID       = "Patient #"
COL_WEEKS    = "completed weeks of pregnancy"
COL_DAYS     = "completed days of the current week of pregnancy"
COL_PREV_PG  = "number of previous pregnancies ≥23.0wk"
COL_PREV_CS  = "number of previous cesarean sections"
COL_AGE      = "maternal age at the time of ultrasound examination (in years)"
COL_WEIGHT   = "maternal weight at the start of the pregnancy (in kg)"
COL_HEIGHT   = "maternal height (in cm)"
COL_ISTHMIC  = "0=no, 1=yes (presence of isthmic contraction during the examination, subjectively assessed)"
COL_URINE    = "volume of urine collected before the ultrasound examination (in ml)"
COL_CL       = "Cervix Measure in cm (MatLAB)"

def _f(val, default=0.0):
    """Strict float conversion: handles empty strings and removes whitespace."""
    if val is None:
        return default
    s = str(val).strip().replace(",", "")
    if s == "" or s.lower() == "nan" or s.lower() == "n/a":
        return default
    try:
        return float(s)
    except (ValueError, TypeError):
        return default

def _i(val, default=0):
    """Strict integer conversion: handles floats in strings (e.g., '1.0' -> 1)."""
    if val is None:
        return default
    s = str(val).strip()
    if s == "" or s.lower() == "nan" or s.lower() == "n/a":
        return default
    try:
        # Convert to float first to handle cases like "1.0"
        return int(float(s))
    except (ValueError, TypeError):
        return default

def load_csv(path: str) -> list[PatientInput]:
    """
    Reads the CSV and converts every row into a PatientInput object.
    Uses utf-8-sig to handle Excel-specific hidden characters (BOM).
    """
    patients = []
    
    if not os.path.exists(path):
        return []

    with open(path, newline="", encoding="utf-8-sig") as f:
        # DictReader maps the first row as keys
        reader = csv.DictReader(f)
        
        # Clean the headers just in case there are hidden spaces
        reader.fieldnames = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []
        
        for row in reader:
            # Clean all cell values
            row = {k.strip(): v.strip() for k, v in row.items() if k}
            
            pid = row.get(COL_ID, "0")
            
            # Map columns to the PatientInput dataclass
            p = PatientInput(
                weeks_completed=_i(row.get(COL_WEEKS)),
                days_completed=_i(row.get(COL_DAYS)),
                prev_pregnancies_gte23w=_i(row.get(COL_PREV_PG)),
                prev_cesarean_sections=_i(row.get(COL_PREV_CS)),
                maternal_age=_f(row.get(COL_AGE)),
                weight_kg=_f(row.get(COL_WEIGHT)),
                height_cm=_f(row.get(COL_HEIGHT)),
                isthmic_contraction=_i(row.get(COL_ISTHMIC)),
                urine_volume_ml=_f(row.get(COL_URINE)),
                measured_cl_cm=_f(row.get(COL_CL)),
                patient_id=f"PT-{_i(pid):02d}" if pid.isdigit() else pid,
                patient_name=f"Patient {pid}"
            )
            patients.append(p)
            
    return patients