"""
Realistic claim_status generator.
Joins claims with providers, diagnosis, and cost reference data.
Computes a multi-factor denial score simulating real-world insurance logic.
"""
import pandas as pd
import numpy as np

np.random.seed(42)

claims = pd.read_csv(r"c:\Users\varsh\OneDrive\Desktop\health_claims_project\raw_data\claims_1000.csv")
providers = pd.read_csv(r"c:\Users\varsh\OneDrive\Desktop\health_claims_project\raw_data\providers_1000.csv")
diagnosis = pd.read_csv(r"c:\Users\varsh\OneDrive\Desktop\health_claims_project\raw_data\diagnosis.csv")
cost = pd.read_csv(r"c:\Users\varsh\OneDrive\Desktop\health_claims_project\raw_data\cost.csv")

# Drop old claim_status
if "claim_status" in claims.columns:
    claims = claims.drop(columns=["claim_status"])

# Enrich claims with reference data
df = claims.merge(providers, on="provider_id", how="left")
df = df.merge(diagnosis, on="diagnosis_code", how="left")
df = df.merge(cost, on="procedure_code", how="left")

score = np.zeros(len(df))

# ---- Factor 1: Cost ratio (billed vs regional average) ----
# This is the most important real-world factor
df["_avg_cost"] = df["average_cost"].fillna(10000)
df["_billed"] = df["billed_amount"].fillna(0)
df["_ratio"] = np.where(df["_avg_cost"] > 0, df["_billed"] / df["_avg_cost"], 1.0)

# Ratio > 2.0 = suspicious, > 3.0 = very suspicious
score += np.where(df["_ratio"] > 3.0, 0.30,
         np.where(df["_ratio"] > 2.0, 0.20,
         np.where(df["_ratio"] > 1.5, 0.10, 0.0)))

# ---- Factor 2: Diagnosis severity ----
# High severity diagnoses (Heart, Bone, Diabetes) face more scrutiny
severity_score = df["severity"].map({"High": 0.15, "Low": 0.0}).fillna(0.05)
score += severity_score

# ---- Factor 3: Specialty risk ----
# Cardiology and Neurology have higher denial rates in real insurance
specialty_score = df["specialty"].map({
    "Cardiology": 0.12, "Neurology": 0.10,
    "Orthopedic": 0.05, "General": 0.0
}).fillna(0.03)
score += specialty_score

# ---- Factor 4: Diagnosis-Procedure mismatch ----
# e.g., Cold/Skin (low severity) with expensive procedure (PROC5=$20K)
# or Heart diagnosis with cheap procedure (PROC6=$800) — suspicious
expensive_procs = df["procedure_code"].isin(["PROC5", "PROC2"])
low_severity = df["severity"] == "Low"
cheap_procs = df["procedure_code"].isin(["PROC6", "PROC1"])
high_severity = df["severity"] == "High"

score += (expensive_procs & low_severity).astype(float) * 0.18  # overbilling signal
score += (cheap_procs & high_severity).astype(float) * 0.12    # undercoding signal

# ---- Factor 5: Missing fields ----
# Still a factor but not the dominant one
missing_diag = df["diagnosis_code"].isna().astype(float) * 0.10
missing_proc = df["procedure_code"].isna().astype(float) * 0.10
missing_amt = df["billed_amount"].isna().astype(float) * 0.08
score += missing_diag + missing_proc + missing_amt

# ---- Factor 6: Provider-specific patterns ----
# Some providers just have historically higher denial rates
# (In real life this comes from historical data, here we simulate)
high_risk_providers = ["PR101", "PR106", "PR109", "PR112", "PR119"]
score += df["provider_id"].isin(high_risk_providers).astype(float) * 0.10

# ---- Factor 7: Patient claim frequency ----
# Patients with many claims are flagged for review
patient_counts = df.groupby("patient_id")["claim_id"].transform("count")
score += np.where(patient_counts >= 5, 0.10,
         np.where(patient_counts >= 3, 0.05, 0.0))

# ---- Add controlled random noise (8%) ----
# Real-world decisions have subjectivity
score += np.random.uniform(-0.08, 0.08, len(df))

# ---- Threshold: aim for ~35-40% denial rate ----
threshold = np.percentile(score, 60)  # top 40% get denied
claims["claim_status"] = (score >= threshold).astype(int)

# Stats
denied = claims["claim_status"].sum()
accepted = (claims["claim_status"] == 0).sum()
print(f"Total: {len(claims)}")
print(f"Denied: {denied} ({denied/len(claims):.1%})")
print(f"Accepted: {accepted} ({accepted/len(claims):.1%})")

# Show score distribution by factor
print(f"\nScore stats: min={score.min():.3f}, median={np.median(score):.3f}, max={score.max():.3f}")
print(f"Threshold: {threshold:.3f}")

# Verify diversity: check denial rates across different slices
merged = df.copy()
merged["claim_status"] = claims["claim_status"]
print("\n--- Denial rates by specialty ---")
print(merged.groupby("specialty")["claim_status"].mean().round(3))
print("\n--- Denial rates by severity ---")
print(merged.groupby("severity")["claim_status"].mean().round(3))
print("\n--- Denial rates by procedure ---")
print(merged.groupby("procedure_code")["claim_status"].mean().round(3))

claims.to_csv(r"c:\Users\varsh\OneDrive\Desktop\health_claims_project\raw_data\claims_1000.csv", index=False)
print("\nSaved claims_1000.csv with realistic claim_status.")
