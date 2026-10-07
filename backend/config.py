"""
RiskIntel upay - Production Security Configuration
File: backend/config.py

Centralized configuration loaded from environment variables with
safe defaults for local development and strict guards for production.
"""

import os
from typing import List

# Environment: 'development', 'staging', or 'production'
ENV = os.getenv("RISKINTEL_ENV", "development").lower()
IS_PRODUCTION = ENV == "production"

# Secret Keys
# WARNING: In production, JWT_SECRET_KEY must be set via environment variable.
DEFAULT_DEV_SECRET = "dev-insecure-secret-key-change-in-production-ai-dev-fest-2026"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", DEFAULT_DEV_SECRET)
if IS_PRODUCTION and JWT_SECRET_KEY == DEFAULT_DEV_SECRET:
    raise RuntimeError("CRITICAL SECURITY ERROR: JWT_SECRET_KEY must be set in production environment!")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Allowed CORS Origins
# Configured via comma-separated string, e.g. "https://riskintel-upay.vercel.app,http://localhost:3000"
DEFAULT_ALLOWED_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000,https://riskintel-upay.vercel.app"
_raw_origins = os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in _raw_origins.split(",") if origin.strip()]

# Rate Limiting Configuration (requests per window)
RATE_LIMIT_ASSESS_PER_MIN = int(os.getenv("RATE_LIMIT_ASSESS_PER_MIN", "60"))
RATE_LIMIT_AUTH_PER_MIN = int(os.getenv("RATE_LIMIT_AUTH_PER_MIN", "10"))
RATE_LIMIT_2FA_PER_MIN = int(os.getenv("RATE_LIMIT_2FA_PER_MIN", "10"))
RATE_LIMIT_RECOVERY_PER_MIN = int(os.getenv("RATE_LIMIT_RECOVERY_PER_MIN", "5"))

# Database & File Paths
DATABASE_URL = os.getenv("DATABASE_URL")  # Render PostgreSQL connection string if available
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
MODELS_DIR = os.getenv("MODELS_DIR", os.path.join(PROJECT_ROOT, "models"))
DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(DATA_DIR, "riskintel_audit.db"))

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

MODEL_FILE_PATH = os.path.join(MODELS_DIR, "fraud_model.pkl")
EXPLAINER_FILE_PATH = os.path.join(MODELS_DIR, "shap_explainer.pkl")
DATASET_FILE_PATH = os.path.join(DATA_DIR, "synthetic_upay_txns.csv")

# 2FA and Account Recovery TTLs & Rate Limits
TWO_FACTOR_EXPIRY_SECONDS = int(os.getenv("TWO_FACTOR_EXPIRY_SECONDS", "300"))  # 5 minutes
TWO_FACTOR_MAX_ATTEMPTS = int(os.getenv("TWO_FACTOR_MAX_ATTEMPTS", "3"))
RECOVERY_TOKEN_EXPIRY_SECONDS = int(os.getenv("RECOVERY_TOKEN_EXPIRY_SECONDS", "900"))  # 15 minutes
RATE_LIMIT_TXN_PER_MIN = int(os.getenv("RATE_LIMIT_TXN_PER_MIN", "30"))
RATE_LIMIT_OTP_REQUEST_PER_WINDOW = int(os.getenv("RATE_LIMIT_OTP_REQUEST_PER_WINDOW", "3"))

# SMS Provider Configuration
SMS_PROVIDER = os.getenv("SMS_PROVIDER", "development").lower()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
DEMO_USER_PHONE = os.getenv("DEMO_USER_PHONE", "+8801812345678")

