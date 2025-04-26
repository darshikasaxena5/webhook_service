import hashlib
import hmac
from typing import Optional

def verify_signature(secret: Optional[str], request_body: bytes, signature_header: Optional[str]) -> bool:
    """Verifies the HMAC-SHA256 signature of the request body.

    Args:
        secret: The secret key for the subscription. If None, verification is skipped (passes).
        request_body: The raw request body bytes.
        signature_header: The content of the signature header (e.g., 'X-Webhook-Signature-256').
                          Expected format: 'sha256=<hex_digest>'.

    Returns:
        True if the signature is valid or if no secret is configured, False otherwise.
    """
    if not secret:
        # No secret configured for this subscription, skip verification
        return True

    if not signature_header:
        # Secret is configured, but no signature provided in the header
        print("Signature verification failed: Header missing")
        return False

    try:
        # Extract the provided signature hash from the header
        method, signature_hash = signature_header.split('=', 1)
        if method.lower() != 'sha256':
            print(f"Signature verification failed: Unsupported method '{method}'")
            return False
    except ValueError:
        print("Signature verification failed: Invalid header format")
        return False

    # Calculate the expected signature
    mac = hmac.new(secret.encode('utf-8'), msg=request_body, digestmod=hashlib.sha256)
    expected_signature = mac.hexdigest()

    # Compare signatures securely
    if not hmac.compare_digest(expected_signature, signature_hash):
        print("Signature verification failed: Mismatch")
        return False

    # Signatures match
    print("Signature verification successful.")
    return True 