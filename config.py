# Intent-Aware Security Configuration

# === DATA GENERATION ===
NORMAL_RATIO = 0.95
ATTACK_RATIO = 0.05
TOTAL_RECORDS = 20000

# Normal Behavior Profile
NORMAL_HOURS = list(range(8, 21))      # 8 AM to 8 PM
NORMAL_REQ_MIN_RANGE = (1, 15)         # Requests per minute
NORMAL_PAYLOAD_KB_RANGE = (1, 15)      # Payload size in KB

# Attacker Behavior Profile
ATTACK_HOURS = list(range(2, 5))       # 2 AM to 4 AM
ATTACK_REQ_MIN_RANGE = (100, 1000)     # High velocity
ATTACK_PAYLOAD_KB_RANGE = (20, 100)    # Large exports

# === PATHS ===
DATA_DIR = "data"
DATA_FILE = "traffic_logs.csv"
MODEL_FILE = "model.pkl"

# === ML PARAMETERS ===
CONTAMINATION = 0.05  # Expected percentage of anomalies
RANDOM_STATE = 42

# === API CONFIG ===
API_HOST = "127.0.0.1"
API_PORT = 8000
API_URL = f"http://{API_HOST}:{API_PORT}"
VERIFY_ENDPOINT = "/verify"
