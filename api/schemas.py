"""
Pydantic schemas for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional


class ClaimRequest(BaseModel):
    claim_id: str = Field(..., description="Unique claim identifier")
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    provider_id: str = Field(..., description="Provider identifier")
    diagnosis_code: str = Field(..., description="ICD diagnosis code")
    procedure_code: str = Field(..., description="CPT procedure code")
    billed_amount: float = Field(..., gt=0, description="Billed amount in USD")


class FeatureContribution(BaseModel):
    feature: str
    percentage: float


class ClaimResponse(BaseModel):
    claim_id: str
    risk: str
    risk_score: float
    score: float
    prediction: str
    reasons: list[str]
    feature_contributions: dict[str, float]
    top_2_features: list[FeatureContribution]
    policy_explanation: str
    recommendations: list[str]
    execution_flow: list[dict]


class ErrorResponse(BaseModel):
    claim_id: str
    status: str
    errors: list[str]


class HealthResponse(BaseModel):
    status: str
    version: str
