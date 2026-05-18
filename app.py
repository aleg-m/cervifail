import streamlit as st
import os, sys, csv
import pandas as pd
import plotly.express as px

# Keep your existing relative path logic
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model     import PatientInput, run_model
from data      import load_csv
from visualize import build_dashboard

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Cervifail CDS", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Glassmorphism and SaaS Palette
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(135deg, #FFD6E0 0%, #C1C1ED 100%);
    }}
    
    section[data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.4) !important;
        backdrop-filter: blur(10px);
    }}

    .glass-card {{
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
    }}
    
    h1, h2, h3 {{
        color: #4A4A4A !important;
        font-family: 'Inter', sans-serif;
    }}

    [data-testid="stMetricValue"] {{
        color: #FFA0B6 !important;
        font-weight: 700;
    }}

    .stButton>button {{
        background-color: #B3B3E3;
        color: white;
        border-radius: 12px;
        width: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)

TIER_ICONS = {"Critical": "🔴", "Elevated": "🟠", "Moderate": "🟡", "Low": "🟢"}
CSV_PATH = "final_data.csv" 

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown("<h2 style='color: #B3B3E3;'>CERVIFAIL</h2>", unsafe_allow_html=True)
mode = st.sidebar.radio("Clinical Navigation", ["Patient Risk Assessment", "Overview & Analytics"])

st.sidebar.divider()
st.sidebar.markdown("### Clinical Features")
st.sidebar.write("✨ Real-time Prediction")
st.sidebar.write("📊 Cohort Analysis")
st.sidebar.write("📋 EMR Ready")

# --- MODE 1: PATIENT RISK ASSESSMENT ---
if mode == "Patient Risk Assessment":
    st.markdown("## Patient Risk Assessment")
    st.markdown("Enter clinical parameters below to generate a real-time risk profile.")
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    with st.form("assessment_form"):
        # We'll use 3 columns to organize the 10+ parameters professionally
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            st.markdown("##### 👤 Identity & Age")
            name = st.text_input("Patient Identifier", value="New Patient")
            age = st.number_input("Maternal Age (years)", 15.0, 55.0, 30.0)
            preg = st.number_input("Prev. Pregnancies ≥ 23w", 0, step=1)
            cs = st.number_input("Prev. Cesarean Sections", 0, step=1)

        with f_col2:
            st.markdown("##### 📅 Gestation & Clinical")
            weeks = st.slider("Gestational Weeks", 0, 42, 20)
            days = st.slider("Additional Days", 0, 6, 0)
            isch = st.selectbox("Isthmic Contraction", [0, 1], format_func=lambda x: "Yes" if x==1 else "No")
            urine = st.number_input("Urine Volume (ml) [Optional]", 0.0, value=0.0)

        with f_col3:
            st.markdown("##### 📏 Physical Metrics")
            ht = st.number_input("Maternal Height (cm)", 100.0, 250.0, 165.0)
            wt = st.number_input("Pre-pregnancy Weight (kg)", 30.0, 300.0, 70.0)
            cl = st.number_input("Cervical Length (cm) [Optional]", 0.0, 10.0, 0.0)
            
        submitted = st.form_submit_button("Generate Prediction")
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        # Now passing EVERY parameter to your Model
        patient = PatientInput(
            weeks_completed=weeks, 
            days_completed=days,
            prev_pregnancies_gte23w=preg, 
            prev_cesarean_sections=cs,
            maternal_age=age, 
            weight_kg=wt, 
            height_cm=ht,
            isthmic_contraction=isch, 
            urine_volume_ml=urine if urine > 0 else None,
            measured_cl_cm=cl if cl > 0 else None,
            patient_id="ID-001", 
            patient_name=name,
        )
        
        out = run_model(patient)
        
        # Result Display (Same glass style)
        st.markdown(f'<div class="glass-card" style="border-left: 8px solid #FFA0B6;">', unsafe_allow_html=True)
        res_col1, res_col2 = st.columns([1, 2])
        with res_col1:
            st.metric("Risk Probability", f"{out.p_cervical_insufficiency*100:.1f}%")
            st.markdown(f"### {TIER_ICONS[out.risk_tier]} {out.risk_tier}")
        with res_col2:
            st.markdown(f"**Clinical Status:** {out.risk_label}")
            st.markdown(f"**Gestational Age Decimal:** {out.gestational_age_decimal:.2f}")
            st.markdown(f"**Calculated CSIS:** {out.csis:.4f}")
        st.markdown('</div>', unsafe_allow_html=True)

# --- MODE 2: OVERVIEW & ANALYTICS ---
elif mode == "Overview & Analytics":
    st.markdown("## Cohort Data Analytics")
    
    # Verify file exists first
    if not os.path.exists(CSV_PATH):
        st.error(f"🚨 Data Source Not Found at: {CSV_PATH}")
        st.info("Check if final_data.csv is in the same folder as this script.")
    else:
        # Load the data
        patients = load_csv(CSV_PATH)
        
        if not patients:
            st.warning("The CSV was found, but no patient records were loaded. Check your column headers.")
        else:
            # Process outputs and handle potential errors
            outputs = []
            valid_patients = []
            
            for p in patients:
                try:
                    out = run_model(p)
                    outputs.append(out)
                    valid_patients.append(p)
                except Exception as e:
                    # Skip patients with broken data instead of crashing the whole app
                    continue

            if outputs:
                # 1. KPI Metrics
                k1, k2, k3 = st.columns(3)
                high_risk = sum(1 for o in outputs if o.risk_label == "High Risk")
                avg_p = sum(o.p_cervical_insufficiency for o in outputs) / len(outputs)
                
                k1.metric("Total Cohort Size", len(outputs))
                k2.metric("Identified High Risk", high_risk)
                k3.metric("Cohort Mean P(CI)", f"{avg_p*100:.1f}%")

                # 2. The Data Table
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("### Clinical Data & Predictions")
                
                display_df = pd.DataFrame([{
                    "Patient": p.patient_name,
                    "GA (Weeks)": round(o.gestational_age_decimal, 1),
                    "Measured CL": f"{p.measured_cl_cm}cm" if p.measured_cl_cm else "N/A",
                    "Prob(CI) %": round(o.p_cervical_insufficiency * 100, 1),
                    "Tier": o.risk_tier,
                    "CSIS": round(o.csis, 2)
                } for p, o in zip(valid_patients, outputs)])

                st.dataframe(display_df, use_container_width=True, hide_index=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 3. The Population Graph
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                st.markdown("### Population Risk Distribution")
                
                # Using your color palette for the chart
                fig = px.bar(
                    display_df, 
                    x="Patient", 
                    y="Prob(CI) %", 
                    color="Tier",
                    color_discrete_map={
                        "Critical": "#FFA0B6", 
                        "Elevated": "#FFC0CF", 
                        "Moderate": "#C1C1ED", 
                        "Low": "#B3B3E3"
                    },
                    category_orders={"Tier": ["Critical", "Elevated", "Moderate", "Low"]}
                )
                
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title="Patient ID",
                    yaxis_title="Risk Probability (%)"
                )
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.error("Calculations failed. Please check if model.py is correctly calculating CSIS.")