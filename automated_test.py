import requests
import time
import random
import threading

API_URL = "http://127.0.0.1:8000/verify"

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def send_request(payload, desc="Request"):
    try:
        response = requests.post(API_URL, json=payload)
        status = "PASSED" if response.status_code == 200 else "BLOCKED"
        color = GREEN if status == "PASSED" else RED
        print(f"{color}[{status}] {desc} | Payload: {payload['payload_size_kb']}KB{RESET}")
    except:
        print(f"{RED}[ERROR] API Unavailable{RESET}")

def run_test():
    print("--- [+] STARTING NORMAL TRAFFIC TEST ---")
    for i in range(5):
        payload = {
            "hour": 10, "request_rate": 5, "payload_size_kb": 2, 
            "geo_location": "India", "endpoint": "/profile"
        }
        send_request(payload, "Normal User")
        time.sleep(0.5)

    print("\n--- [-] STARTING ATTACK TRAFFIC TEST ---")
    for i in range(10):
        # Scraping Attack
        payload = {
            "hour": 2, "request_rate": 50, "payload_size_kb": 80, 
            "geo_location": "Russia", "endpoint": "/bulk_export"
        }
        send_request(payload, "Scraping Attack")
        time.sleep(0.5)

if __name__ == "__main__":
    # Wait for server to be up
    print("Waiting for API...")
    for _ in range(10):
        try:
            requests.get("http://127.0.0.1:8000/health")
            break
        except:
            time.sleep(1)
            
    run_test()
