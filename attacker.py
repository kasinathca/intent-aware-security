import requests
import time
import random
import sys
import threading

# ANSI Colors for Hacker Aesthetic
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

API_URL = "http://127.0.0.1:8000/verify"

def print_banner():
    print(requests.get(API_URL).text) # ensure server is up
    print(f"{GREEN}")
    print("========================================")
    print("      ATTACKER TERMINAL - v1.0          ")
    print("========================================")
    print(f"{RESET}")

def send_request(payload):
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print(f"{GREEN}[+] SUCCESS: Payload delivered (Risk: {response.json().get('risk_score', 0):.2f}){RESET}")
        elif response.status_code == 403:
            print(f"{RED}[!] BLOCKED: Target Defense Active (Risk: {response.json().get('detail', {}).get('risk_score', 0):.2f}){RESET}")
    except requests.exceptions.ConnectionError:
        print(f"{YELLOW}[!] ERROR: Cannot connect to Target (Server Down?){RESET}")

def normal_behavior():
    print(f"{GREEN}[*] Simulating Background Noise (Normal Users)...{RESET}")
    for i in range(10):
        payload = {
            "hour": random.randint(9, 17),
            "request_rate": random.randint(1, 10),
            "payload_size_kb": random.randint(1, 5),
            "geo_location": "India",
            "endpoint": "/user_profile"
        }
        send_request(payload)
        time.sleep(1)

def brute_force_attack():
    print(f"{RED}[*] INITIATING BRUTE FORCE (Credential Stuffing)...{RESET}")
    for i in range(20):
        print(f"{YELLOW}[*] Testing Credential Pair: admin:{random.randint(1000,9999)}{RESET}")
        payload = {
            "hour": 3,  # suspicious hour
            "request_rate": 150 + (i * 10), # rising rate
            "payload_size_kb": 2,
            "geo_location": "India", 
            "endpoint": "/admin_login" # risky endpoint
        }
        send_request(payload)
        time.sleep(0.2)

def scraping_attack():
    print(f"{RED}[*] STARTING AADHAAR DATA SCRAPING (Bulk Export)...{RESET}")
    for i in range(15):
        print(f"{YELLOW}[*] Downloading Batch: {i+1}/15 (Size: {50 + (i*5)}KB){RESET}")
        payload = {
            "hour": 2, # suspicious
            "request_rate": 20, 
            "payload_size_kb": 50 + (i * 10), # large payload
            "geo_location": "Russia", # foreign IP
            "endpoint": "/bulk_export"
        }
        send_request(payload)
        time.sleep(0.5)

def ddos_attack():
    print(f"{RED}[*] LAUNCHING DDoS (Distributed Denial of Service)...{RESET}")
    # Launch multiple threads to simulate concurrent hits
    def single_hit():
        payload = {
            "hour": 4,
            "request_rate": 1000,
            "payload_size_kb": 1,
            "geo_location": "Tor_Exit",
            "endpoint": "/verify"
        }
        send_request(payload)

    threads = []
    for _ in range(50):
        t = threading.Thread(target=single_hit)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    print(f"{RED}[!] Massive Traffic Wave Sent.{RESET}")


if __name__ == "__main__":
    while True:
        print_banner()
        print("1. 🟢 Normal User Sim")
        print("2. 🔴 Brute Force Attack")
        print("3. 🔴 Data Scraping Attack")
        print("4. 💀 DDoS Attack")
        print("5. Exit")
        
        choice = input(f"{GREEN}\nroot@kali:~# {RESET}")
        
        if choice == '1':
            normal_behavior()
        elif choice == '2':
            brute_force_attack()
        elif choice == '3':
            scraping_attack()
        elif choice == '4':
            ddos_attack()
        elif choice == '5':
            sys.exit()
        else:
            print("Invalid command.")
        
        input("\nPress Enter to continue...")
