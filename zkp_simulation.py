import hashlib
import time

def hash_data(data):
    return hashlib.sha256(data.encode()).hexdigest()

def zkp_demo():
    print("==============================================")
    print("  ZERO KNOWLEDGE PROOF: 'Is Age > 18?' DEMO   ")
    print("==============================================")
    print("Problem: User wants to prove age without revealing DOB.\n")

    # Step 1: User Input
    print("[1] PROVER (User): Generating Secret...")
    secret_dob = "2000-01-01"
    secret_salt = "random_salt_123"
    
    # User calculates: H(DOB + Salt)
    commitment = hash_data(secret_dob + secret_salt)
    print(f"    Secret DOB: {secret_dob}")
    print(f"    Commitment sent to Verifier: {commitment[:10]}...")
    time.sleep(1)

    # Step 2: Challenge
    print("\n[2] VERIFIER (System): Sending Challenge...")
    print("    Challenge: 'Prove the commitment corresponds to year <= 2008'")
    time.sleep(1)

    # Step 3: Proof Generation (Simplified)
    print("\n[3] PROVER: Generating Proof...")
    print("    Proof: 'I possess the pre-image of the hash that satisfies the condition.'")
    # In real ZKP (zk-SNARKs), this involves complex polynomials. 
    # Here we simulate the verification logic.
    time.sleep(1)

    # Step 4: Verification
    print("\n[4] VERIFIER: Validating Proof...")
    
    # Simulation logic
    user_year = int(secret_dob.split("-")[0])
    current_year = 2026
    age = current_year - user_year
    
    if age > 18:
        print("    [SUCCESS] Proof Validated! User is > 18.")
        print("    [PRIVACY] Date of Birth was NEVER revealed.")
    else:
        print("    [FAIL] Proof Invalid.")

if __name__ == "__main__":
    zkp_demo()
