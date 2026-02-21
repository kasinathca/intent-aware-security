from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from collections import deque
import joblib
import pandas as pd
import numpy as np
import config
import os
import time
import asyncio
import threading
from contextlib import asynccontextmanager
import crypto_utils
from typing import Optional

# ============ GLOBAL STATE ============

model = None

# Thread-safe stats using a lock
_stats_lock = threading.Lock()
stats = {
    "total_requests": 0,
    "blocked_requests": 0,
    "zkp_enabled_requests": 0,
    "zkp_failures": 0,
    "start_time": time.time()
}

def _inc_stat(key: str, amount: int = 1):
    """Thread-safe stat increment."""
    with _stats_lock:
        stats[key] += amount

# Store last 50 logs for live dashboard
recent_logs = deque(maxlen=50)

# Security Configuration (toggleable for demonstration)
security_config = {
    "zkp_enabled": True,
    "ml_enabled": True
}

# ZKP Infrastructure — thread-safe public key store
_keys_lock = threading.Lock()
user_public_keys = {}  # user_id -> public key object
challenge_store = crypto_utils.ChallengeStore(expiry_seconds=60)

# ============ LIFESPAN ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load ML model
    global model
    model_path = os.path.join(config.DATA_DIR, config.MODEL_FILE)
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print(f"[+] Model loaded from {model_path}")
    else:
        print(f"[!] Warning: Model not found at {model_path}. Run train_model.py first.")

    # Background task: clean up expired ZKP challenges every 30 seconds
    async def _cleanup_loop():
        while True:
            await asyncio.sleep(30)
            challenge_store.cleanup_expired()

    cleanup_task = asyncio.create_task(_cleanup_loop())

    yield

    # Shutdown
    cleanup_task.cancel()
    print("[*] Shutting down API Gateway...")

# ============ APP SETUP ============

app = FastAPI(title="Intent-Aware Security Gateway", version="1.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mounts
app.mount("/portal", StaticFiles(directory="static/portal"), name="portal")
app.mount("/hacker", StaticFiles(directory="static/hacker"), name="hacker")
app.mount("/dashboard", StaticFiles(directory="static/dashboard", html=True), name="dashboard")
app.mount("/demo", StaticFiles(directory="static/demo", html=True), name="demo")
app.mount("/compare", StaticFiles(directory="static/compare", html=True), name="compare")

# ============ REQUEST MODELS ============

class TrafficLog(BaseModel):
    hour: int = Field(ge=0, le=23, description="Hour of day (0–23)")
    request_rate: int = Field(ge=0, description="Requests per minute")
    payload_size_kb: int = Field(ge=0, description="Payload size in KB")
    geo_location: str = Field(min_length=1, max_length=100)
    endpoint: str = Field(min_length=1, max_length=200)

class ZKPProof(BaseModel):
    user_id: str
    signature: str  # Hex-encoded signature
    challenge: str  # Hex-encoded challenge

class TrafficLogWithZKP(BaseModel):
    # Traffic data
    hour: int = Field(ge=0, le=23)
    request_rate: int = Field(ge=0)
    payload_size_kb: int = Field(ge=0)
    geo_location: str = Field(min_length=1, max_length=100)
    endpoint: str = Field(min_length=1, max_length=200)
    # ZKP proof (optional for backward compatibility)
    zkp_proof: Optional[ZKPProof] = None

class UserRegistration(BaseModel):
    user_id: str
    public_key_pem: str  # PEM-encoded public key

# ============ HELPER FUNCTIONS ============

def _make_log_entry(log, status: str, risk_score: float, zkp_verified, blocked_by=None) -> dict:
    """Build a standardized log entry dict to avoid repetition."""
    return {
        "timestamp": time.time(),
        "status": status,
        "risk_score": float(risk_score),
        "geo": log.geo_location,
        "endpoint": log.endpoint,
        "rate": log.request_rate,
        "payload": log.payload_size_kb,
        "zkp_verified": zkp_verified,
        "blocked_by": blocked_by,
    }

# ============ BASIC ENDPOINTS ============

@app.get("/")
def home():
    return {"message": "Intent-Aware Security Gateway is Running. Send POST to /verify"}

@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": model is not None}

@app.get("/stats")
def get_stats():
    with _stats_lock:
        stats_snapshot = dict(stats)
    duration = time.time() - stats_snapshot["start_time"]
    return {
        **stats_snapshot,
        "uptime_seconds": round(duration, 2),
        "pass_rate": round(1 - (stats_snapshot["blocked_requests"] / max(1, stats_snapshot["total_requests"])), 2),
        "zkp_success_rate": round(
            1 - (stats_snapshot["zkp_failures"] / max(1, stats_snapshot["zkp_enabled_requests"])), 2
        ) if stats_snapshot["zkp_enabled_requests"] > 0 else 1.0,
        "security_config": security_config
    }

@app.get("/logs")
def get_logs():
    return list(recent_logs)

@app.post("/stats/reset")
def reset_stats():
    """Reset all counters and logs — useful for demo resets without restarting the server."""
    global stats
    with _stats_lock:
        stats["total_requests"] = 0
        stats["blocked_requests"] = 0
        stats["zkp_enabled_requests"] = 0
        stats["zkp_failures"] = 0
        stats["start_time"] = time.time()
    recent_logs.clear()
    return {"status": "reset", "message": "Stats and logs cleared"}

# ============ SECURITY CONFIGURATION ENDPOINTS ============

@app.get("/security/config")
def get_security_config():
    """Get current security layer configuration"""
    return security_config

@app.post("/security/config")
def update_security_config(payload: dict):
    """Update security layer configuration (toggle ZKP/ML)"""
    global security_config

    if "zkp_enabled" in payload:
        security_config["zkp_enabled"] = bool(payload["zkp_enabled"])
    if "ml_enabled" in payload:
        security_config["ml_enabled"] = bool(payload["ml_enabled"])

    return {
        "status": "updated",
        "config": security_config
    }

# ============ LEGACY VERIFICATION ENDPOINT ============

@app.post(config.VERIFY_ENDPOINT)
def verify_request(log: TrafficLog):
    _inc_stat("total_requests")

    if model is None:
        raise HTTPException(status_code=503, detail={"status": "error", "message": "Model not loaded. Run train_model.py first."})

    # Feature Engineering (same as training)
    is_foreign = 0 if log.geo_location == "India" else 1
    risky_endpoints = ['/bulk_export', '/admin_login']
    is_risky = 1 if log.endpoint in risky_endpoints else 0

    # Prepare DataFrame for prediction
    features = pd.DataFrame([{
        'hour': log.hour,
        'request_rate': log.request_rate,
        'payload_size_kb': log.payload_size_kb,
        'is_foreign_ip': is_foreign,
        'is_risky_endpoint': is_risky
    }])

    # IsolationForest: 1 = normal, -1 = anomaly
    prediction = model.predict(features)[0]
    score = model.decision_function(features)[0]

    entry = {
        "timestamp": time.time(),
        "status": "ALLOWED",
        "risk_score": float(score),
        "geo": log.geo_location,
        "endpoint": log.endpoint,
        "rate": log.request_rate,
        "payload": log.payload_size_kb,
        "zkp_verified": None  # Legacy endpoint — ZKP not applicable
    }

    if prediction == -1:
        _inc_stat("blocked_requests")
        entry["status"] = "BLOCKED"
        recent_logs.append(entry)
        raise HTTPException(status_code=403, detail={
            "status": "BLOCKED",
            "risk_score": float(score),
            "reason": "Anomaly Detected by Isolation Forest"
        })

    recent_logs.append(entry)
    return {
        "status": "ALLOWED",
        "risk_score": float(score),
        "message": "Request authorized"
    }

# ============ ZKP ENDPOINTS ============

@app.post("/zkp/register")
def register_user(registration: UserRegistration):
    """Register user's public key for ZKP authentication"""
    try:
        public_key = crypto_utils.ZKPKeyPair.load_public_key(registration.public_key_pem)
        with _keys_lock:
            user_public_keys[registration.user_id] = public_key
        return {
            "status": "success",
            "message": f"User {registration.user_id} registered successfully",
            "user_id": registration.user_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid public key: {str(e)}")

@app.get("/zkp/challenge")
def get_zkp_challenge(user_id: str):
    """Issue ZKP challenge to user"""
    with _keys_lock:
        registered = user_id in user_public_keys
    if not registered:
        raise HTTPException(status_code=404, detail="User not registered. Call /zkp/register first.")

    challenge = challenge_store.create_challenge(user_id)
    return {
        "challenge": challenge.hex(),
        "expires_in": 60  # seconds
    }

@app.post("/verify_zkp")
def verify_request_with_zkp(log: TrafficLogWithZKP):
    """
    Enhanced verification endpoint with toggleable ZKP and ML layers.
    Demonstrates security effectiveness progression.
    """
    _inc_stat("total_requests")

    zkp_verified = None  # Default to None (N/A) if disabled

    # LAYER 1: ZKP AUTHENTICATION (if enabled)
    if security_config["zkp_enabled"]:
        if not log.zkp_proof:
            _inc_stat("zkp_failures")
            _inc_stat("blocked_requests")
            recent_logs.append(_make_log_entry(log, "BLOCKED", -1.0, False, "ZKP"))
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "risk_score": -1.0,
                "reason": "ZKP proof required",
                "layer": "ZKP"
            })

        _inc_stat("zkp_enabled_requests")

        with _keys_lock:
            public_key = user_public_keys.get(log.zkp_proof.user_id)

        if public_key is None:
            _inc_stat("zkp_failures")
            _inc_stat("blocked_requests")
            recent_logs.append(_make_log_entry(log, "BLOCKED", -1.0, False, "ZKP"))
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "risk_score": -1.0,
                "reason": "User not registered",
                "layer": "ZKP"
            })

        stored_challenge = challenge_store.get_challenge(log.zkp_proof.user_id)
        if stored_challenge is None:
            _inc_stat("zkp_failures")
            _inc_stat("blocked_requests")
            recent_logs.append(_make_log_entry(log, "BLOCKED", -1.0, False, "ZKP"))
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "risk_score": -1.0,
                "reason": "Challenge expired or already used",
                "layer": "ZKP"
            })

        if stored_challenge.hex() != log.zkp_proof.challenge:
            _inc_stat("zkp_failures")
            _inc_stat("blocked_requests")
            recent_logs.append(_make_log_entry(log, "BLOCKED", -1.0, False, "ZKP"))
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "risk_score": -1.0,
                "reason": "Challenge mismatch",
                "layer": "ZKP"
            })

        try:
            signature = bytes.fromhex(log.zkp_proof.signature)
            zkp_verified = crypto_utils.verify_signature(public_key, stored_challenge, signature)
        except Exception as e:
            _inc_stat("zkp_failures")
            _inc_stat("blocked_requests")
            recent_logs.append(_make_log_entry(log, "BLOCKED", -1.0, False, "ZKP"))
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "risk_score": -1.0,
                "reason": f"Invalid signature: {str(e)}",
                "layer": "ZKP"
            })

        if not zkp_verified:
            _inc_stat("zkp_failures")
            _inc_stat("blocked_requests")
            challenge_store.mark_used(log.zkp_proof.user_id)
            recent_logs.append(_make_log_entry(log, "BLOCKED", -1.0, False, "ZKP"))
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "risk_score": -1.0,
                "reason": "ZKP verification failed",
                "layer": "ZKP"
            })

        challenge_store.mark_used(log.zkp_proof.user_id)
        zkp_verified = True

    # LAYER 2: BEHAVIORAL ANALYSIS (if enabled)
    risk_score = 0.0

    if security_config["ml_enabled"]:
        if model is None:
            raise HTTPException(status_code=503, detail={"status": "error", "message": "Model not loaded"})

        is_foreign = 0 if log.geo_location == "India" else 1
        risky_endpoints = ['/bulk_export', '/admin_login']
        is_risky = 1 if log.endpoint in risky_endpoints else 0

        features = pd.DataFrame([{
            'hour': log.hour,
            'request_rate': log.request_rate,
            'payload_size_kb': log.payload_size_kb,
            'is_foreign_ip': is_foreign,
            'is_risky_endpoint': is_risky
        }])

        prediction = model.predict(features)[0]
        risk_score = model.decision_function(features)[0]

        if prediction == -1:
            _inc_stat("blocked_requests")
            recent_logs.append(_make_log_entry(log, "BLOCKED", risk_score, zkp_verified, "ML"))
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "risk_score": float(risk_score),
                "reason": "Anomaly detected by ML",
                "layer": "ML",
                "zkp_verified": zkp_verified
            })

    # ALLOWED — passed all enabled layers
    recent_logs.append(_make_log_entry(log, "ALLOWED", risk_score, zkp_verified, None))

    return {
        "status": "ALLOWED",
        "risk_score": float(risk_score),
        "message": "Request authorized",
        "zkp_verified": zkp_verified
    }

if __name__ == "__main__":
    import uvicorn
    print(f"[*] Starting API Gateway on {config.API_HOST}:{config.API_PORT}")
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
