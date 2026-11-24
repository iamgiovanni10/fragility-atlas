"""Input fingerprint regression tests."""
import hashlib
import pytest

from fragility_atlas.provenance import sha256_input_bytes


def test_hash_matches_exact_uploaded_bytes():
    raw = b"position_id,quantity,price_usd,eq\r\nA,1,1,2\r\n"
    assert sha256_input_bytes(raw) == hashlib.sha256(raw).hexdigest()


def test_bom_and_newline_changes_produce_distinct_fingerprints():
    plain = b"factor\n0.01\n"
    bom = b"\xef\xbb\xbffactor\n0.01\n"
    crlf = b"factor\r\n0.01\r\n"
    assert len({sha256_input_bytes(x) for x in (plain, bom, crlf)}) == 3


def test_non_bytes_rejected():
    with pytest.raises(TypeError):
        sha256_input_bytes("factor\n0.01\n")
