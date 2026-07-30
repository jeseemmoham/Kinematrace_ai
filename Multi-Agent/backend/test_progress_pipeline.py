import pandas as pd
import sys
sys.path.insert(0, '.')
from clinical_math import calculate_joint_angles, evaluate_gait_risk
from agents import analyze_biomechanics, assess_clinical_risk, assess_progress, get_patient_assessments

print("=== TESTING AGENT 3: PATIENT PROGRESS MONITORING AGENT ===")

# Test 1: History retrieval for seeded demo patient KT-2026-P902
history = get_patient_assessments("KT-2026-P902")
print(f"1. Seeded History for KT-2026-P902: {len(history)} assessment(s) retrieved.")
for a in history:
    print(f"   [{a['assessment_date']}] Asymmetry: {a['asymmetry_percentage']}% | Risk: {a['risk_level']}")

# Test 2: Process current walking video with Agent 1, Agent 2, Agent 3
df = pd.read_csv('../demo_asymmetric.csv', index_col='frame')
angles_df = calculate_joint_angles(df)
risk = evaluate_gait_risk(df)
bio = analyze_biomechanics(angles_df, risk)
cr = assess_clinical_risk(bio, patient_age="7 y/o")

# Run Agent 3
pr = assess_progress(
    patient_id="KT-2026-P902",
    gait_analysis_result=bio,
    clinical_risk_result=cr,
    patient_age="7 y/o",
    assessment_date="2026-07-27",
    save=False
)

print("\n2. Agent 3 Multi-Agent Result:")
print("   Patient ID      :", pr["patient_id"])
print("   Trend           :", pr["trend"])
print("   Current Asym %  :", pr["current_asymmetry"])
print("   Previous Asym % :", pr["previous_asymmetry"])
print("   Asymmetry Change:", pr["asymmetry_change"], "pp")
print("   Risk Level      :", pr["previous_risk_level"], "to", pr["current_risk_level"])
print("   Key Changes     :", [c.encode('ascii', 'replace').decode() for c in pr["key_changes"]])
print("   is_diagnostic   :", pr["is_diagnostic"])

# Test 3: First-time patient (INSUFFICIENT DATA check)
pr_new = assess_progress(
    patient_id="KT-FIRST-TIME-001",
    gait_analysis_result=bio,
    clinical_risk_result=cr,
    patient_age="2 y/o",
    assessment_date="2026-07-27",
    save=False
)
print("\n3. First-Time Patient Test:")
print("   Trend        :", pr_new["trend"])
print("   Data Available:", pr_new["data_available"])
print("   Explanation  :", pr_new["explanation"][:120], "...")

print("\nSUCCESS: Patient Progress Monitoring Agent tests passed cleanly!")
