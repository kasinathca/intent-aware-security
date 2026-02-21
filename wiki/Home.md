# Home

Welcome to the **Intent-Aware Security for Identity Verification** documentation wiki. 

This repository houses the source code and architectural documentation for a prototype "Privacy Wrapper" designed to secure identity verification systems (such as the Aadhaar authentication infrastructure). The system utilizes a dual-layer defense mechanism, combining Zero-Knowledge Proof (ZKP) cryptography with behavioral Machine Learning (ML) analysis, to detect anomalous behavior based on intent rather than relying solely on credential validity.

## Documentation Structure

This wiki provides comprehensive technical documentation for all system components. Please use the sidebar or the links below to navigate through the topics:

1. **[System Architecture](System-Architecture.md)**
   An overview of the middleware design, system boundaries, interaction flows, and the integration of frontend interfaces with the backend validation engine.

2. **[Cryptographic Security (ZKP)](Cryptographic-Security.md)**
   Detailed mathematical and implementation breakdown of the Zero-Knowledge Proof layer, including the Elliptic Curve Digital Signature Algorithm (ECDSA P-256) implementation, the challenge-response protocol, and replay-attack mitigation.

3. **[Machine Learning Engine](Machine-Learning-Engine.md)**
   Specifications regarding the behavioral analysis layer utilizing strictly unsupervised anomaly detection via the Isolation Forest algorithm. Contains details on feature selection, synthetic data distributions, and risk scoring logic.

4. **[API Reference](API-Reference.md)**
   Exhaustive documentation of the FastAPI endpoints, required JSON payloads, response structures, and HTTP status codes for system integration.

## Project Scope
This project was developed as part of academic research under Group 4 - Introduction to Innovative Projects (PHY1901), focused on establishing robust, future-proof defenses against credential stuffing, automated scraping, and SS7/SIM swapping vulnerabilities inherent in legacy OTP-based systems.
