import pandas as pd
import sys
sys.path.insert(0, '.')
from clinical_math import calculate_joint_angles, evaluate_gait_risk
from agents import analyze_biomechanics, assess_clinical_risk

cases = [
    ('Normative (expected LOW)', '../demo_normative.csv'),
    ('Asymmetric (expected HIGH)', '../demo_asymmetric.csv'),
]

for label, csv in cases:
    df = pd.read_csv(csv, index_col='frame')
    angles_df = calculate_joint_angles(df)
    risk = evaluate_gait_risk(df)
    bio = analyze_biomechanics(angles_df, risk)
    cr = assess_clinical_risk(bio, patient_age='7 y/o')
    rl = cr['risk_level']
    sv = cr['severity']
    ap = cr['asymmetry_percentage']
    af = cr['affected_side']
    fm = len(cr['triggered_measurements'])
    print(label)
    print('  Risk Level :', rl)
    print('  Severity   :', sv)
    print('  Asymmetry  :', ap, '%')
    print('  Affected   :', af)
    print('  Factors    :', fm, 'measurement(s) flagged')
    print('  is_diagnostic:', cr['is_diagnostic'])
    print()
print('PASS: Pipeline test complete.')
