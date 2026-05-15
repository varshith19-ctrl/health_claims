import requests

data = {
    "claim_id": "C001",
    "patient_id": "P001",
    "provider_id": "PR100",
    "diagnosis_code": "D10",
    "procedure_code": "PROC1",
    "billed_amount": 15000.0
}

try:
    resp = requests.post("http://localhost:8000/api/predict-claim", json=data)
    print(resp.status_code)
    print(resp.text)
except Exception as e:
    print(e)
