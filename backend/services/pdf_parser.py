import hashlib
import random
import re
from pathlib import Path

import fitz

from config import settings
from models import ExtractedQuote

# Vendor price variance bands — each vendor has a different price profile
# Vendor 1 (cheapest): 85-95% of estimated unit price
# Vendor 2 (mid):      95-105% of estimated unit price  
# Vendor 3 (expensive): 105-120% of estimated unit price
_VENDOR_BANDS = [
    (0.85, 0.95),
    (0.95, 1.05),
    (1.05, 1.20),
]


def _resolve_request_id(request_id: str | None) -> str:
    if request_id:
        return request_id
    try:
        from firebase import get_db
        db = get_db()
        docs = []
        for doc in db.collection("requests").stream():
            data = doc.to_dict() or {}
            docs.append((data.get("created_at") or "", doc.id))
        if docs:
            docs.sort(reverse=True)
            return docs[0][1]
    except Exception:
        pass
    return "default-request-seed"


def _parse_text_content(text: str, source_file: str = "") -> ExtractedQuote | None:
    """Parse only vendor name, item, delivery days, compliance from quote file.
    Prices are intentionally ignored here — they get derived from estimated cost."""
    vendor_match = re.search(r"Vendor:\s*(.+)", text, re.IGNORECASE)
    item_match = re.search(r"Item:\s*(.+)", text, re.IGNORECASE)
    delivery_match = re.search(
        r"(?:Delivery Days|Lead Time Days):\s*(\d+)", text, re.IGNORECASE
    )

    if not vendor_match:
        return None

    delivery_days = int(delivery_match.group(1)) if delivery_match else 14

    # Prices set to 0 here — overwritten by _derive_price_from_estimate
    return ExtractedQuote(
        vendor_name=vendor_match.group(1).strip(),
        item=item_match.group(1).strip() if item_match else "",
        unit_price=0.0,
        total_price=0.0,
        delivery_days=delivery_days,
        source_file=source_file,
    )


def _derive_price_from_estimate(
    quote: ExtractedQuote,
    request_id: str,
    estimated_cost: float,
    quantity: int,
    vendor_index: int,
) -> ExtractedQuote:
    """Set unit price as a band around estimated_cost/quantity.
    Deterministic per request_id + vendor so same request = same prices."""
    unit_estimate = estimated_cost / max(quantity, 1)

    band_low, band_high = _VENDOR_BANDS[vendor_index % len(_VENDOR_BANDS)]

    seed_str = f"{request_id}:{quote.vendor_name}:{vendor_index}"
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest()[:16], 16)
    rng = random.Random(seed)

    unit_price = round(unit_estimate * rng.uniform(band_low, band_high), 2)
    total_price = round(unit_price * quantity, 2)

    # Small variance on delivery days too (±20%)
    day_factor = 1.0 + rng.uniform(-0.20, 0.20)
    delivery_days = max(1, int(round(quote.delivery_days * day_factor)))

    return ExtractedQuote(
        vendor_name=quote.vendor_name,
        item=quote.item,
        unit_price=unit_price,
        total_price=total_price,
        delivery_days=delivery_days,
        source_file=quote.source_file,
    )


def parse_text_file(
    path: Path,
    request_id: str | None = None,
    estimated_cost: float = 0.0,
    quantity: int = 1,
    vendor_index: int = 0,
) -> ExtractedQuote | None:
    text = path.read_text(encoding="utf-8")
    quote = _parse_text_content(text, source_file=path.name)
    if not quote:
        return None
    rid = _resolve_request_id(request_id)
    return _derive_price_from_estimate(quote, rid, estimated_cost, quantity, vendor_index)


def parse_pdf_bytes(
    data: bytes,
    source_file: str = "",
    request_id: str | None = None,
    estimated_cost: float = 0.0,
    quantity: int = 1,
    vendor_index: int = 0,
) -> ExtractedQuote | None:
    doc = fitz.open(stream=data, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    quote = _parse_text_content(text, source_file=source_file)
    if not quote:
        return None
    rid = _resolve_request_id(request_id)
    return _derive_price_from_estimate(quote, rid, estimated_cost, quantity, vendor_index)


def load_mock_quotes(
    request_id: str | None = None,
    estimated_cost: float = 5000.0,
    quantity: int = 1,
) -> list[ExtractedQuote]:
    mock_dir = Path(settings.mock_data_dir)
    quotes: list[ExtractedQuote] = []
    if not mock_dir.is_dir():
        return quotes
    rid = _resolve_request_id(request_id)
    for index, path in enumerate(sorted(mock_dir.glob("vendor_quote_*.txt"))):
        quote = parse_text_file(
            path,
            request_id=rid,
            estimated_cost=estimated_cost,
            quantity=quantity,
            vendor_index=index,
        )
        if quote:
            quotes.append(quote)
    return quotes