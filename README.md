# Intent-Aware Security for Identity Verification
## Group 4 - Introduction to Innovative Projects (PHY1901)

### About This Project
The **Intent-Aware Security System** is an advanced API middleware prototype designed to protect legacy identity verification infrastructure (e.g., Aadhaar OTP systems) against modern threat vectors like credential stuffing, automated scraping, and SS7/SIM-swapping. 

Unlike traditional platforms that rely strictly on credential validity, this project introduces a **dual-layer defense architecture**:
1. **Cryptographic Layer (ZKP):** Utilizes client-side ECDSA P-256 signatures and strict challenge-response nonces to authenticate users mathematically, without transmitting private secrets across the network.
2. **Behavioral Layer (Machine Learning):** Deploys an unsupervised `IsolationForest` anomaly detection engine to evaluate the *intent* of a request (timing, location, velocity, and payload mass), instantly terminating perfectly-spoofed mimicry attacks where cryptographic keys are bypassed or disabled.

---

## Quick Start

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

## Running the Demo

### Option 1: Automated Launch (Recommended)
Simply run the included batch file to start everything:
```bash
start_system.bat
```
*This will launch the API Gateway and open all necessary interfaces in your browser.*

### Option 2: Manual Launch
For manual control, open two separate terminal windows:

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

## Project Structure

### Core System
- `config.py`: Configuration settings (thresholds, file paths)
- `generate_data.py`: Creates synthetic training data for the model
- `train_model.py`: Trains the Isolation Forest model
- `app.py`: The security middleware (FastAPI backend)
- `attacker.py`: The attack simulation tool
- `crypto_utils.py`: Cryptographic utilities for Zero-Knowledge Proof (ZKP) authentication
- `test_zkp_integration.py`: Integration tests for the complete ZKP flow
- `zkp_simulation.py`: A simple command-line demonstration of Zero Knowledge Proofs
- `start_system.bat`: Automated system launcher script
- `requirements.txt`: Python package dependencies

### Frontend (`static/`)

The application serves multiple distinct frontend modules, organized by functional area:

#### 1. Portal (`static/portal/`)
Government portal simulation.
- `index.html`: Main portal interface
- `zkp-client.js`: Client-side ZKP library for key generation and cryptographic signing
- `timer-worker.js`: Web worker for portal session timeouts
- `ashoka_emblem.svg`: Interface graphical asset

#### 2. Hacker Interface (`static/hacker/`)
Hacker console interface simulation.
- `index.html`: Automated attack simulation interface

#### 3. Dashboard (`static/dashboard/`)
Real-time security monitoring dashboard.
- `index.html`: Main dashboard view
- `script.js`: Dashboard logic, charting, and real-time updates
- `style.css`: Dashboard styling

#### 4. Architecture Comparison (`static/compare/`)
Security architecture comparison UI (Legitimate vs. Attack scenarios).
- `index.html`: Comparison interface
- `compare.js`: Comparison logic and animations
- `style.css`: Comparison styling

#### 5. ZKP Demo (`static/demo/`)
Visual ZKP security demonstration.
- `index.html`: Interactive ZKP demonstration showcasing security layers
