import os
import sys
from Crypto.PublicKey import RSA

# Ensure keys are created at project root for shared usage
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
KEYS_DIR = os.path.join(PROJECT_ROOT, "keys")


def generate_rsa_keys() -> None:
    os.makedirs(KEYS_DIR, exist_ok=True)
    key = RSA.generate(2048)

    private_key = key.export_key()
    with open(os.path.join(KEYS_DIR, "private.pem"), "wb") as f:
        f.write(private_key)

    public_key = key.publickey().export_key()
    with open(os.path.join(KEYS_DIR, "public.pem"), "wb") as f:
        f.write(public_key)

    print(f"RSA keys generated and saved in '{KEYS_DIR}'.")


if __name__ == "__main__":
    generate_rsa_keys()


