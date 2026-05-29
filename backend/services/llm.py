from openai import OpenAI

from config import settings
from models import VendorScore


def generate_justification(
    item: str,
    quantity: int,
    cost: float,
    department: str,
    vendor_scores: list[VendorScore],
) -> str:
    if not vendor_scores:
        return "No vendor scores available for justification."

    top = vendor_scores[0]
    fallback = (
        f"Recommended vendor: {top.vendor_name}. "
        f"Composite score {top.total_score}/100 "
        f"(price {top.price_score}, speed {top.speed_score}, rating {top.rating_score}). "
        f"Quoted price ${top.price:,.2f}, delivery {top.delivery_days} days, SLA {top.sla_rating}/5."
    )

    if not settings.openai_api_key:
        return fallback

    client = OpenAI(api_key=settings.openai_api_key)
    scores_text = "\n".join(
        f"- {v.vendor_name}: total={v.total_score}, price=${v.price}, days={v.delivery_days}, sla={v.sla_rating}"
        for v in vendor_scores[:5]
    )
    prompt = f"""You are a procurement analyst. Write a concise 2-3 sentence justification for selecting the top vendor.

Request: {item} x{quantity} for {department}, estimated cost ${cost:,.2f}.

Vendor scores (highest first):
{scores_text}

Top vendor to justify: {top.vendor_name}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Write brief professional procurement justifications."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
        )
        content = response.choices[0].message.content
        return content.strip() if content else fallback
    except Exception:
        return fallback
