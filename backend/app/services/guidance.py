"""
Explanation and safety guidance generator for the detection pipeline.
"""

from typing import List, Optional
from app.services.rules import DetectedIndicator


def generate_summary(
    risk_level: str,
    category: Optional[str],
    indicators: List[DetectedIndicator]
) -> str:
    """Generate a concise assessment headline."""
    if risk_level == "low":
        return "No obvious scam warning signs were detected in this message."

    category_labels = {
        "bank_payment": "bank or payment impersonation",
        "fake_job": "fraudulent job or task offers",
        "investment": "unrealistic investment or crypto schemes",
    }

    if risk_level == "high":
        if category and category in category_labels:
            return f"This message exhibits strong warning signs commonly associated with {category_labels[category]}."
        return "This message exhibits multiple high-risk warning signs commonly associated with fraud."

    # needs_verification
    if category and category in category_labels:
        return f"This message contains warning signs related to {category_labels[category]} that warrant verification."
    return "This message contains warning signs that warrant careful verification before taking action."


def generate_explanation(
    risk_level: str,
    category: Optional[str],
    indicators: List[DetectedIndicator]
) -> str:
    """
    Generate a cautious, contextual explanation strictly tied to detected indicators.
    """
    if risk_level == "low":
        return (
            "Our baseline analysis did not detect known red flags such as artificial urgency, "
            "credential requests, or unrealistic financial promises. However, absence of common "
            "indicators does not guarantee legitimacy. Targeted or newly crafted messages may not "
            "match standard patterns. Always verify unfamiliar requests through official channels."
        )

    # Build indicator-specific narrative points
    reasons = []
    codes = {ind.definition.code for ind in indicators}

    if "BANK_CREDENTIAL_HARVEST" in codes:
        reasons.append("it solicits sensitive credentials (such as PINs, passwords, or one-time security codes)")
    if "BANK_URGENT_ACTION" in codes:
        reasons.append("it applies artificial pressure threatening account suspension or immediate penalties")
    if "BANK_UNAUTHORIZED_ALERT" in codes:
        reasons.append("it presents an unverified transaction or debit alert designed to provoke an urgent reaction")
    if "BANK_PAYMENT_REDIRECT" in codes:
        reasons.append("it directs funds to unusual destinations like 'safe accounts', crypto wallets, or gift cards")
    if "JOB_UNREALISTIC_PAY" in codes:
        reasons.append("it offers unusually high compensation for simple, minimal, or vague remote tasks")
    if "JOB_UPFRONT_PAYMENT" in codes:
        reasons.append("it requires upfront payment for training, background checks, or equipment")
    if "JOB_NO_INTERVIEW_HIRE" in codes:
        reasons.append("it claims direct hiring or selection without a formal interview process")
    if "JOB_TASK_REBATE" in codes:
        reasons.append("it describes task-based commissions (e.g., liking videos or rating apps) requiring deposits")
    if "JOB_OFF_PLATFORM" in codes or "GEN_CHANNEL_HOPPING" in codes:
        reasons.append("it directs communication away from official platforms to personal messaging apps")
    if "INV_GUARANTEED_RETURNS" in codes:
        reasons.append("it promises guaranteed profits or risk-free investment returns")
    if "INV_URGENCY_FOMO" in codes:
        reasons.append("it uses limited-spot pressure or countdowns to rush an investment decision")
    if "INV_CRYPTO_PLATFORM" in codes:
        reasons.append("it promotes unverified automated crypto bots, liquidity pools, or deposit platforms")
    if "INV_INSIDER_MENTOR" in codes:
        reasons.append("it advertises unsolicited insider trading signals or portfolio management gurus")
    if "GEN_SUSPICIOUS_LINK" in codes and "BANK_CREDENTIAL_HARVEST" not in codes:
        reasons.append("it urges clicking an unverified link to resolve an urgent issue")

    if reasons:
        if len(reasons) == 1:
            reason_str = reasons[0]
        elif len(reasons) == 2:
            reason_str = f"{reasons[0]} and {reasons[1]}"
        else:
            reason_str = f"{', '.join(reasons[:-1])}, and {reasons[-1]}"
        
        explanation = (
            f"This message was flagged because {reason_str}. "
            "These characteristics are frequently observed in fraudulent communications. "
            "This assessment is decision support and not legal or forensic proof of fraud, "
            "but extreme care should be exercised before responding or transferring funds."
        )
    else:
        explanation = (
            "This message exhibits characteristics that warrant caution. "
            "Verify the authenticity of the sender independently before taking any requested action."
        )

    return explanation


def generate_safety_guidance(
    risk_level: str,
    category: Optional[str],
    indicators: List[DetectedIndicator]
) -> List[str]:
    """
    Produce curated, actionable safety advice based on category and detected indicators.
    """
    guidance = []
    codes = {ind.definition.code for ind in indicators}

    # Universal foundational advice
    if risk_level == "low":
        return [
            "Verify any unexpected requests through an official, trusted contact method.",
            "Never share passwords, PINs, or one-time verification codes with anyone.",
            "Do not forward or click links in unsolicited communications."
        ]

    # Category-specific guidance
    if category == "bank_payment" or any("BANK" in c for c in codes):
        guidance.append("Contact your bank directly using the official number on the back of your card or via their verified app.")
        guidance.append("Never share one-time passcodes (OTPs), PINs, or online banking passwords with anyone.")
        guidance.append("Do not transfer money to 'safe' or 'holding' accounts under any circumstances.")

    elif category == "fake_job" or any("JOB" in c for c in codes):
        guidance.append("Verify the job opening directly on the employer's official careers portal or corporate directory.")
        guidance.append("Never pay upfront fees for equipment, software, onboarding, or training materials.")
        guidance.append("Be wary of recruiters insisting on conducting formal hiring exclusively over WhatsApp or Telegram.")

    elif category == "investment" or any("INV" in c for c in codes):
        guidance.append("Remember that guaranteed high returns with zero risk do not exist in legitimate financial markets.")
        guidance.append("Check official financial regulatory registries (e.g., SEC, FCA) before depositing funds.")
        guidance.append("Never send cryptocurrency or grant remote wallet access to unverified third parties.")

    # Cross-cutting guidance based on specific signals
    if "GEN_SUSPICIOUS_LINK" in codes and len(guidance) < 3:
        guidance.append("Do not click links in unexpected messages; type the official website address directly into your browser.")

    # Fallback to general safety if guidance list is short
    if len(guidance) < 3:
        guidance.append("Never share personal identification, banking details, or security codes in response to a message.")
    if len(guidance) < 3:
        guidance.append("Take time to verify the claim independently before taking any urgent action.")

    return guidance[:3]
