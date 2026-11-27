"""Reproducible fingerprints of exact input file bytes."""
import hashlib


def sha256_input_bytes(data):
    """Hash bytes as supplied; do not normalize BOM, newlines or encoding."""
    if not isinstance(data, bytes):
        raise TypeError("input must be bytes")
    return hashlib.sha256(data).hexdigest()
