"""
cervifail/main.py
=================
Cervifail Phase 2 — Clinical Decision Support Tool

Two modes:
  python main.py --dashboard          Run cohort dashboard on the 20-patient CSV
  python main.py --assess             Interactive single-patient risk assessment
  python main.py                      Runs both (default)

CSV expected at: ../Cervifail_-_final_data.csv
"""

import os, sys, argparse, csv, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model     import PatientInput, run_model, ModelOutput
from data      import load_csv
from visualize import build_dashboard

CSV_PATH   = os.path.join(os.path.dirname(__file__), "..", "Cervifail_-_final_data.csv")
OUT_DIR    = os.path.join(os.path.dirname(__file__), "..", "output")
DASH_HTML  = os.path.join(OUT_DIR, "cervifail_dashboard.html")
RESULTS_CSV = os.path.join(OUT_DIR, "cervifail_results.csv")

os.makedirs(OUT_DIR, exist_ok=True)

TIER_ICONS = {"Critical": "🔴", "Elevated": "🟠", "Moderate": "🟡", "Low": "🟢"}
TIER_ADVICE = {
    "Critical": (
        "URGENT: P(CI) ≥ 75%. Immediate clinical review recommended. "
        "Consider cervical cerclage evaluation, progesterone therapy, "
        "and enhanced surveillance protocol."
    ),
    "Elevated": (
        "ELEVATED: P(CI) 50–74%. Enhanced monitoring advised. "
        "Discuss progesterone supplementation and activity modification. "
        "Repeat ultrasound in 1–2 weeks."
    ),
    "Moderate": (
        "MODERATE: P(CI) 30–49%. Routine monitoring with increased vigilance. "
        "Patient education on warning signs. Follow-up in 2–3 weeks."
    ),
    "Low": (
        "LOW: P(CI) < 30%. Structurally sound cervix for gestational age. "
        "Continue standard antenatal care."
    ),
}


# ── Helpers ───────────────────────────────────────────────────────────────

def _ask(prompt, cast=float, allow_blank=False, default=None):
    while True:
        raw = input(f"  {prompt}: ").strip()
        if allow_blank and raw == "":
            return default
        try:
            return cast(raw)
        except ValueError:
            print("    ↳ Invalid input. Please try again.")


def print_result(patient: PatientInput, out: ModelOutput):
    tier  = out.risk_tier
    icon  = TIER_ICONS[tier]
    divider = "─" * 62

    print(f"\n  {divider}")
    print(f"  CERVIFAIL · Risk Assessment Result")
    print(f"  {divider}")
    print(f"  Patient         : {patient.patient_name or patient.patient_id or 'N/A'}")
    print(f"  Gestational Age : {patient.weeks_completed}w {patient.days_completed}d  "
          f"({out.gestational_age_decimal:.2f} decimal weeks)")
    print()
    print(f"  ── Equation Outputs ─────────────────────────────────────")
    print(f"  Eq. A  CL predicted (regression)  : {out.cl_predicted_cm:.3f} cm")
    print(f"  Eq. A  CL used (ultrasound/pred.)  : {out.cl_used_cm:.3f} cm")
    print(f"  Eq. B  CL / GA adjusted            : {out.cl_adjusted:.4f}")
    print(f"  Eq. C  CSIS                        : {out.csis:.4f}")
    print(f"  Eq. D  P(Cervical Insufficiency)   : {out.p_cervical_insufficiency*100:.1f}%")
    print()
    print(f"  ── Risk Classification ──────────────────────────────────")
    print(f"  {icon} {out.risk_label} — {tier} Tier")
    print()
    advice = textwrap.fill(TIER_ADVICE[tier], width=58,
                           initial_indent="  ", subsequent_indent="  ")
    print(advice)
    print(f"  {divider}\n")


def save_results(patients, outputs):
    fields = ["patient_id", "patient_name", "gestational_age_decimal",
              "cl_used_cm", "cl_predicted_cm", "cl_adjusted",
              "csis", "p_cervical_insufficiency", "risk_label", "risk_tier"]
    with open(RESULTS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for p, o in zip(patients, outputs):
            w.writerow({
                "patient_id":               p.patient_id,
                "patient_name":             p.patient_name,
                "gestational_age_decimal":  round(o.gestational_age_decimal, 3),
                "cl_used_cm":               round(o.cl_used_cm, 3),
                "cl_predicted_cm":          round(o.cl_predicted_cm, 3),
                "cl_adjusted":              round(o.cl_adjusted, 4),
                "csis":                     round(o.csis, 4),
                "p_cervical_insufficiency": round(o.p_cervical_insufficiency, 4),
                "risk_label":               o.risk_label,
                "risk_tier":                o.risk_tier,
            })
    print(f"  Results CSV      → {RESULTS_CSV}")


def run_cohort_dashboard():
    print("\n  Loading patient data …")
    if not os.path.exists(CSV_PATH):
        print(f"  ✗ CSV not found at: {CSV_PATH}")
        print("    Place Cervifail_-_final_data.csv one directory above main.py")
        return
    patients = load_csv(CSV_PATH)
    print(f"  Loaded {len(patients)} patients from CSV.")
    outputs  = [run_model(p) for p in patients]
    save_results(patients, outputs)

    tiers = [o.risk_tier for o in outputs]
    high  = sum(1 for o in outputs if o.risk_label == "High Risk")
    print(f"\n  ── Cohort Summary ───────────────────────────────────────")
    print(f"  Patients      : {len(patients)}")
    for t in ["Critical", "Elevated", "Moderate", "Low"]:
        print(f"  {TIER_ICONS[t]} {t:<10}: {tiers.count(t)}")
    print(f"  High Risk total : {high} / {len(patients)}  "
          f"({high/len(patients)*100:.0f}%)")
    print(f"  Mean P(CI)      : {sum(o.p_cervical_insufficiency for o in outputs)/len(outputs)*100:.1f}%")

    print("\n  Rendering Plotly dashboard …")
    build_dashboard(patients, outputs, DASH_HTML)
    print("  Open output/cervifail_dashboard.html in a browser.\n")


def run_patient_assessment():
    print("\n  ╔══════════════════════════════════════════════════════╗")
    print("  ║   CERVIFAIL · Single Patient Risk Assessment        ║")
    print("  ║   Enter patient data below to receive a prediction  ║")
    print("  ╚══════════════════════════════════════════════════════╝\n")
    print("  Fields marked [optional] may be left blank (press Enter).\n")

    name  = input("  Patient name / ID (optional): ").strip() or "Patient"
    weeks = _ask("Completed weeks of pregnancy", int)
    days  = _ask("Completed days of current week (0–6)", int)
    preg  = _ask("Previous pregnancies ≥23 weeks", int)
    cs    = _ask("Previous cesarean sections", int)
    age   = _ask("Maternal age (years)", float)
    wt    = _ask("Pre-pregnancy weight (kg)", float)
    ht    = _ask("Maternal height (cm)", float)
    isch  = _ask("Isthmic contraction present? (0=No / 1=Yes)", int)
    urine = _ask("Urine volume before ultrasound in ml [optional]",
                 float, allow_blank=True, default=None)
    cl    = _ask("Ultrasound cervical length in cm [optional — from MATLAB]",
                 float, allow_blank=True, default=None)

    patient = PatientInput(
        weeks_completed=weeks, days_completed=days,
        prev_pregnancies_gte23w=preg, prev_cesarean_sections=cs,
        maternal_age=age, weight_kg=wt, height_cm=ht,
        isthmic_contraction=isch, urine_volume_ml=urine,
        measured_cl_cm=cl,
        patient_id="ASSESS-001", patient_name=name,
    )
    out = run_model(patient)
    print_result(patient, out)

    again = input("  Assess another patient? (y/n): ").strip().lower()
    if again == "y":
        run_patient_assessment()


def main():
    parser = argparse.ArgumentParser(description="Cervifail Clinical Decision Support")
    parser.add_argument("--dashboard", action="store_true",
                        help="Generate cohort dashboard from CSV")
    parser.add_argument("--assess", action="store_true",
                        help="Interactive single-patient assessment")
    args = parser.parse_args()

    print("\n  ┌─────────────────────────────────────────────────────┐")
    print("  │  CERVIFAIL  ·  Phase 2 Clinical Decision Support   │")
    print("  │  Cervical Failure Risk Prediction Engine  v1.0     │")
    print("  └─────────────────────────────────────────────────────┘")

    # Default: run both
    if not args.dashboard and not args.assess:
        run_cohort_dashboard()
        run_patient_assessment()
    elif args.dashboard:
        run_cohort_dashboard()
    elif args.assess:
        run_patient_assessment()


if __name__ == "__main__":
    main()