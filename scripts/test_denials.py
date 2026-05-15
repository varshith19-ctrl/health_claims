import requests
import json

API = "http://localhost:8000/api/predict-claim"

tests = [
    {
        "name": "High risk specialty + high severity + high cost ratio",
        "data": {
            "claim_id": "Test_Denial_1",
            "patient_id": "P_HIGH_FREQ", # Simulating a patient with many claims
            "provider_id": "PR106", # Cardiology, known high risk
            "diagnosis_code": "D10", # Heart (High severity)
            "procedure_code": "PROC6", # Cheap procedure (mismatch)
            "billed_amount": 20000 # High billed amount vs avg cost
        }
    },
    {
        "name": "Missing fields",
        "data": {
            "claim_id": "Test_Denial_2",
            "patient_id": "P001",
            "provider_id": "PR100",
            "diagnosis_code": "",
            "procedure_code": "",
            "billed_amount": 1000
        }
    }
]

for t in tests:
    resp = requests.post(API, json=t["data"])
    d = resp.json()
    print(f"\n=== {t['name']} ===")
    print(f"Prediction: {d['prediction']} | Score: {d['score']:.2%} | Risk: {d['risk']}")
    for f in d.get("top_2_features", []):
        print(f"  - {f['feature']}: {f['percentage']}%")
