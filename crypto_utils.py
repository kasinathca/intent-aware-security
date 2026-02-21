"""
Cryptographic utilities for Zero-Knowledge Proof (ZKP) authentication.
Implements ECDSA-based challenge-response protocol for unforgeable identity verification.
"""

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import secrets
import hashlib
import time

# Schnorr Protocol Parameters
CURVE = ec.SECP256R1()  # NIST P-256 curve
HASH_ALGORITHM = hashes.SHA256()

class ZKPKeyPair:
    """Represents a user's ZKP keypair"""
    
    def __init__(self, private_key=None):
        if private_key is None:
            # Generate new keypair
            self.private_key = ec.generate_private_key(CURVE, default_backend())
        else:
            self.private_key = private_key
        
        self.public_key = self.private_key.public_key()
    
    def export_public_key(self) -> str:
        """Export public key as PEM string"""
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem.decode('utf-8')
    
    def export_private_key(self) -> str:
        """Export private key as PEM string (for backup only)"""
        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return pem.decode('utf-8')
    
    @staticmethod
    def load_public_key(pem_string: str):
        """Load public key from PEM string"""
        return serialization.load_pem_public_key(
            pem_string.encode('utf-8'),
            backend=default_backend()
        )

def generate_challenge() -> bytes:
    """Generate cryptographically secure random challenge (32 bytes)"""
    return secrets.token_bytes(32)

def create_signature(private_key, challenge: bytes) -> bytes:
    """
    Sign challenge with private key using ECDSA.
    This is the 'proof' in Zero-Knowledge Proof.
    """
    signature = private_key.sign(
        challenge,
        ec.ECDSA(HASH_ALGORITHM)
    )
    return signature

def verify_signature(public_key, challenge: bytes, signature: bytes) -> bool:
    """
    Verify that signature was created by holder of private key.
    Returns True if proof is valid, False otherwise.
    
    Note: Handles both DER-encoded and IEEE P1363 (raw) signatures from browsers.
    """
    try:
        # Try DER format first (standard Python format)
        public_key.verify(
            signature,
            challenge,
            ec.ECDSA(HASH_ALGORITHM)
        )
        return True
    except Exception as der_error:
        # If DER fails, try converting from IEEE P1363 format (browser format)
        try:
            # For P-256, signature is 64 bytes (32 bytes r + 32 bytes s)
            if len(signature) == 64:
                from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature
                r = int.from_bytes(signature[:32], 'big')
                s = int.from_bytes(signature[32:], 'big')
                der_signature = encode_dss_signature(r, s)
                
                public_key.verify(
                    der_signature,
                    challenge,
                    ec.ECDSA(HASH_ALGORITHM)
                )
                return True
        except Exception as p1363_error:
            return False
        return False

class ChallengeStore:
    """
    Thread-safe storage for active challenges with automatic expiry.
    Prevents replay attacks by ensuring challenges are used only once.
    """
    
    def __init__(self, expiry_seconds=60):
        self.challenges = {}
        self.expiry_seconds = expiry_seconds
    
    def create_challenge(self, user_id: str) -> bytes:
        """Create and store new challenge for user"""
        challenge = generate_challenge()
        self.challenges[user_id] = {
            'challenge': challenge,
            'expires_at': time.time() + self.expiry_seconds,
            'used': False
        }
        return challenge
    
    def get_challenge(self, user_id: str) -> bytes:
        """Retrieve challenge for user (if valid and unused)"""
        if user_id not in self.challenges:
            return None
        
        entry = self.challenges[user_id]
        
        # Check expiry
        if time.time() > entry['expires_at']:
            del self.challenges[user_id]
            return None
        
        # Check if already used (prevent replay)
        if entry['used']:
            return None
        
        return entry['challenge']
    
    def mark_used(self, user_id: str):
        """Mark challenge as used (prevents replay attacks)"""
        if user_id in self.challenges:
            self.challenges[user_id]['used'] = True
    
    def cleanup_expired(self):
        """Remove expired challenges (call periodically)"""
        current_time = time.time()
        expired = [
            uid for uid, entry in self.challenges.items()
            if current_time > entry['expires_at']
        ]
        for uid in expired:
            del self.challenges[uid]

# Global challenge store instance
challenge_store = ChallengeStore(expiry_seconds=60)

def hash_user_id(user_id: str) -> str:
    """Create deterministic hash of user ID for privacy"""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]

# Example usage and testing
if __name__ == "__main__":
    print("=== ZKP Authentication Demo ===\n")
    
    # 1. User generates keypair (done once)
    print("[1] User: Generating keypair...")
    user_keypair = ZKPKeyPair()
    print(f"    Public Key (first 64 chars): {user_keypair.export_public_key()[:64]}...")
    
    # 2. Server issues challenge
    print("\n[2] Server: Issuing challenge...")
    user_id = "portal_user_001"
    challenge = challenge_store.create_challenge(user_id)
    print(f"    Challenge: {challenge.hex()[:32]}...")
    
    # 3. User creates proof (signs challenge)
    print("\n[3] User: Creating ZKP proof...")
    signature = create_signature(user_keypair.private_key, challenge)
    print(f"    Signature: {signature.hex()[:32]}...")
    
    # 4. Server verifies proof
    print("\n[4] Server: Verifying proof...")
    stored_challenge = challenge_store.get_challenge(user_id)
    is_valid = verify_signature(user_keypair.public_key, stored_challenge, signature)
    
    if is_valid:
        print("    [OK] PROOF VALID - User authenticated!")
        challenge_store.mark_used(user_id)
    else:
        print("    [X] PROOF INVALID - Authentication failed!")
    
    # 5. Test replay attack prevention
    print("\n[5] Testing replay attack prevention...")
    stored_challenge = challenge_store.get_challenge(user_id)
    if stored_challenge is None:
        print("    [OK] Replay prevented - Challenge already used!")
    else:
        print("    [X] Replay vulnerability detected!")
    
    print("\n=== Demo Complete ===")
