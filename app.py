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

# Global variables for model and stats
model = None
stats = {
    "total_requests": 0,
    "blocked_requests": 0,
    "start_time": time.time()
}
# Store last 50 logs for live dashboard
recent_logs = deque(maxlen=50)

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

# Request Model
class TrafficLog(BaseModel):
    hour: int
    request_rate: int
    payload_size_kb: int
    geo_location: str
    endpoint: str

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
        "pass_rate": round(1 - (stats["blocked_requests"] / max(1, stats["total_requests"])), 2)
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

if __name__ == "__main__":
    import uvicorn
    print(f"[*] Starting API Gateway on {config.API_HOST}:{config.API_PORT}")
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
