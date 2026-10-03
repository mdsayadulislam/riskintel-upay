"""
RiskIntel upay - Track 01: Trust & Risk Intelligence
File: backend/main.py

FastAPI Production Backend Engine for Real-Time MFS Transaction Risk Scoring,
Local SHAP Explainability, and Automated Rule-Based Decisioning for upay.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Setup production logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("RiskIntel-API")

# Robust dynamic model artifact path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "models", "fraud_model.pkl"))
EXPLAINER_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "models", "shap_explainer.pkl"))

FEATURE_COLUMNS = [
    "txn_amount",
    "hour_of_day",
    "device_change_count_30d",
    "velocity_last_1h",
    "agent_distance_km",
    "failed_pin_attempts_24h",
    "is_cash_out"
]

# Global artifact containers
model: Optional[Any] = None
explainer: Optional[Any] = None


def load_artifacts() -> None:
    """
    Dynamically loads the LightGBM fraud model and SHAP TreeExplainer from disk.
    If models do not exist, automatically executes train_pipeline to produce them.
    """
    global model, explainer

    if not os.path.exists(MODEL_PATH) or not os.path.exists(EXPLAINER_PATH):
        logger.warning("Artifacts missing. Executing train_pipeline.py dynamically...")
        try:
            from backend.train_pipeline import run_pipeline
            run_pipeline()
        except ImportError:
            # Fallback if invoked directly inside backend dir
            import train_pipeline
            train_pipeline.run_pipeline()

    logger.info("Loading fraud model from: %s", MODEL_PATH)
    model = joblib.load(MODEL_PATH)

    logger.info("Loading SHAP explainer from: %s", EXPLAINER_PATH)
    explainer = joblib.load(EXPLAINER_PATH)

    logger.info("RiskIntel upay artifacts loaded successfully into memory.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for artifact initialization on startup."""
    logger.info("Initializing RiskIntel upay backend engine...")
    load_artifacts()
    yield
    logger.info("RiskIntel upay backend engine shut down successfully.")


# Initialize FastAPI Application
app = FastAPI(
    title="RiskIntel upay - Trust & Risk Intelligence Engine",
    description="Real-Time Risk Scoring, SHAP-driven Explainability, and Automated Decision Governance for upay MFS.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORSMiddleware with requested specifications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class TxnRequest(BaseModel):
    txn_amount: float = Field(
        ...,
        description="Transaction amount in Bangladeshi Taka (BDT)",
        ge=0.0,
        examples=[22500.0]
    )
    hour_of_day: int = Field(
        ...,
        description="Hour of day the transaction occurs (0-23)",
        ge=0,
        le=23,
        examples=[3]
    )
    device_change_count_30d: int = Field(
        ...,
        description="Number of device changes registered in the last 30 days",
        ge=0,
        examples=[2]
    )
    velocity_last_1h: int = Field(
        ...,
        description="Total transaction count in the preceding 1 hour window",
        ge=0,
        examples=[5]
    )
    agent_distance_km: float = Field(
        ...,
        description="Distance to nearest agent point in kilometers",
        ge=0.0,
        examples=[14.5]
    )
    failed_pin_attempts_24h: int = Field(
        ...,
        description="Cumulative failed PIN authentication attempts in past 24 hours",
        ge=0,
        examples=[2]
    )
    is_cash_out: int = Field(
        ...,
        description="Binary flag: 1 if Cash-Out operation, 0 for other transactions",
        ge=0,
        le=1,
        examples=[1]
    )


class KeyRiskDriver(BaseModel):
    feature: str = Field(..., description="Feature column identifier")
    impact: float = Field(..., description="Local SHAP impact value (attribution score)")


class RiskAssessmentResponse(BaseModel):
    risk_score: float = Field(..., description="Calibrated risk score between 0.0 and 100.0")
    risk_level: str = Field(..., description="Categorical risk tier: HIGH, MEDIUM, or LOW")
    recommended_action: str = Field(..., description="Engine action: BLOCK_IMMEDIATELY, STEP_UP_2FA, or APPROVE")
    key_risk_drivers: List[KeyRiskDriver] = Field(..., description="Top 3 features driving local risk by absolute SHAP impact")
    narrative: str = Field(..., description="Compliance and operational narrative explaining the decision rationale")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["System"])
def root_info() -> Dict[str, Any]:
    """Root metadata endpoint."""
    return {
        "title": "RiskIntel upay - Trust & Risk Intelligence Engine",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/health",
        "assess_risk_endpoint": "/api/v1/assess-risk"
    }


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    """
    Health check endpoint returning system readiness.
    """
    return {
        "status": "healthy",
        "service": "RiskIntel upay Engine"
    }


@app.post(
    "/api/v1/assess-risk",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
    tags=["Risk Intelligence"]
)
def assess_risk(txn: TxnRequest) -> Dict[str, Any]:
    """
    Evaluates real-time MFS transaction risk for upay:
    1. Computes fraud probability via LightGBM and scales to 0-100 risk score.
    2. Calculates SHAP local explanation values.
    3. Identifies Top 3 risk drivers by absolute SHAP impact.
    4. Triggers the Decision Engine policy:
       - score >= 75: BLOCK_IMMEDIATELY (HIGH)
       - score >= 40: STEP_UP_2FA (MEDIUM)
       - score < 40: APPROVE (LOW)
    """
    global model, explainer

    # Safeguard against uninitialized models
    if model is None or explainer is None:
        load_artifacts()

    if model is None or explainer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RiskIntel ML artifacts are currently unavailable."
        )

    # 1. Structure feature vector
    input_data = {
        "txn_amount": float(txn.txn_amount),
        "hour_of_day": int(txn.hour_of_day),
        "device_change_count_30d": int(txn.device_change_count_30d),
        "velocity_last_1h": int(txn.velocity_last_1h),
        "agent_distance_km": float(txn.agent_distance_km),
        "failed_pin_attempts_24h": int(txn.failed_pin_attempts_24h),
        "is_cash_out": int(txn.is_cash_out)
    }
    input_df = pd.DataFrame([input_data])[FEATURE_COLUMNS]

    # 2. Risk score calculation
    fraud_prob = float(model.predict_proba(input_df)[0, 1])
    risk_score = round(fraud_prob * 100.0, 2)

    # 3. Real-time local explainability via SHAP TreeExplainer
    shap_raw = explainer.shap_values(input_df)

    if isinstance(shap_raw, list):
        # Multiclass or legacy binary return format: take positive class [1]
        shap_values = np.array(shap_raw[1][0])
    elif isinstance(shap_raw, np.ndarray):
        if shap_raw.ndim == 3 and shap_raw.shape[2] == 2:
            shap_values = shap_raw[0, :, 1]
        elif shap_raw.ndim == 2:
            shap_values = shap_raw[0]
        else:
            shap_values = shap_raw.flatten()
    else:
        shap_values = np.array(shap_raw)[0]

    # 4. Map drivers and isolate Top 3 by absolute SHAP impact
    drivers = [
        {
            "feature": feat,
            "impact": round(float(val), 4)
        }
        for feat, val in zip(FEATURE_COLUMNS, shap_values)
    ]
    top_drivers = sorted(drivers, key=lambda d: abs(d["impact"]), reverse=True)[:3]
    top_drivers_names = ", ".join([d["feature"] for d in top_drivers])

    # 5. Automated Decision Engine
    if risk_score >= 75.0:
        action = "BLOCK_IMMEDIATELY"
        risk_level = "HIGH"
        narrative = (
            f"Critical risk detected. Significant anomaly driven by {top_drivers_names}. "
            "Transaction halted; step-up audit mandated for upay operations."
        )
    elif risk_score >= 40.0:
        action = "STEP_UP_2FA"
        risk_level = "MEDIUM"
        narrative = (
            f"Moderate risk variance identified due to elevated {top_drivers_names}. "
            "Prompt user for biometric or SMS OTP challenge."
        )
    else:
        action = "APPROVE"
        risk_level = "LOW"
        narrative = (
            "Transaction conforms to expected baseline behavior. "
            "Low fraud probability across velocity and biometric markers."
        )

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommended_action": action,
        "key_risk_drivers": top_drivers,
        "narrative": narrative
    }


if __name__ == "__main__":
    import uvicorn
    # Allow running directly from any directory via `python backend/main.py`
    uvicorn.run(app, host="0.0.0.0", port=8000)
