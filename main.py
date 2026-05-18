import streamlit as st
import os, sys, csv
import pandas as pd

# Keep your existing relative path logic
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model     import PatientInput, run_model
from data      import load_csv
from visualize import build_dashboard

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Cervifail CDS", layout="wide")

TIER_ICONS = {"Critical": "🔴", "Elevated": "🟠", "Moderate": "🟡", "Low": "🟢"}
TIER_ADVICE = {
    "Critical": "URGENT: P(CI) ≥ 75%. Immediate clinical review recommended. Consider cervical cerclage evaluation, progesterone therapy, and enhanced surveillance protocol.",
    "Elevated": "ELEVATED: P(CI) 50–74%. Enhanced monitoring advised. Discuss progesterone supplementation and activity modification.",
    "Moderate": "MODERATE: P(CI) 30–49%. Routine monitoring with increased vigilance. Patient education on warning signs.",
    "Low": "LOW: P(CI) < 30%. Structurally sound cervix for gestational age. Continue standard antenatal care."
}

CSV_PATH = "/Users/mimi/Programming/bench/cervifail/final_data.csv"  # Adjust as needed


# --- APP LAYOUT ---
st.title("🛡️ CERVIFAIL · Phase 2")
st.markdown("### Clinical Decision Support Tool for Cervical Failure Risk")

# Sidebar for Navigation
mode = st.sidebar.radio("Navigate", ["Single Patient Assessment", "Cohort Dashboard"])

# --- MODE 1: SINGLE PATIENT ASSESSMENT ---
if mode == "Single Patient Assessment":
    st.header("Single Patient Risk Assessment")
    
    with st.form("assessment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Patient Name / ID", value="Patient-001")
            weeks = st.slider("Completed Weeks of Pregnancy", 0, 42, 20)
            days = st.slider("Completed Days of Current Week", 0, 6, 0)
            preg = st.number_input("Previous pregnancies ≥ 23 weeks", min_value=0, step=1)
            cs = st.number_input("Previous Cesarean Sections", min_value=0, step=1)
            isch = st.selectbox("Isthmic Contraction Present?", options=[0, 1], format_func=lambda x: "Yes" if x==1 else "No")

        with col2:
            age = st.number_input("Maternal Age (years)", min_value=12.0, max_value=60.0, value=30.0)
            wt = st.number_input("Pre-pregnancy weight (kg)", min_value=30.0, value=70.0)
            ht = st.number_input("Maternal height (cm)", min_value=100.0, value=165.0)
            urine = st.number_input("Urine volume (ml) [Optional]", min_value=0.0, value=0.0)
            cl = st.number_input("Ultrasound cervical length (cm) [Optional]", min_value=0.0, value=0.0)

        submitted = st.form_submit_button("Run Risk Assessment")

    if submitted:
        # Map inputs to your existing Model class
        patient = PatientInput(
            weeks_completed=weeks, days_completed=days,
            prev_pregnancies_gte23w=preg, prev_cesarean_sections=cs,
            maternal_age=age, weight_kg=wt, height_cm=ht,
            isthmic_contraction=isch, 
            urine_volume_ml=urine if urine > 0 else None,
            measured_cl_cm=cl if cl > 0 else None,
            patient_id="ASSESS-001", patient_name=name,
        )
        
        out = run_model(patient)
        
        # Display Results
        st.divider()
        tier = out.risk_tier
        st.subheader(f"{TIER_ICONS[tier]} Risk Tier: {tier}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("P(Cervical Insufficiency)", f"{out.p_cervical_insufficiency*100:.1f}%")
        m2.metric("Predicted CL", f"{out.cl_predicted_cm:.2f} cm")
        m3.metric("CSIS Score", f"{out.csis:.4f}")

        st.info(f"**Clinical Advice:** {TIER_ADVICE[tier]}")

# --- MODE 2: COHORT DASHBOARD ---
elif mode == "Cohort Dashboard":
    st.header("Cohort Analytics Dashboard")
    
    if not os.path.exists(CSV_PATH):
        st.error(f"CSV not found at {CSV_PATH}. Please ensure the data file is in the parent directory.")
    else:
        if st.button("Load & Process CSV Data"):
            patients = load_csv(CSV_PATH)
            outputs  = [run_model(p) for p in patients]
            
            # Summary Metrics
            high_risk_count = sum(1 for o in outputs if o.risk_label == "High Risk")
            avg_p = sum(o.p_cervical_insufficiency for o in outputs) / len(outputs)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Patients", len(patients))
            c2.metric("High Risk Patients", f"{high_risk_count}")
            c3.metric("Avg Risk Probability", f"{avg_p*100:.1f}%")
            
            # Display results table
            data_dict = [{
                "Name": p.patient_name,
                "Risk Tier": o.risk_tier,
                "Prob(CI)": f"{o.p_cervical_insufficiency*100:.1f}%",
                "CL Used": f"{o.cl_used_cm:.2f} cm"
            } for p, o in zip(patients, outputs)]
            
            st.dataframe(pd.DataFrame(data_dict), use_container_width=True)
            
            st.success("Analysis Complete. For full Plotly interactive visuals, run the visualize module.")
            # Note: You can embed Plotly charts directly here using st.plotly_chart() 
            # if your build_dashboard function returns a figure.