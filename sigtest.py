import hmac
import hashlib
import json

def generate_signature(data, secret_key):
    message = json.dumps(data, sort_keys=True, separators=(',', ':'))
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
    return signature

def verify_signature(data, signature, secret_key):
    expected_signature = generate_signature(data, secret_key)
    return hmac.compare_digest(signature, expected_signature)

# Example usage
secret_key = "my_secret_key"

# Client-side: Generate signature
data = {
    "client_id": "abc123",
    "timestamp": 1234567890,
    "metrics": {
        "cpu_usage": 50.0,
        "memory_usage": 75.0
    }
}
signature = generate_signature(data, secret_key)
print("Generated signature:", signature)

# Server-side: Verify signature
is_valid = verify_signature(data, signature, secret_key)
print("Signature is valid:", is_valid)

# Tamper with the data
data["metrics"]["cpu_usage"] = 100.0

# Server-side: Verify tampered signature
is_valid = verify_signature(data, signature, secret_key)
print("Tampered signature is valid:", is_valid)