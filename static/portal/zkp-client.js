/**
 * ZKP Client Library for Government Portal
 * Handles keypair generation, challenge-response, and cryptographic signing
 */

class ZKPClient {
    constructor(userId, apiBaseUrl = '') {
        this.userId = userId;
        this.apiBaseUrl = apiBaseUrl;
        this.privateKey = null;
        this.publicKey = null;
        this.isInitialized = false;
    }

    /**
     * Initialize ZKP client - generate or load keypair
     */
    async initialize() {
        try {
            // Check if keypair already exists in localStorage
            const storedPrivateKey = localStorage.getItem(`zkp_private_key_${this.userId}`);

            if (storedPrivateKey) {
                // Load existing keypair
                await this.loadKeypair(storedPrivateKey);
                console.log('[ZKP] Loaded existing keypair from storage');
            } else {
                // Generate new keypair
                await this.generateKeypair();
                console.log('[ZKP] Generated new keypair');
            }

            this.isInitialized = true;
            return true;
        } catch (error) {
            console.error('[ZKP] Initialization failed:', error);
            return false;
        }
    }

    /**
     * Generate new ECDSA keypair using Web Crypto API
     */
    async generateKeypair() {
        try {
            const keypair = await window.crypto.subtle.generateKey(
                {
                    name: 'ECDSA',
                    namedCurve: 'P-256'  // Same as SECP256R1 in Python
                },
                true,  // extractable
                ['sign', 'verify']
            );

            this.privateKey = keypair.privateKey;
            this.publicKey = keypair.publicKey;

            // Export and store private key
            const exportedPrivateKey = await window.crypto.subtle.exportKey('jwk', this.privateKey);
            localStorage.setItem(`zkp_private_key_${this.userId}`, JSON.stringify(exportedPrivateKey));

            // Register public key with server
            await this.registerPublicKey();

        } catch (error) {
            console.error('[ZKP] Keypair generation failed:', error);
            throw error;
        }
    }

    /**
     * Load keypair from stored JWK
     */
    async loadKeypair(storedPrivateKeyJWK) {
        try {
            const privateKeyJWK = JSON.parse(storedPrivateKeyJWK);

            this.privateKey = await window.crypto.subtle.importKey(
                'jwk',
                privateKeyJWK,
                {
                    name: 'ECDSA',
                    namedCurve: 'P-256'
                },
                true,
                ['sign']
            );

            // Derive public key
            const exportedPrivateKey = await window.crypto.subtle.exportKey('jwk', this.privateKey);
            delete exportedPrivateKey.d;  // Remove private component
            exportedPrivateKey.key_ops = ['verify'];

            this.publicKey = await window.crypto.subtle.importKey(
                'jwk',
                exportedPrivateKey,
                {
                    name: 'ECDSA',
                    namedCurve: 'P-256'
                },
                true,
                ['verify']
            );

        } catch (error) {
            console.error('[ZKP] Keypair loading failed:', error);
            throw error;
        }
    }

    /**
     * Export public key in PEM format for server registration
     */
    async exportPublicKeyPEM() {
        const exported = await window.crypto.subtle.exportKey('spki', this.publicKey);
        const exportedAsBase64 = btoa(String.fromCharCode(...new Uint8Array(exported)));
        const pem = `-----BEGIN PUBLIC KEY-----\n${exportedAsBase64.match(/.{1,64}/g).join('\n')}\n-----END PUBLIC KEY-----`;
        return pem;
    }

    /**
     * Register public key with server
     */
    async registerPublicKey() {
        try {
            const publicKeyPEM = await this.exportPublicKeyPEM();

            const response = await fetch(`${this.apiBaseUrl}/zkp/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: this.userId,
                    public_key_pem: publicKeyPEM
                })
            });

            if (!response.ok) {
                throw new Error(`Registration failed: ${response.statusText}`);
            }

            const result = await response.json();
            console.log('[ZKP] Public key registered:', result);
            return result;

        } catch (error) {
            console.error('[ZKP] Public key registration failed:', error);
            throw error;
        }
    }

    /**
     * Get challenge from server
     */
    async getChallenge() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/zkp/challenge?user_id=${this.userId}`);

            if (!response.ok) {
                throw new Error(`Challenge request failed: ${response.statusText}`);
            }

            const result = await response.json();
            return result.challenge;

        } catch (error) {
            console.error('[ZKP] Challenge request failed:', error);
            throw error;
        }
    }

    /**
     * Sign challenge with private key (create ZKP proof)
     */
    async signChallenge(challengeHex) {
        try {
            // Convert hex challenge to Uint8Array
            const challengeBytes = new Uint8Array(
                challengeHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16))
            );

            // Sign challenge
            const signature = await window.crypto.subtle.sign(
                {
                    name: 'ECDSA',
                    hash: 'SHA-256'
                },
                this.privateKey,
                challengeBytes
            );

            // Convert signature to hex
            const signatureHex = Array.from(new Uint8Array(signature))
                .map(b => b.toString(16).padStart(2, '0'))
                .join('');

            return signatureHex;

        } catch (error) {
            console.error('[ZKP] Challenge signing failed:', error);
            throw error;
        }
    }

    /**
     * Create ZKP proof for a request
     */
    async createProof() {
        if (!this.isInitialized) {
            throw new Error('ZKP client not initialized');
        }

        try {
            // 1. Get challenge from server
            const challenge = await this.getChallenge();

            // 2. Sign challenge
            const signature = await this.signChallenge(challenge);

            // 3. Return proof object
            return {
                user_id: this.userId,
                signature: signature,
                challenge: challenge
            };

        } catch (error) {
            console.error('[ZKP] Proof creation failed:', error);
            throw error;
        }
    }

    /**
     * Send authenticated request with ZKP proof
     */
    async sendAuthenticatedRequest(trafficData) {
        try {
            // Create ZKP proof
            const zkpProof = await this.createProof();

            // Combine traffic data with ZKP proof
            const requestData = {
                ...trafficData,
                zkp_proof: zkpProof
            };

            // Send to enhanced verification endpoint
            const response = await fetch(`${this.apiBaseUrl}/verify_zkp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail?.reason || 'Request blocked');
            }

            return result;

        } catch (error) {
            console.error('[ZKP] Authenticated request failed:', error);
            throw error;
        }
    }

    /**
     * Reset keypair (for testing or key rotation)
     */
    async resetKeypair() {
        localStorage.removeItem(`zkp_private_key_${this.userId}`);
        this.privateKey = null;
        this.publicKey = null;
        this.isInitialized = false;
        await this.initialize();
    }
}

// Export for use in portal
window.ZKPClient = ZKPClient;
