# API Reference

The entire system operations act via `app.py`, deployed utilizing standard FastAPI Uvicorn protocols on port `8000`. The API enforces robust validation defined sequentially via inherently typed Pydantic parameter boundaries.

## Endpoints

### 1. Register Public Key
Registers a new client's ECDSA P-256 Public Key (SPKI PEM format), anchoring identity strictly to local hardware parameters.
- **URL**: `/zkp/register`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "user_id": "string",
    "public_key_pem": "string"
  }
  ```
- **Response**: `200 OK` (Registration Confirmed)

### 2. Request ZKP Challenge
Retrieves a volatile (60-second execution lifecycle) cryptographically pseudo-random 32-byte hexadecimal nonce parameter unique to the defined `user_id`.
- **URL**: `/zkp/challenge/{user_id}`
- **Method**: `GET`
- **Response**:
  ```json
  {
    "challenge": "hex_string"
  }
  ```

### 3. Verification Gateway (ZKP/ML Engine Pipeline)
The primary architectural proxy. Transmits explicitly signed identity signatures over strictly measured traffic patterns. Sequentially processed. Rejects strictly unauthenticated interactions utilizing Zero-Knowledge-Proofs and isolates behavioral mimicry anomalies utilizing an Isolation Forest Engine.
- **URL**: `/verify_zkp`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "hour": "integer [0-23]",
    "request_rate": "integer [Req/Min]",
    "payload_size_kb": "integer",
    "geo_location": "string",
    "endpoint": "string",
    "zkp_data": {
       "user_id": "string",
       "signature": "hex_string",
       "challenge": "hex_string"
    }
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "status": "ALLOWED/BLOCKED",
    "risk_score": "float",
    "zkp_verified": "boolean"
  }
  ```
- **Denial Flags (403 Forbidden)**:
   Returns descriptive isolation categories depending on mitigation parameters (e.g., `Invalid Signature`, `Challenge Expired`, `Anomaly Detected`).

### 4. Legacy Validation (ML Engine Only)
Provides a simulated comparison environment directly demonstrating validation parameters acting without defined inherent Cryptographic Security boundaries (ZKP).
- **URL**: `/verify`
- **Method**: `POST`
- **Payload**: (Identical subset structural mapping excluding the strictly required `zkp_data` array).

### 5. Architectural Configuration
Administrative diagnostic utility endpoint strictly controlling global toggles over the ZKP and ML verification boundaries in real-time.
- **URL**: `/security/config`
- **Method**: `POST`, `GET`
- **Payload (POST)**:
  ```json
  {
    "zkp_enabled": "boolean",
    "ml_enabled": "boolean"
  }
  ```

### 6. Subsystem Telemetry Dashboard
Continuous continuous log propagation providing aggregated data values detailing network volume, risk threshold variables, and operational block constraints.
- **URL**: `/stats` (Aggregation) | `/logs` (Raw Telemetry)
- **Method**: `GET`
