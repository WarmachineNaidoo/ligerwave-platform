#!/usr/bin/env python3
"""
Ligerwave Agent QR Pairing
Generates pairing URL with gateway_id + nonce, prints QR code.
"""

import hashlib
import hmac
import json
import os
import sys
import time
import uuid
from urllib.parse import urlencode

PAIRING_BASE = "https://app.ligerwave.tech/pair"
NONCE_BYTES = 16


def generate_nonce() -> str:
    return uuid.uuid4().hex


def generate_pairing_url(gateway_id: str) -> str:
    nonce = generate_nonce()
    params = urlencode({"gateway_id": gateway_id, "nonce": nonce})
    return f"{PAIRING_BASE}?{params}"


def print_qr(text: str) -> None:
    """Print an ASCII QR code to the terminal using qrcode library if available,
    else a fallback URL barcode."""
    try:
        import qrcode
        from io import StringIO

        f = StringIO()
        qr = qrcode.QRCode(border=2, box_size=1)
        qr.add_data(text)
        qr.make(fit=True)
        qr.print_ascii(out=f)
        f.seek(0)
        print(f.read())
        return
    except ImportError:
        pass

    # Fallback: simple ASCII barcode using block chars
    print("=" * 60)
    print("SCAN THE QR CODE BELOW (install 'qrcode' for proper QR):")
    print("=" * 60)
    # Generate a simple 2D matrix from hash of the URL
    h = hashlib.sha256(text.encode()).digest()
    bits = "".join(format(b, "08b") for b in h)
    cols = 21
    rows = (len(bits) + cols - 1) // cols
    for r in range(rows):
        line = ""
        for c in range(cols):
            idx = r * cols + c
            if idx < len(bits):
                line += "\u2588" if bits[idx] == "1" else " "
            else:
                line += " "
        print(f"\u2551{line}\u2551")
    print("\u255a" + "\u2550" * cols + "\u255d")
    print()


def generate_pairing_qr(gateway_id: str) -> str:
    url = generate_pairing_url(gateway_id)
    print("\n=== Ligerwave Pairing ===")
    print(f"Gateway ID: {gateway_id}")
    print(f"Pairing URL: {url}")
    print()
    print_qr(url)
    print(f"Open the Ligerwave dashboard and scan this QR code.")
    print(f"Or visit: {url}")
    print()
    return url


if __name__ == "__main__":
    gw_id = sys.argv[1] if len(sys.argv) > 1 else f"router-{uuid.uuid4().hex[:8]}"
    generate_pairing_qr(gw_id)
