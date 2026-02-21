# Intent-Aware Security for Identity Verification
## Group 4 - Introduction to Innovative Projects (PHY1901)

This project prototype demonstrates a machine learning-based "Privacy Wrapper" for identity verification systems like Aadhaar. It detects anomalous behavior (scraping, brute force attacks) based on intent rather than just credentials.

---

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have Python 3.8+ installed.

### 2. Installation
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Build the System
Generate synthetic traffic logs and train the anomaly detection model:

```bash
# Step 1: Generate Data
python generate_data.py

# Step 2: Train Model
python train_model.py
```
*You should see `traffic_logs.csv` and `model.pkl` appear in the `data/` folder.*

---

## 🖥️ Running the Demo

### Option 1: Automated Launch (Recommended)
Simply run the included batch file to start everything:
```bash
start_system.bat
```
*This will launch the API Gateway and open all three interfaces (Portal, Hacker Console, Dashboard) in your browser.*

### Option 2: Manual Launch
For manual control, open **2 separate terminal windows**:

#### Terminal 1: The API Gateway (Backend)
Start the FastAPI server that processes verification requests.
```bash
python app.py
```
*Server will start at http://127.0.0.1:8000*

#### Terminal 2: The Attacker Console
Launch the hacker simulation tool.
```bash
python attacker.py
```
*Use the menu to launch attacks and watch them get blocked in real-time.*

**Dashboard Access:** Open `http://localhost:8000/dashboard/index.html` in your browser.

---

## 📂 Project Structure

### Core Files
- `config.py`: Configuration settings (thresholds, paths)
- `generate_data.py`: Creates synthetic training data
- `train_model.py`: Trains the Isolation Forest model
- `app.py`: The security middleware (FastAPI backend)
- `attacker.py`: The attack simulation tool
- `crypto_utils.py`: Cryptographic utilities for Zero-Knowledge Proof (ZKP) authentication
- `test_zkp_integration.py`: Integration tests for the complete ZKP flow
- `zkp_simulation.py`: A simple demo of Zero Knowledge Proofs
- `start_system.bat`: Automated system launcher

### Frontend (static/)
- `portal/`: Government portal simulation
  - `zkp-client.js`: Client-side ZKP library for key generation and cryptographic signing
- `hacker/`: Hacker console interface
- `dashboard/`: Real-time security monitoring dashboard (HTML/JS/Chart.js)
- `compare/`: Security architecture comparison UI (Legitimate vs. Attack scenarios)
