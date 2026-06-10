"""QR-code helpers."""

from __future__ import annotations

import base64
from io import BytesIO

import qrcode


def make_qr_data_uri(payload: str) -> str:
    """Create a PNG QR code encoded as a data URI."""
    image = qrcode.make(payload)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
