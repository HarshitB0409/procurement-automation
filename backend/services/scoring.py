from firebase import get_db
from models import ExtractedQuote, VendorScore


def _normalize(values: list[float], invert: bool = False) -> list[float]:
    if not values:
        return []
    min_v, max_v = min(values), max(values)
    if min_v == max_v:
        return [100.0] * len(values)
    scores = []
    for v in values:
        if invert:
            score = (max_v - v) / (max_v - min_v) * 100
        else:
            score = (v - min_v) / (max_v - min_v) * 100
        scores.append(score)
    return scores


def _lookup_vendor_catalog(vendor_name: str) -> dict:
    db = get_db()
    docs = db.collection("vendors").where("name", "==", vendor_name).limit(1).stream()
    for doc in docs:
        return doc.to_dict() or {}
    return {"sla_rating": 3.0, "compliance_verified": False}


def compute_vendor_scores(quotes: list[ExtractedQuote]) -> list[VendorScore]:
    if not quotes:
        return []

    prices = [q.total_price or q.unit_price for q in quotes]
    days = [q.delivery_days for q in quotes]

    price_scores = _normalize(prices, invert=True)
    speed_scores = _normalize([float(d) for d in days], invert=True)

    results: list[VendorScore] = []
    for i, quote in enumerate(quotes):
        catalog = _lookup_vendor_catalog(quote.vendor_name)
        sla = float(catalog.get("sla_rating", 3.0))
        rating_score = sla * 20
        total = price_scores[i] * 0.5 + speed_scores[i] * 0.3 + rating_score * 0.2
        results.append(
            VendorScore(
                vendor_name=quote.vendor_name,
                price=prices[i],
                delivery_days=quote.delivery_days,
                sla_rating=sla,
                price_score=round(price_scores[i], 2),
                speed_score=round(speed_scores[i], 2),
                rating_score=round(rating_score, 2),
                total_score=round(total, 2),
                compliance_verified=bool(catalog.get("compliance_verified", False)),
            )
        )

    results.sort(key=lambda x: x.total_score, reverse=True)
    return results
