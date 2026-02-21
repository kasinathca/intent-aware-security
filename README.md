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

For the best presentation experience, open **3 separate terminal windows**:

### Terminal 1: The API Gateway (Backend)
Start the FastAPI server that processes verification requests.
```bash
python app.py
```
*Server will start at http://127.0.0.1:8000*

### Terminal 2: The Defender Dashboard (Frontend)
Launch the live visualization dashboard.
```bash
python -m streamlit run dashboard.py
```
*Browser will open automatically showing the dashboard.*

### Terminal 3: The Attacker Console
Launch the hacker simulation tool.
```bash
python attacker.py
```
*Use the menu to launch attacks and watch them get blocked in real-time on the Dashboard.*

---

## 📂 Project Structure

- `config.py`: Configuration settings (thresholds, paths).
- `generate_data.py`: Creates synthetic training data.
- `train_model.py`: Trains the Isolation Forest model.
- `app.py`: The security middleware (API).
- `dashboard.py`: The visualization interface.
- `attacker.py`: The attack simulation tool.
- `zkp_simulation.py`: A simple demo of Zero Knowledge Proofs.
