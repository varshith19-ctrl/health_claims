"""
Claims route — POST /predict-claim endpoint.
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from monitoring.logger import get_logger
from api.schemas import ClaimRequest, ClaimResponse, ErrorResponse

log = get_logger("api.routes.claims")
router = APIRouter()


@router.post("/predict-claim", response_model=ClaimResponse)
async def predict_claim(request: ClaimRequest):
    """
    Endpoint to predict the denial risk of a healthcare claim.
    
    Accepts a claim request, processes it through the claim agent (which handles validation,
    feature engineering, ML prediction, rule overrides, and RAG-based explanations),
    and returns a structured response.
    
    Args:
        request (ClaimRequest): The validated request payload containing claim details.
        
    Returns:
        ClaimResponse: The final prediction, risk level, recommendations, and explanations.
        
    Raises:
        HTTPException: 
            - 422 if validation fails at the agent layer.
            - 500 if an unexpected error occurs during processing.
    """
    try:
        from agent.claim_agent import process_claim

        # Extract data from the validated request schema to pass into the agent
        claim_data = {
            "claim_id": request.claim_id,
            "patient_id": request.patient_id or "",
            "provider_id": request.provider_id,
            "diagnosis_code": request.diagnosis_code,
            "procedure_code": request.procedure_code,
            "billed_amount": request.billed_amount,
        }

        # Call the central claim processing logic
        result = process_claim(claim_data)

        # Handle specific validation errors returned by the agent
        if result.get("status") == "VALIDATION_ERROR":
            raise HTTPException(status_code=422, detail=result["errors"])

        # Return the successful response matching the ClaimResponse schema
        return ClaimResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        import traceback
        log.error("Prediction failed: %s\n%s", exc, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(exc))
