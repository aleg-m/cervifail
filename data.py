"""
cervifail/data.py
=================
Loads the real 20-patient dataset from the provided CSV.
Column names are mapped exactly as they appear in the file.
"""

import csv
from model import PatientInput

# Exact CSV column headers (stripped)
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


def _f(val, default=None):
    """Safe float parse."""
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return default


def _i(val, default=0):
    """Safe int parse."""
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return default


def load_csv(path: str) -> list[PatientInput]:
    """Load patients from the Cervifail CSV file."""
    patients = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        # Strip whitespace from all header keys
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        for row in reader:
            row = {k.strip(): v.strip() for k, v in row.items()}
            pid = row.get(COL_ID, "")
            cl_val = _f(row.get(COL_CL))
            p = PatientInput(
                weeks_completed=_i(row.get(COL_WEEKS)),
                days_completed=_i(row.get(COL_DAYS)),
                prev_pregnancies_gte23w=_i(row.get(COL_PREV_PG)),
                prev_cesarean_sections=_i(row.get(COL_PREV_CS)),
                maternal_age=_f(row.get(COL_AGE), 0),
                weight_kg=_f(row.get(COL_WEIGHT), 0),
                height_cm=_f(row.get(COL_HEIGHT), 0),
                isthmic_contraction=_i(row.get(COL_ISTHMIC)),
                urine_volume_ml=_f(row.get(COL_URINE)),
                measured_cl_cm=cl_val,
                patient_id=f"PT-{int(pid):02d}" if pid.isdigit() else pid,
                patient_name=f"Patient {pid}",
            )
            patients.append(p)
    return patients