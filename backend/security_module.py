"""Pluggable encryption module for Second Brain.

Security properties:
- Uses a BB84-based *simulation* to derive a long-lived Master Key (MK).
- Uses AES-256-GCM for authenticated encryption.
- Envelope encryption:
  - Per-record Data Encryption Key (DEK) encrypts the memory plaintext.
  - MK encrypts (wraps) the DEK.

Database should store ONLY:
- ciphertext (base64 string)
- encrypted_dek (base64 string)

The MK is never written to the database. It exists only in process memory or can be
loaded from an environment variable as simulated secure storage.
"""

from __future__ import annotations

import base64
import os
import secrets
import threading
from hashlib import sha256
from typing import Optional, Tuple, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


# Process-global in-memory Master Key.
# Thread-safe to avoid races in async servers.
_MK_LOCK = threading.RLock()
_MASTER_KEY: Optional[bytes] = None  # 32 bytes


# Optional simulated secure storage: the application may provide the MK via env var
# on startup so existing data can be decrypted after restarts.
_ENV_MK_B64 = "SECOND_BRAIN_MASTER_KEY_B64"


def _b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _b64d(b64: str) -> bytes:
    return base64.b64decode(b64.encode("ascii"))


def _require_master_key() -> bytes:
    with _MK_LOCK:
        if _MASTER_KEY is None:
            raise RuntimeError(
                "Master Key is not initialized. Call initialize_master_key() once at startup."
            )
        return _MASTER_KEY


def _bb84_simulate_sifted_bits(target_bits: int = 512) -> bytes:
    """Simulate BB84 key sifting to obtain at least `target_bits` shared bits.

    This is a software-only simulation (no external services / no quantum hardware).

    High-level BB84 steps (simplified, no eavesdropper modeling):
    - Alice chooses random bits and random bases.
    - Bob chooses random measurement bases.
    - They publicly compare bases and keep only positions where bases match.

    Returns bytes containing packed sifted bits (LSB-first within each byte).
    """

    sifted = []  # list[int] of 0/1

    # Oversample to reduce loops; repeat until enough bits.
    while len(sifted) < target_bits:
        n = max(1024, target_bits * 4)

        alice_bits = [secrets.randbits(1) for _ in range(n)]
        alice_bases = [secrets.randbits(1) for _ in range(n)]  # 0=Z, 1=X

        bob_bases = [secrets.randbits(1) for _ in range(n)]

        # In an ideal no-noise channel with no eavesdropper, when bases match,
        # Bob's measured bit equals Alice's bit.
        for i in range(n):
            if alice_bases[i] == bob_bases[i]:
                sifted.append(alice_bits[i])
                if len(sifted) >= target_bits:
                    break

    # Pack bits into bytes.
    out = bytearray((target_bits + 7) // 8)
    for idx, bit in enumerate(sifted[:target_bits]):
        if bit:
            out[idx // 8] |= 1 << (idx % 8)
    return bytes(out)


def initialize_master_key() -> str:
    """Initialize the long-lived Master Key (MK).

    Behavior:
    - If env var SECOND_BRAIN_MASTER_KEY_B64 is present, loads MK from it.
    - Otherwise runs BB84 simulation once, derives a 32-byte MK, and keeps it only in memory.

    Returns:
        base64-encoded MK (so you can place it into process environment as simulated secure storage).

    IMPORTANT:
    - Do NOT store this returned value in the database.
    - If you do not persist it anywhere outside the DB, you will NOT be able to decrypt
      existing encrypted memories after a server restart.
    """

    global _MASTER_KEY

    with _MK_LOCK:
        env_val = os.getenv(_ENV_MK_B64)
        if env_val:
            mk = _b64d(env_val)
            if len(mk) != 32:
                raise ValueError(
                    f"{_ENV_MK_B64} must decode to exactly 32 bytes (AES-256 key)."
                )
            _MASTER_KEY = mk
            return env_val

        # BB84 simulation -> sifted shared bits -> derive MK
        sifted = _bb84_simulate_sifted_bits(target_bits=512)

        # Derive 32 bytes deterministically from sifted bits.
        # (We avoid storing intermediate plaintext keys anywhere persistent.)
        mk = sha256(sifted).digest()  # 32 bytes
        _MASTER_KEY = mk

        return _b64e(mk)


def encrypt_memory(plaintext: Union[str, bytes]) -> Tuple[str, str]:
    """Encrypt a memory/note and return (ciphertext_b64, encrypted_dek_b64).

    Output format (DB-friendly):
    - ciphertext_b64 encodes: nonce(12) || aesgcm_ciphertext_and_tag
    - encrypted_dek_b64 encodes: wrap_nonce(12) || wrapped_dek_and_tag

    Plaintext is never stored. DEK is unique per call (per DB row).
    """

    mk = _require_master_key()

    if isinstance(plaintext, str):
        pt = plaintext.encode("utf-8")
    else:
        pt = plaintext

    # Per-row DEK (AES-256)
    dek = secrets.token_bytes(32)

    # Encrypt content with DEK using AES-256-GCM
    content_nonce = secrets.token_bytes(12)
    content_aesgcm = AESGCM(dek)
    content_ct = content_aesgcm.encrypt(content_nonce, pt, b"second-brain:memory")

    ciphertext_b64 = _b64e(content_nonce + content_ct)

    # Wrap (encrypt) DEK with MK using AES-256-GCM
    wrap_nonce = secrets.token_bytes(12)
    wrap_aesgcm = AESGCM(mk)
    wrapped_dek = wrap_aesgcm.encrypt(wrap_nonce, dek, b"second-brain:dek")

    encrypted_dek_b64 = _b64e(wrap_nonce + wrapped_dek)

    # Best-effort key material cleanup (Python can't guarantee immediate zeroization).
    # We at least remove references promptly.
    del dek

    return ciphertext_b64, encrypted_dek_b64


def decrypt_memory(ciphertext: str, encrypted_dek: str) -> str:
    """Decrypt (ciphertext_b64, encrypted_dek_b64) and return plaintext string."""

    mk = _require_master_key()

    ct_blob = _b64d(ciphertext)
    if len(ct_blob) < 13:
        raise ValueError("Invalid ciphertext: too short")

    wrap_blob = _b64d(encrypted_dek)
    if len(wrap_blob) < 13:
        raise ValueError("Invalid encrypted_dek: too short")

    content_nonce, content_ct = ct_blob[:12], ct_blob[12:]
    wrap_nonce, wrapped_dek = wrap_blob[:12], wrap_blob[12:]

    # Unwrap DEK
    wrap_aesgcm = AESGCM(mk)
    dek = wrap_aesgcm.decrypt(wrap_nonce, wrapped_dek, b"second-brain:dek")

    if len(dek) != 32:
        raise ValueError("Unwrapped DEK has invalid length")

    # Decrypt content
    content_aesgcm = AESGCM(dek)
    pt = content_aesgcm.decrypt(content_nonce, content_ct, b"second-brain:memory")

    # Best-effort cleanup
    del dek

    return pt.decode("utf-8")


def rotate_master_key() -> str:
    """Rotate the Master Key (MK) by generating a new one (BB84 simulation).

    Returns:
        base64-encoded new MK.

    IMPORTANT:
    - Rotating the MK *does not automatically re-encrypt your database*.
    - After rotation, previously stored rows cannot be decrypted unless you either:
      - kept the old MK available during a migration window, and
      - re-wrapped each row's DEK under the new MK.

    This function intentionally stays minimal and pluggable; the migration procedure
    depends on your existing data access layer.
    """

    global _MASTER_KEY

    with _MK_LOCK:
        sifted = _bb84_simulate_sifted_bits(target_bits=512)
        mk = sha256(sifted).digest()
        _MASTER_KEY = mk
        return _b64e(mk)
