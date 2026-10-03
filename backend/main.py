import os
import sys
import time
import logging
import warnings
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Suppress benign SHAP tree output format warnings
warnings.filterwarnings("ignore", category=UserWarning, module="shap")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("riskintel.api")

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
    "is_cash_out",
]

# In-memory artifact singletons
model: Optional[Any] = None
explainer: Optional[Any] = None


def load_artifacts() -> None:
    """Load LightGBM classifier and SHAP TreeExplainer into process memory."""
    global model, explainer

    if not os.path.exists(MODEL_PATH) or not os.path.exists(EXPLAINER_PATH):
        logger.warning("Model artifacts missing from disk. Initializing training pipeline...")
        try:
            from backend.train_pipeline import run_pipeline
            run_pipeline()
        except ImportError:
            import train_pipeline
            train_pipeline.run_pipeline()

    logger.info("Loading model artifact from %s", MODEL_PATH)
    model = joblib.load(MODEL_PATH)

    logger.info("Loading SHAP explainer from %s", EXPLAINER_PATH)
    explainer = joblib.load(EXPLAINER_PATH)

    logger.info("RiskIntel model and explainer ready for online scoring.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for cold-start artifact warming."""
    load_artifacts()
    yield
    logger.info("RiskIntel backend engine shutdown complete.")


app = FastAPI(
    title="RiskIntel upay - Trust & Risk Intelligence Engine",
    description="Real-time transaction risk scoring and local XAI attribution for upay MFS.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic v2 Schemas
# ---------------------------------------------------------------------------
class TransactionPayload(BaseModel):
    txn_amount: float = Field(
        ...,
        description="Transaction amount in BDT",
        ge=0.0,
        examples=[18500.0]
    )
    hour_of_day: int = Field(
        ...,
        description="Hour of day (0-23)",
        ge=0,
        le=23,
        examples=[2]
    )
    device_change_count_30d: int = Field(
        ...,
        description="Number of device switches over the past 30 days",
        ge=0,
        examples=[1]
    )
    velocity_last_1h: int = Field(
        ...,
        description="Transaction velocity frequency in the past 1 hour",
        ge=0,
        examples=[4]
    )
    agent_distance_km: float = Field(
        ...,
        description="Estimated agent or endpoint distance in kilometers",
        ge=0.0,
        examples=[8.5]
    )
    failed_pin_attempts_24h: int = Field(
        ...,
        description="Failed PIN authentication count in the last 24 hours",
        ge=0,
        examples=[1]
    )
    is_cash_out: int = Field(
        ...,
        description="Transaction channel (1 for Agent Cash-Out, 0 for P2P Send Money)",
        ge=0,
        le=1,
        examples=[1]
    )


class SHAPDriver(BaseModel):
    feature: str = Field(..., description="Feature name")
    impact: float = Field(..., description="Local SHAP attribution score")


class AssessmentResponse(BaseModel):
    risk_score: float = Field(..., description="Calibrated risk index (0.0 to 100.0)")
    risk_level: str = Field(..., description="Risk category: LOW, MEDIUM, or HIGH")
    recommended_action: str = Field(..., description="Automated policy action: APPROVE, STEP_UP_2FA, or BLOCK_IMMEDIATELY")
    key_risk_drivers: List[SHAPDriver] = Field(..., description="Top 3 features by absolute SHAP impact")
    narrative: str = Field(..., description="Audit and operational narrative for compliance triage")
    inference_time_ms: float = Field(..., description="Server inference and XAI attribution latency in milliseconds")


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["System"])
def root_info() -> Dict[str, Any]:
    """Root metadata discovery endpoint."""
    return {
        "service": "RiskIntel upay",
        "track": "Track 01: Trust & Risk Intelligence",
        "organization": "UCB Fintech Ltd.",
        "health": "/health",
        "docs": "/docs",
        "endpoint": "/api/v1/assess-risk",
    }


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    """Health check endpoint indicating model readiness."""
    is_ready = model is not None and explainer is not None
    return {
        "status": "healthy" if is_ready else "degraded",
        "service": "RiskIntel upay Engine",
        "artifacts_loaded": str(is_ready),
    }


@app.post(
    "/api/v1/assess-risk",
    response_model=AssessmentResponse,
    status_code=status.HTTP_200_OK,
    tags=["Risk Intelligence"],
)
def assess_risk(txn: TransactionPayload) -> AssessmentResponse:
    """
    Evaluates real-time MFS transaction risk using LightGBM and TreeExplainer:
    1. Validates telemetry parameters.
    2. Runs inference (<10ms) and extracts class 1 fraud probability.
    3. Calculates SHAP local explanation values.
    4. Triggers governance policy:
       - score >= 75.0: BLOCK_IMMEDIATELY
       - score >= 40.0: STEP_UP_2FA
       - score < 40.0: APPROVE
    """
    global model, explainer

    if model is None or explainer is None:
        load_artifacts()

    if model is None or explainer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Risk scoring models are currently offline or unavailable.",
        )

    start_time = time.perf_counter()

    try:
        # Construct single-row DataFrame aligned with training schema
        input_data = {
            "txn_amount": float(txn.txn_amount),
            "hour_of_day": int(txn.hour_of_day),
            "device_change_count_30d": int(txn.device_change_count_30d),
            "velocity_last_1h": int(txn.velocity_last_1h),
            "agent_distance_km": float(txn.agent_distance_km),
            "failed_pin_attempts_24h": int(txn.failed_pin_attempts_24h),
            "is_cash_out": int(txn.is_cash_out),
        }
        input_df = pd.DataFrame([input_data])[FEATURE_COLUMNS]

        # Model inference
        prob_matrix = model.predict_proba(input_df)
        fraud_prob = float(prob_matrix[0, 1])
        risk_score = round(fraud_prob * 100.0, 2)

        # Local XAI attribution via TreeExplainer
        shap_raw = explainer.shap_values(input_df)

        if isinstance(shap_raw, list):
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

        # Extract top 3 drivers by absolute magnitude
        drivers = [
            SHAPDriver(feature=feat, impact=round(float(val), 4))
            for feat, val in zip(FEATURE_COLUMNS, shap_values)
        ]
        top_drivers = sorted(drivers, key=lambda d: abs(d.impact), reverse=True)[:3]
        top_driver_names = ", ".join([d.feature for d in top_drivers])

        # Policy decision engine
        if risk_score >= 75.0:
            action = "BLOCK_IMMEDIATELY"
            risk_level = "HIGH"
            narrative = (
                f"Critical risk detected. Severe deviation driven by {top_driver_names}. "
                "Transaction halted immediately; step-up verification or manual triage required."
            )
        elif risk_score >= 40.0:
            action = "STEP_UP_2FA"
            risk_level = "MEDIUM"
            narrative = (
                f"Moderate risk variance identified due to elevated {top_driver_names}. "
                "Secondary biometric or SMS OTP challenge prompted to account holder."
            )
        else:
            action = "APPROVE"
            risk_level = "LOW"
            narrative = (
                "Transaction conforms to expected baseline behavior. "
                "Low anomaly probability across biometric and velocity signals."
            )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return AssessmentResponse(
            risk_score=risk_score,
            risk_level=risk_level,
            recommended_action=action,
            key_risk_drivers=top_drivers,
            narrative=narrative,
            inference_time_ms=elapsed_ms,
        )

    except Exception as exc:
        logger.exception("Inference failed for input %s: %s", txn, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference computation error: {str(exc)}",
        ) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
