"""Test multiple edge cases against the live API."""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

API = "http://localhost:8000/api/predict-claim"

tests = [
    {"name": "Normal valid claim ($15K)", "data": {"claim_id": "T1", "patient_id": "P001", "provider_id": "PR103", "diagnosis_code": "D10", "procedure_code": "PROC1", "billed_amount": 15000}},
    {"name": "Low amount ($500)", "data": {"claim_id": "T2", "patient_id": "P002", "provider_id": "PR100", "diagnosis_code": "D20", "procedure_code": "PROC2", "billed_amount": 500}},
    {"name": "High amount ($500K)", "data": {"claim_id": "T3", "patient_id": "P003", "provider_id": "PR105", "diagnosis_code": "D30", "procedure_code": "PROC3", "billed_amount": 500000}},
    {"name": "Extreme amount ($15M)", "data": {"claim_id": "T4", "patient_id": "P004", "provider_id": "PR110", "diagnosis_code": "D40", "procedure_code": "PROC4", "billed_amount": 15000000}},
    {"name": "High severity D50 + Cardiology PR103", "data": {"claim_id": "T5", "patient_id": "P005", "provider_id": "PR103", "diagnosis_code": "D50", "procedure_code": "PROC5", "billed_amount": 25000}},
    {"name": "Low severity D20 + General PR100", "data": {"claim_id": "T6", "patient_id": "P006", "provider_id": "PR100", "diagnosis_code": "D20", "procedure_code": "PROC1", "billed_amount": 8000}},
]

for t in tests:
    resp = requests.post(API, json=t["data"], timeout=30)
    d = resp.json()
    top = [f"{f['feature']}({f['percentage']}%)" for f in d.get("top_2_features", [])]
    print(f"\n=== {t['name']} ===")
    print(f"  Prediction: {d['prediction']}  |  Score: {d['score']:.2%}  |  Risk: {d['risk']}")
    print(f"  Top 2: {', '.join(top)}")
