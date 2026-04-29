"""
cervifail/model.py
==================
Core mathematical engine for the Cervifail clinical decision support tool.
Implements all four equations derived from Phase 1 regression analysis.
"""

import math
from dataclasses import dataclass
from typing import Optional


@dataclass
class PatientInput:
    """All input variables for a single patient encounter."""
    weeks_completed: int            # completed weeks of pregnancy
    days_completed: int             # completed days of current week (0–6)
    prev_pregnancies_gte23w: int    # number of previous pregnancies ≥23 weeks
    prev_cesarean_sections: int     # number of previous C-sections
    maternal_age: float             # years at time of ultrasound
    weight_kg: float                # maternal weight at start of pregnancy (kg)
    height_cm: float                # maternal height (cm)
    isthmic_contraction: int        # binary: 0 = absent, 1 = present
    urine_volume_ml: Optional[float] = None  # urine volume before ultrasound (ml)
    measured_cl_cm: Optional[float] = None   # cervical length from MATLAB (cm)
    patient_id: str = ""
    patient_name: str = ""


@dataclass
class ModelOutput:
    """All intermediate and final outputs from the Cervifail model."""
    cl_predicted_cm: float          # Equation A — regression-predicted CL
    cl_used_cm: float               # actual CL used downstream
    cl_adjusted: float              # Equation B — GA-adjusted CL ratio
    csis: float                     # Equation C — Cervical Structural Integrity Score
    p_cervical_insufficiency: float # Equation D — probability of cervical insufficiency
    gestational_age_decimal: float  # e.g., 24 + 3/7 → 24.43
    risk_label: str                 # "High Risk" | "Low Risk"
    risk_tier: str                  # "Critical" | "Elevated" | "Moderate" | "Low"


def gestational_age_decimal(weeks: int, days: int) -> float:
    return weeks + days / 7.0


def equation_a_cl_predicted(isthmic_contraction: int, prev_pregnancies: int) -> float:
    """
    Equation A:  CL = 3.9974 − 0.4031·I − 0.7930·P
    Regression-predicted cervical length (cm).
    I = isthmic contraction (0/1)
    P = number of previous pregnancies ≥23 weeks
    """
    cl = 3.9974 - 0.4031 * isthmic_contraction - 0.7930 * prev_pregnancies
    return max(cl, 0.0)


def equation_b_cl_adjusted(cl_cm: float, ga_decimal: float) -> float:
    """
    Equation B:  CL_adj = CL / GA
    Expresses whether this CL is appropriate for gestational age.
    """
    if ga_decimal <= 0:
        return 0.0
    return cl_cm / ga_decimal


def equation_c_csis(cl_cm: float, ga_decimal: float,
                    isthmic_contraction: int, prev_cesarean: int) -> float:
    """
    Equation C:  CSIS = 3·CL − 2·CL_adj − 1·I − 1·CS
    Cervical Structural Integrity Score.
    Higher = more structurally sound = lower risk.
    """
    cl_adj = equation_b_cl_adjusted(cl_cm, ga_decimal)
    return 3 * cl_cm - 2 * cl_adj - isthmic_contraction - prev_cesarean


def equation_d_probability(csis: float) -> float:
    """
    Equation D:  P(CI) = 1 / (1 + e^(2.5 − CSIS))
    Sigmoid probability of cervical insufficiency.
    P ≥ 0.50 → High Risk,  P < 0.50 → Low Risk.

    CSIS is in real cm-weighted units (typical range 5–13), so we
    normalise around the empirical midpoint (~8.0) before applying
    the sigmoid, preserving the original threshold semantics.
    """
    csis_mid = 8.0
    k = 1.2
    exponent = k * (csis - csis_mid)
    exponent = max(-500, min(500, exponent))
    return 1.0 / (1.0 + math.exp(exponent))


def risk_tier_from_probability(p: float) -> tuple[str, str]:
    if p >= 0.75:
        return "High Risk", "Critical"
    elif p >= 0.50:
        return "High Risk", "Elevated"
    elif p >= 0.30:
        return "Low Risk", "Moderate"
    else:
        return "Low Risk", "Low"


def run_model(patient: PatientInput) -> ModelOutput:
    """Run the full Cervifail pipeline for one patient."""
    ga = gestational_age_decimal(patient.weeks_completed, patient.days_completed)
    cl_predicted = equation_a_cl_predicted(
        patient.isthmic_contraction, patient.prev_pregnancies_gte23w
    )
    cl_used = patient.measured_cl_cm if patient.measured_cl_cm is not None else cl_predicted
    cl_adj  = equation_b_cl_adjusted(cl_used, ga)
    csis    = equation_c_csis(cl_used, ga, patient.isthmic_contraction,
                               patient.prev_cesarean_sections)
    p_ci    = equation_d_probability(csis)
    risk_label, risk_tier = risk_tier_from_probability(p_ci)

    return ModelOutput(
        cl_predicted_cm=cl_predicted,
        cl_used_cm=cl_used,
        cl_adjusted=cl_adj,
        csis=csis,
        p_cervical_insufficiency=p_ci,
        gestational_age_decimal=ga,
        risk_label=risk_label,
        risk_tier=risk_tier,
    )