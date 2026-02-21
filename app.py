from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from collections import deque
import joblib
import pandas as pd
import numpy as np
import config
import os
import time
from contextlib import asynccontextmanager
import crypto_utils
from typing import Optional

# Global variables for model and stats
model = None
stats = {
    "total_requests": 0,
    "blocked_requests": 0,
    "zkp_enabled_requests": 0,
    "zkp_failures": 0,
    "start_time": time.time()
}
# Store last 50 logs for live dashboard
recent_logs = deque(maxlen=50)

# ZKP Infrastructure
user_public_keys = {}  # Store registered user public keys
challenge_store = crypto_utils.ChallengeStore(expiry_seconds=60)

# Modern FastAPI Lifespan Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global model
    model_path = os.path.join(config.DATA_DIR, config.MODEL_FILE)
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        print(f"[+] Model loaded from {model_path}")
    else:
        print(f"[!] Warning: Model not found at {model_path}. Run train_model.py first.")
    yield
    # Shutdown (cleanup if needed)
    print("[*] Shutting down API Gateway...")

# Initialize FastAPI with lifespan
app = FastAPI(title="Intent-Aware Security Gateway", version="1.0", lifespan=lifespan)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

# Add CORS middleware for dashboard robustness
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files
app.mount("/portal", StaticFiles(directory="static/portal"), name="portal")
app.mount("/hacker", StaticFiles(directory="static/hacker"), name="hacker")
app.mount("/dashboard", StaticFiles(directory="static/dashboard", html=True), name="dashboard")

# Request Models
class TrafficLog(BaseModel):
    hour: int
    request_rate: int
    payload_size_kb: int
    geo_location: str
    endpoint: str

class ZKPProof(BaseModel):
    user_id: str
    signature: str  # Hex-encoded signature
    challenge: str  # Hex-encoded challenge

class TrafficLogWithZKP(BaseModel):
    # Traffic data
    hour: int
    request_rate: int
    payload_size_kb: int
    geo_location: str
    endpoint: str
    # ZKP proof (optional for backward compatibility)
    zkp_proof: Optional[ZKPProof] = None

class UserRegistration(BaseModel):
    user_id: str
    public_key_pem: str  # PEM-encoded public key

@app.get("/")
def home():
    return {"message": "Intent-Aware Security Gateway is Running. Send POST to /verify"}

@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": model is not None}

@app.get("/stats")
def get_stats():
    duration = time.time() - stats["start_time"]
    return {
        **stats,
        "uptime_seconds": round(duration, 2),
        "pass_rate": round(1 - (stats["blocked_requests"] / max(1, stats["total_requests"])), 2),
        "zkp_success_rate": round(
            1 - (stats["zkp_failures"] / max(1, stats["zkp_enabled_requests"])), 2
        ) if stats["zkp_enabled_requests"] > 0 else 0
    }

@app.get("/logs")
def get_logs():
    return list(recent_logs)

@app.post(config.VERIFY_ENDPOINT)
def verify_request(log: TrafficLog):
    global stats
    stats["total_requests"] += 1
    
    if model is None:
        return {"status": "error", "message": "Model not loaded"}

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
    
    # Predict
    # IsolationForest: 1 = normal, -1 = anomaly
    prediction = model.predict(features)[0]
    score = model.decision_function(features)[0]  # Lower score = more anomalous
    
    # Log Entry
    entry = {
        "timestamp": time.time(),
        "status": "ALLOWED",
        "risk_score": float(score),
        "geo": log.geo_location,
        "endpoint": log.endpoint,
        "rate": log.request_rate,
        "payload": log.payload_size_kb
    }
    
    # Logic: If prediction is -1, BLOCK
    if prediction == -1:
        stats["blocked_requests"] += 1
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
        # Load and validate public key
        public_key = crypto_utils.ZKPKeyPair.load_public_key(registration.public_key_pem)
        
        # Store public key
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
    # Check if user is registered
    if user_id not in user_public_keys:
        raise HTTPException(status_code=404, detail="User not registered. Call /zkp/register first.")
    
    # Generate and store challenge
    challenge = challenge_store.create_challenge(user_id)
    
    return {
        "challenge": challenge.hex(),
        "expires_in": 60  # seconds
    }

@app.post("/verify_zkp")
def verify_request_with_zkp(log: TrafficLogWithZKP):
    """
    Enhanced verification endpoint with ZKP authentication.
    Implements two-layer defense: ZKP (Layer 1) + Behavioral ML (Layer 2)
    """
    global stats
    stats["total_requests"] += 1
    
    # LAYER 1: ZKP AUTHENTICATION (if proof provided)
    zkp_verified = False
    if log.zkp_proof:
        stats["zkp_enabled_requests"] += 1
        
        # Get user's public key
        if log.zkp_proof.user_id not in user_public_keys:
            stats["zkp_failures"] += 1
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "reason": "User not registered",
                "layer": "ZKP"
            })
        
        public_key = user_public_keys[log.zkp_proof.user_id]
        
        # Retrieve challenge
        stored_challenge = challenge_store.get_challenge(log.zkp_proof.user_id)
        if stored_challenge is None:
            stats["zkp_failures"] += 1
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "reason": "Challenge expired or already used",
                "layer": "ZKP"
            })
        
        # Verify challenge matches
        if stored_challenge.hex() != log.zkp_proof.challenge:
            stats["zkp_failures"] += 1
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "reason": "Challenge mismatch",
                "layer": "ZKP"
            })
        
        # Verify signature
        try:
            signature = bytes.fromhex(log.zkp_proof.signature)
            zkp_verified = crypto_utils.verify_signature(public_key, stored_challenge, signature)
        except Exception as e:
            stats["zkp_failures"] += 1
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "reason": f"Invalid signature: {str(e)}",
                "layer": "ZKP"
            })
        
        if not zkp_verified:
            stats["zkp_failures"] += 1
            challenge_store.mark_used(log.zkp_proof.user_id)
            raise HTTPException(status_code=403, detail={
                "status": "BLOCKED",
                "reason": "ZKP verification failed",
                "layer": "ZKP"
            })
        
        # Mark challenge as used (prevent replay)
        challenge_store.mark_used(log.zkp_proof.user_id)
    
    # LAYER 2: BEHAVIORAL ANALYSIS (existing ML logic)
    if model is None:
        return {"status": "error", "message": "Model not loaded"}

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
    
    # Predict
    prediction = model.predict(features)[0]
    score = model.decision_function(features)[0]
    
    # Log Entry
    entry = {
        "timestamp": time.time(),
        "status": "ALLOWED",
        "risk_score": float(score),
        "geo": log.geo_location,
        "endpoint": log.endpoint,
        "rate": log.request_rate,
        "payload": log.payload_size_kb,
        "zkp_verified": zkp_verified
    }
    
    # Logic: If prediction is -1, BLOCK
    if prediction == -1:
        stats["blocked_requests"] += 1
        entry["status"] = "BLOCKED"
        recent_logs.append(entry)
        raise HTTPException(status_code=403, detail={
            "status": "BLOCKED",
            "risk_score": float(score),
            "reason": "Anomaly Detected by Isolation Forest",
            "layer": "Behavioral ML",
            "zkp_verified": zkp_verified
        })
    
    recent_logs.append(entry)
    return {
        "status": "ALLOWED",
        "risk_score": float(score),
        "message": "Request authorized",
        "zkp_verified": zkp_verified
    }

if __name__ == "__main__":
    import uvicorn
    print(f"[*] Starting API Gateway on {config.API_HOST}:{config.API_PORT}")
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)

