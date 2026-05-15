"""
Claim Agent — Orchestrates ML prediction + rule checks + RAG retrieval
to produce a complete remediation response.
"""
import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from monitoring.logger import get_logger
from config.settings import SILVER_DIR

log = get_logger("agent.claim_agent")

REQUIRED_KEYS = ["claim_id", "provider_id", "diagnosis_code", "procedure_code", "billed_amount"]


def validate_claim(claim: dict) -> list[str]:
    """
    Validates the incoming claim dictionary to ensure all required keys are present
    and have valid values (e.g., billed_amount must be a positive number).
    
    Args:
        claim (dict): The claim data dictionary.
        
    Returns:
        list[str]: A list of error messages if validation fails, empty list otherwise.
    """
    errors = []
    for key in REQUIRED_KEYS:
        if key not in claim or claim[key] is None or str(claim[key]).strip() == "":
            errors.append(f"Missing required field: {key}")
    if "billed_amount" in claim and claim["billed_amount"] is not None:
        try:
            amt = float(claim["billed_amount"])
            if amt <= 0:
                errors.append("Billed amount must be positive")
        except (ValueError, TypeError):
            errors.append("Billed amount must be a number")
    return errors


def _build_features(claim: dict) -> dict:
    """
    Constructs feature values for the ML model based on the claim data.
    Retrieves historical/statistical data (averages, severity, frequency) from 
    local parquet files (Silver layer) to engineer the features.
    
    Args:
        claim (dict): The validated claim data.
        
    Returns:
        dict: A dictionary of engineered features required for ML prediction.
    """
    billed = float(claim.get("billed_amount", 0))

    providers_path = SILVER_DIR / "silver_providers.parquet"
    diagnosis_path = SILVER_DIR / "silver_diagnosis.parquet"
    cost_path = SILVER_DIR / "silver_cost.parquet"
    claims_path = SILVER_DIR / "silver_claims.parquet"

    avg_cost = 10000.0
    severity_score = 2
    specialty_risk = 1
    provider_claim_count = 50
    patient_claim_frequency = 3

    # Attempt to enrich features by reading from Silver layer parquet files
    # If files are missing or lookup fails, defaults (above) are retained.

    try:
        if cost_path.exists():
            cost_df = pd.read_parquet(cost_path)
            match = cost_df[cost_df["procedure_code"] == claim.get("procedure_code")]
            if not match.empty:
                avg_cost = float(match["average_cost"].iloc[0])
    except Exception:
        pass

    try:
        if diagnosis_path.exists():
            diag_df = pd.read_parquet(diagnosis_path)
            match = diag_df[diag_df["diagnosis_code"] == claim.get("diagnosis_code")]
            if not match.empty:
                sev = match["severity"].iloc[0]
                severity_score = 3 if sev == "High" else 1
    except Exception:
        pass

    try:
        if providers_path.exists():
            prov_df = pd.read_parquet(providers_path)
            match = prov_df[prov_df["provider_id"] == claim.get("provider_id")]
            if not match.empty:
                spec = match["specialty"].iloc[0]
                risk_map = {"Cardiology": 3, "Neurology": 3, "Orthopedic": 2, "General": 1}
                specialty_risk = risk_map.get(spec, 1)
    except Exception:
        pass

    try:
        if claims_path.exists():
            claims_df = pd.read_parquet(claims_path)
            prov_claims = claims_df[claims_df["provider_id"] == claim.get("provider_id")]
            if not prov_claims.empty:
                provider_claim_count = len(prov_claims)
            pat_claims = claims_df[claims_df["patient_id"] == claim.get("patient_id", "")]
            if not pat_claims.empty:
                patient_claim_frequency = len(pat_claims)
    except Exception:
        pass

    # Calculate ratio of billed amount to average cost
    ratio = billed / avg_cost if avg_cost > 0 else 1.0

    return {
        "billed_vs_avg_ratio": ratio,
        "severity_score": severity_score,
        "provider_claim_count": provider_claim_count,
        "patient_claim_frequency": patient_claim_frequency,
        "specialty_risk": specialty_risk,
    }


def _generate_recommendations(prediction: dict, claim: dict) -> list[str]:
    """
    Generates human-readable, actionable recommendations based on the top 2 features 
    that drove the ML model's prediction.
    
    Args:
        prediction (dict): The prediction output dictionary containing 'top_2_features'.
        claim (dict): The original claim data.
        
    Returns:
        list[str]: A list of actionable recommendations for the user.
    """
    recs = []
    for feat_info in prediction.get("top_2_features", []):
        feat = feat_info["feature"]
        if "Missing" in feat:
            recs.append("Ensure all required fields (diagnosis code, procedure code, billed amount) are filled before submission.")
        elif "Cost" in feat or "Billed" in feat or "Ratio" in feat:
            recs.append("Review the billed amount — it exceeds the regional average. Provide supporting documentation or adjust the billing.")
        elif "Denial Rate" in feat:
            recs.append("This provider has a high historical denial rate. Double-check coding accuracy and documentation completeness.")
        elif "Severity" in feat:
            recs.append("The diagnosis severity is flagged. Ensure the procedure aligns with the diagnosis complexity.")
        elif "Specialty" in feat:
            recs.append("The provider specialty carries elevated risk. Verify that the procedure matches the specialty scope.")
        elif "Frequency" in feat:
            recs.append("High claim frequency detected. Verify this is not a duplicate or unnecessary repeat submission.")
        else:
            recs.append(f"Review the factor: {feat}")
    return recs if recs else ["Review all claim details before submission."]


def process_claim(claim: dict) -> dict:
    """
    The main orchestrator function for the claim processing pipeline.
    It validates the claim, engineers features, gets ML predictions, applies business rules,
    retrieves policy explanations via RAG, and generates recommendations.
    
    Args:
        claim (dict): The raw claim data from the request.
        
    Returns:
        dict: A comprehensive response dictionary with status, prediction, explanations, and execution flow.
    """
    log.info("Processing claim: %s", claim.get("claim_id", "unknown"))
    
    execution_flow = [
        {"node": "API Layer", "label": "Receive Claim", "detail": f"ID: {claim.get('claim_id')}"}
    ]

    # 1. Validation Step
    validation_errors = validate_claim(claim)
    if validation_errors:
        execution_flow.append({"node": "Validation Layer", "label": "Validation Failed", "detail": ", ".join(validation_errors)})
        return {
            "claim_id": claim.get("claim_id", "unknown"),
            "status": "VALIDATION_ERROR",
            "errors": validation_errors,
        }
    execution_flow.append({"node": "Validation Layer", "label": "Passed Checks", "detail": "All required keys present"})

    # 2. Feature Engineering Step
    features = _build_features(claim)
    execution_flow.append({"node": "Feature Engineering", "label": "Extract Features", "detail": "silver_cost.parquet, silver_providers.parquet"})

    # 3. ML Inference Step
    from ml.predict import predict_claim
    prediction = predict_claim(features)
    execution_flow.append({"node": "ML Inference", "label": "XGBoost + SHAP", "detail": "xgboost.pkl loaded"})

    # 4. Business Rules Override
    # Hard-coded rules that override ML decisions (e.g. for extreme outliers)
    if features.get("billed_vs_avg_ratio", 0) > 5.0:
        log.info("Override: extreme billed amount (ratio > 5x).")
        prediction["prediction"] = 1
        prediction["risk_level"] = "HIGH"
        prediction["probability"] = max(prediction["probability"], 0.95)
        prediction["reasons"].insert(0, "Billed amount is extremely high (>5x the regional average).")
        execution_flow.append({"node": "Rule Engine", "label": "Hard Override", "detail": f"Cost ratio {features['billed_vs_avg_ratio']:.1f}x"})
    else:
        execution_flow.append({"node": "Rule Engine", "label": "Pass", "detail": "No manual overrides"})

    claim_context = (
        f"Claim ID: {claim.get('claim_id')}, "
        f"Provider: {claim.get('provider_id')}, "
        f"Diagnosis: {claim.get('diagnosis_code')}, "
        f"Procedure: {claim.get('procedure_code')}, "
        f"Amount: ${claim.get('billed_amount')}"
    )

    # 5. RAG Policy Retrieval & Explanation Generation
    policy_chunks = []
    explanation = "Policy retrieval unavailable."
    try:
        from rag.retriever import retrieve
        from rag.generator import generate_explanation
        query = f"Policy rules for Procedure {claim.get('procedure_code')} and Diagnosis {claim.get('diagnosis_code')} regarding: {' '.join(prediction['reasons'])}"
        execution_flow.append({"node": "Vector Database", "label": "FAISS Hybrid Search", "detail": f"Query: {query[:50]}..."})
        
        policy_chunks = retrieve(query)
        if policy_chunks:
            explanation = generate_explanation(claim_context, policy_chunks, prediction["reasons"])
            execution_flow.append({"node": "LLM Gen AI", "label": "GPT-4o-mini", "detail": f"Grounded in {len(policy_chunks)} policy chunks"})
        else:
            execution_flow.append({"node": "LLM Gen AI", "label": "No Policy Found", "detail": "Bypassed generation"})
    except Exception as exc:
        log.warning("RAG pipeline error: %s", exc)
        explanation = f"Policy lookup unavailable: {exc}"

    # 6. Generate Actionable Recommendations
    recommendations = _generate_recommendations(prediction, claim)

    # Determine final prediction label:
    # DENIED (>= 0.5), MEDIUM (0.4–0.5 gray zone), ACCEPTED (< 0.4)
    prob = prediction["probability"]
    if prediction["prediction"] == 1:
        pred_label = "DENIED"
    elif prob >= 0.4:
        pred_label = "MEDIUM"
    else:
        pred_label = "ACCEPTED"

    response = {
        "claim_id": claim.get("claim_id"),
        "risk": prediction["risk_level"],
        "risk_score": prediction["risk_score"],
        "score": prediction["probability"],
        "prediction": pred_label,
        "reasons": prediction["reasons"],
        "feature_contributions": prediction["feature_contributions"],
        "top_2_features": prediction["top_2_features"],
        "policy_explanation": explanation,
        "recommendations": recommendations,
        "execution_flow": execution_flow,
    }

    execution_flow.append({"node": "Response", "label": "Final Output", "detail": f"Risk: {prediction['risk_level']}"})
    log.info("Claim %s processed: %s (%.2f)", response["claim_id"], response["risk"], response["score"])
    return response
