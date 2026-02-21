import requests
import time
import random
import sys
import os
import config

# ANSI Colors for Hacker Aesthetic
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

API_URL = config.API_URL + config.VERIFY_ENDPOINT

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print(f"{RED}{BOLD}")
    print("========================================")
    print("      [!] ATTACKER CONSOLE v2.0         ")
    print("      Target: Government API Gateway    ")
    print("========================================")
    print(f"{RESET}")
    print("Use this terminal to launch simulated cyber-attacks.")
    print("Observe the DEFENDER DASHBOARD to see the reaction.\n")

def send_request(payload, quiet=False):
    try:
        response = requests.post(API_URL, json=payload)
        risk = response.json().get('risk_score', 0)
        
        if response.status_code == 200:
            if not quiet:
                print(f"{GREEN}[OK] 200 OK | PASSED | Risk: {risk:.2f} | Payload: {payload['payload_size_kb']}KB{RESET}")
            return "PASSED"
        elif response.status_code == 403:
            if not quiet:
                risk_blocked = response.json().get('detail', {}).get('risk_score', -1.0)
                print(f"{RED}[BLOCKED] 403 FORBIDDEN | Risk: {risk_blocked:.2f} | Reason: Anomaly Detected{RESET}")
            return "BLOCKED"
    except requests.exceptions.RequestException as e:
        print(f"{YELLOW}[!] Connection Error: {e} (Is app.py running?){RESET}")
        return "ERROR"

def normal_behavior():
    print(f"\n{CYAN}--- SCENARIO 1: NORMAL TRAFFIC ---{RESET}")
    print("Simulating legitimate users accessing their profiles...")
    print("Expected Result: GREEN lines, Low Risk Scores.\n")
    time.sleep(1)
    
    for i in range(10):
        payload = {
            "hour": random.randint(9, 17),
            "request_rate": random.randint(1, 10),
            "payload_size_kb": random.randint(1, 5),
            "geo_location": "India",
            "endpoint": "/user_profile"
        }
        send_request(payload)
        time.sleep(0.8)
    print(f"\n{GREEN}[OK] Normal Simulation Complete.{RESET}")

def brute_force_attack():
    print(f"\n{YELLOW}--- SCENARIO 2: BRUTE FORCE ATTACK ---{RESET}")
    print("Attempting credential stuffing at high velocity...")
    print("Targeting: /admin_login at 3:00 AM")
    print("Expected Result: RED spikes, Blocked Requests.\n")
    time.sleep(2)

    for i in range(15):
        rate = 150 + (i * 20)
        print(f"{YELLOW}[*] Attempt {i+1}: Rate={rate} req/min...{RESET}", end=" ")
        payload = {
            "hour": 3,
            "request_rate": rate,
            "payload_size_kb": 2,
            "geo_location": "India", 
            "endpoint": "/admin_login"
        }
        send_request(payload)
        time.sleep(0.3)
    print(f"\n{RED}[!] Attack Sequence Finished.{RESET}")

def scraping_attack():
    print(f"\n{YELLOW}--- SCENARIO 3: DATA SCRAPING ---{RESET}")
    print("Attempting to download massive datasets (Bulk Export)...")
    print("Source: Foreign IP (Russia)")
    print("Expected Result: Immediate blockage due to Payload Size & Geo.\n")
    time.sleep(2)

    for i in range(10):
        size = 50 + (i * 10)
        print(f"{YELLOW}[*] Requesting Batch {i+1}: Size={size}KB...{RESET}", end=" ")
        payload = {
            "hour": 2,
            "request_rate": 20, 
            "payload_size_kb": size,
            "geo_location": "Russia", 
            "endpoint": "/bulk_export"
        }
        send_request(payload)
        time.sleep(0.8)
    print(f"\n{RED}[!] Scraping Attempt Finished.{RESET}")

if __name__ == "__main__":
    # check connectivity first
    try:
        requests.get("http://127.0.0.1:8000")
    except requests.exceptions.ConnectionError:
        print(f"{RED}[!] ERROR: Cannot connect to API Gateway.")
        print(f"    Please run 'python app.py' in a separate terminal first.{RESET}")
        sys.exit()

    while True:
        print_header()
        print(f"{GREEN}1. [NORMAL]   Simulate Regular User Traffic{RESET}")
        print(f"{YELLOW}2. [ATTACK]   Launch Brute Force Attack (Velocity Test){RESET}")
        print(f"{RED}3. [ATTACK]   Launch Data Scraping (Payload/Geo Test){RESET}")
        print(f"{CYAN}4. [EXIT]     Quit Console{RESET}")
        
        choice = input(f"\n{BOLD}Select Command > {RESET}")
        
        if choice == '1':
            normal_behavior()
        elif choice == '2':
            brute_force_attack()
        elif choice == '3':
            scraping_attack()
        elif choice == '4':
            sys.exit()
        
        input(f"\n{CYAN}[Press Enter to return to menu]{RESET}")
