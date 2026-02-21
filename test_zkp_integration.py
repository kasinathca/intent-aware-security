"""
Quick integration test for ZKP system.
Tests the complete flow: registration → challenge → signing → verification
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import crypto_utils

def test_zkp_integration():
    """Test complete ZKP flow"""
    print("=" * 60)
    print("ZKP INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Keypair Generation
    print("\n[TEST 1] Keypair Generation")
    try:
        keypair = crypto_utils.ZKPKeyPair()
        public_pem = keypair.export_public_key()
        assert "BEGIN PUBLIC KEY" in public_pem
        print("  [OK] Keypair generated successfully")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False
    
    # Test 2: Challenge Store
    print("\n[TEST 2] Challenge Store")
    try:
        store = crypto_utils.ChallengeStore(expiry_seconds=60)
        challenge = store.create_challenge("test_user")
        assert len(challenge) == 32
        retrieved = store.get_challenge("test_user")
        assert challenge == retrieved
        print("  [OK] Challenge creation and retrieval working")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False
    
    # Test 3: Signature Verification (DER format)
    print("\n[TEST 3] Signature Verification (DER format)")
    try:
        keypair = crypto_utils.ZKPKeyPair()
        challenge = crypto_utils.generate_challenge()
        signature = crypto_utils.create_signature(keypair.private_key, challenge)
        is_valid = crypto_utils.verify_signature(keypair.public_key, challenge, signature)
        assert is_valid == True
        print("  [OK] DER signature verification working")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False
    
    # Test 4: Signature Verification (IEEE P1363 format - browser simulation)
    print("\n[TEST 4] Signature Verification (IEEE P1363 format)")
    try:
        keypair = crypto_utils.ZKPKeyPair()
        challenge = crypto_utils.generate_challenge()
        
        # Create DER signature
        der_signature = crypto_utils.create_signature(keypair.private_key, challenge)
        
        # Convert to IEEE P1363 (simulate browser)
        from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
        r, s = decode_dss_signature(der_signature)
        p1363_signature = r.to_bytes(32, 'big') + s.to_bytes(32, 'big')
        
        # Verify P1363 signature
        is_valid = crypto_utils.verify_signature(keypair.public_key, challenge, p1363_signature)
        assert is_valid == True
        print("  [OK] IEEE P1363 signature verification working")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False
    
    # Test 5: Replay Attack Prevention
    print("\n[TEST 5] Replay Attack Prevention")
    try:
        store = crypto_utils.ChallengeStore(expiry_seconds=60)
        challenge = store.create_challenge("test_user")
        
        # First retrieval should work
        retrieved1 = store.get_challenge("test_user")
        assert retrieved1 is not None
        
        # Mark as used
        store.mark_used("test_user")
        
        # Second retrieval should fail
        retrieved2 = store.get_challenge("test_user")
        assert retrieved2 is None
        print("  [OK] Replay attack prevention working")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False
    
    # Test 6: Public Key Load/Export
    print("\n[TEST 6] Public Key Load/Export")
    try:
        keypair1 = crypto_utils.ZKPKeyPair()
        pem = keypair1.export_public_key()
        
        # Load public key from PEM
        loaded_key = crypto_utils.ZKPKeyPair.load_public_key(pem)
        
        # Verify they work the same way
        challenge = crypto_utils.generate_challenge()
        signature = crypto_utils.create_signature(keypair1.private_key, challenge)
        is_valid = crypto_utils.verify_signature(loaded_key, challenge, signature)
        assert is_valid == True
        print("  [OK] Public key export/import working")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    print("\nZKP Integration Status: READY FOR DEPLOYMENT")
    return True

if __name__ == "__main__":
    success = test_zkp_integration()
    sys.exit(0 if success else 1)
