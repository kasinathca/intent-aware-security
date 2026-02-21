import pandas as pd
import numpy as np
import os
import random
from datetime import datetime, timedelta
import config

def ensure_data_dir():
    if not os.path.exists(config.DATA_DIR):
        os.makedirs(config.DATA_DIR)
        print(f"[+] Created directory: {config.DATA_DIR}")

def generate_ip(is_attack=False):
    if is_attack:
        # Attackers reuse a small pool of IPs (botnet nodes)
        return f"192.168.1.{random.randint(200, 210)}"
    else:
        # Normal users have diverse IPs
        return f"10.0.{random.randint(0, 255)}.{random.randint(0, 255)}"

def generate_dataset():
    ensure_data_dir()
    
    print(f"[*] Generating {config.TOTAL_RECORDS} synthetic records...")
    
    data = []
    
    # 1. Generate Normal Traffic
    num_normal = int(config.TOTAL_RECORDS * config.NORMAL_RATIO)
    for _ in range(num_normal):
        hour = random.choice(config.NORMAL_HOURS)
        req_rate = random.randint(*config.NORMAL_REQ_MIN_RANGE)
        payload = random.randint(*config.NORMAL_PAYLOAD_KB_RANGE)
        
        # Random timestamp within the last 30 days, set to the chosen hour
        base_date = datetime.now() - timedelta(days=random.randint(0, 30))
        ts = base_date.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
        
        data.append({
            "timestamp": ts,
            "hour": hour,
            "request_rate": req_rate,
            "payload_size_kb": payload,
            "ip_address": generate_ip(is_attack=False),
            "geo_location": "India",
            "endpoint": "/user_profile",
            "label": "normal"
        })

    # 2. Generate Attack Traffic
    num_attack = config.TOTAL_RECORDS - num_normal
    for _ in range(num_attack):
        hour = random.choice(config.ATTACK_HOURS)
        req_rate = random.randint(*config.ATTACK_REQ_MIN_RANGE)
        payload = random.randint(*config.ATTACK_PAYLOAD_KB_RANGE)
        
        base_date = datetime.now() - timedelta(days=random.randint(0, 30))
        ts = base_date.replace(hour=hour, minute=random.randint(0, 59), second=random.randint(0, 59))
        
        data.append({
            "timestamp": ts,
            "hour": hour,
            "request_rate": req_rate,
            "payload_size_kb": payload,
            "ip_address": generate_ip(is_attack=True),
            "geo_location": random.choice(["Russia", "China", "Unknown", "Tor_Exit"]),
            "endpoint": "/bulk_export",
            "label": "attack"
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Shuffle dataset
    df = df.sample(frac=1).reset_index(drop=True)
    
    # Save to CSV
    output_path = os.path.join(config.DATA_DIR, config.DATA_FILE)
    df.to_csv(output_path, index=False)
    
    print(f"[+] Data generation complete. Saved to {output_path}")
    print(f"    - Normal records: {num_normal}")
    print(f"    - Attack records: {num_attack}")
    print(f"    - Attack Ratio: {num_attack / config.TOTAL_RECORDS:.2%}")

if __name__ == "__main__":
    generate_dataset()
