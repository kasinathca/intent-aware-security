import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib
import config
import os

# Ensure data exists
if not os.path.exists(os.path.join(config.DATA_DIR, config.DATA_FILE)):
    print(f"[!] Error: Data file not found at {os.path.join(config.DATA_DIR, config.DATA_FILE)}")
    print("    Run generate_data.py first.")
    exit()

print("[*] Loading dataset...")
df = pd.read_csv(os.path.join(config.DATA_DIR, config.DATA_FILE))

# Feature Engineering
print("[*] Preprocessing features...")
# We select relevant numerical features
features = ['hour', 'request_rate', 'payload_size_kb']

# Simple encoding for 'geo_location': 0 for India (safe), 1 for Foreign/Unknown (risky)
df['is_foreign_ip'] = df['geo_location'].apply(lambda x: 0 if x == 'India' else 1)
features.append('is_foreign_ip')

# Simple encoding for 'endpoint': 
# 0 for normal endpoints (e.g. /user_profile)
# 1 for risky endpoints (e.g. /bulk_export)
risky_endpoints = ['/bulk_export', '/admin_login']
df['is_risky_endpoint'] = df['endpoint'].apply(lambda x: 1 if x in risky_endpoints else 0)
features.append('is_risky_endpoint')

X = df[features]

# Train Isolation Forest
print(f"[*] Training Isolation Forest (n_estimators=100, contamination={config.CONTAMINATION})...")
model = IsolationForest(
    n_estimators=100,
    contamination=config.CONTAMINATION,
    random_state=config.RANDOM_STATE,
    n_jobs=-1
)

model.fit(X)

# Evaluate
print("[*] Evaluating model...")
df['pred'] = model.predict(X)
# IsolationForest returns -1 for anomalies, 1 for normal
# Map our 'label' column to match: normal -> 1, attack -> -1
df['true_label'] = df['label'].apply(lambda x: 1 if x == 'normal' else -1)

# Calculate accuracy metrics
correct = (df['pred'] == df['true_label']).sum()
accuracy = correct / len(df)
print(f"[+] Model Accuracy: {accuracy:.2%}")

# Count detected anomalies
anomalies_detected = (df['pred'] == -1).sum()
true_attacks = (df['true_label'] == -1).sum()
print(f"    - Total Records: {len(df)}")
print(f"    - True Attacks in Data: {true_attacks}")
print(f"    - Anomalies Detected by Model: {anomalies_detected}")

# Save Model
model_path = os.path.join(config.DATA_DIR, config.MODEL_FILE)
joblib.dump(model, model_path)
print(f"[+] Model saved to {model_path}")
