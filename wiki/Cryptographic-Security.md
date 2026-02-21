# Cryptographic Security (ZKP)

The Cryptographic Security layer mitigates credential theft by implementing a mechanism functionally identical to a Zero-Knowledge Proof (ZKP). Specifically, it proves possession of authorization without transmitting the authorization secret across the network. 

## Protocol Implementation: ECDSA over SECP256R1

The implementation relies on the Elliptic Curve Digital Signature Algorithm (ECDSA) utilizing the NIST P-256 (SECP256R1) curve. This standard provides a high level of security (128-bit symmetric equivalent) with minimal computational overhead, ensuring rapid authentication suitable for high-frequency API gateways.

### Key Management
The system necessitates asymmetric cryptography:
- **Private Key ($d$):** Generated entirely on the client-side using the `window.crypto.subtle` API. It resides exclusively locally (e.g., `localStorage` or ideally a Secure Enclave/TPM). It is never transmitted.
- **Public Key ($Q = dG$):** Exported in X.509 SubjectPublicKeyInfo (SPKI) PEM format and registered with the server.

### The Challenge-Response Handshake

To prevent interception and reuse of legitimate signatures, the system enforces a strict Challenge-Response protocol:

1. **Nonce Generation:** The server (`crypto_utils.py`) utilizes `secrets.token_bytes(32)` to generate a cryptographically secure 32-byte pseudo-random challenge nonce.
2. **Commitment Binding:** The server stores this nonce in a thread-safe `ChallengeStore` mapped to the `user_id`, alongside a rigid 60-second expiration timestamp.
3. **Proof Generation:** The client retrieves the nonce and signs it using the private key and a SHA-256 hash function: $Sign(PrivateKey, SHA256(Challenge))$.
4. **Verification:** The client submits the resulting signature. The server verifies the signature against the registered Public Key using the exact same nonce parameters.

### Defense Mechanisms

**1. Credential Stuffing & Phishing Immunity:**
Standard attacks rely on capturing a static password or OTP. Even if an attacker captures the traffic from a legitimate session, they only acquire the public signature and the specific nonce for that session. Because they do not possess the Private Key mathmatically required to sign a *new* nonce, subsequent login attempts are impossible.

**2. Replay Attack Prevention:**
The `ChallengeStore` utilizes a strict single-use policy. Upon a successful verification, the state of the challenge is immediately inverted to `used=True`. If an attacker intercepts a valid signature and attempts to resubmit the exact same payload a millisecond later, the server identifies the nonce as consumed and terminates the connection (`HTTP 403`).

**3. Format Interoperability Pipeline:**
Standard WebCrypto operations in JavaScript browsers natively generate IEEE P1363 raw signatures (a concatenated 64-byte array containing the $r$ and $s$ components). Conversely, standard Python `cryptography` verification methods anticipate ASN.1 DER-encoded signatures. 
The backend elegantly resolves this by implementing dual-verification logic: it initially attempts DER validation, and upon failure, dynamically invokes internal utility functions to structurally encode the raw 64-byte array into valid DER format before finalizing verification.
