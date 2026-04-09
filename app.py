#this is where the main application content goes
# imports
import streamlit as st
import pandas as pd
from datetime import date
import math
import io
from formula import weighted_bishop, trajectory, risk_probability, classify_risk # not created yet
from data import load_patients, get_patient_visits, get_all_patient_ids, add_visit

#---App interface ------


#---Side Nav. Bar ------

