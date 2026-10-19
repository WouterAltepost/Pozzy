"""Print a fresh VAPID key pair for Web Push, as the env vars the API reads.

    python scripts/vapid_keys.py

VAPID_PUBLIC_KEY is the browser's applicationServerKey (base64url, uncompressed P-256 point);
VAPID_PRIVATE_KEY is the raw 32 byte private key, base64url. Changing the pair later means
every device has to enable notifications again.
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


key = ec.generate_private_key(ec.SECP256R1())
private = key.private_numbers().private_value.to_bytes(32, "big")
public = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
print(f"VAPID_PUBLIC_KEY={b64(public)}")
print(f"VAPID_PRIVATE_KEY={b64(private)}")
print("VAPID_SUBJECT=mailto:you@example.com")
