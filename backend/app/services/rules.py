"""
Rules-based indicator detection taxonomy and contextual matchers.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.services.normalization import extract_urls


@dataclass(frozen=True)
class IndicatorDefinition:
    """Metadata definition for a scam indicator."""
    code: str
    label: str
    category: Optional[str]  # "bank_payment", "fake_job", "investment", or None
    strength: str  # "strong", "medium", "weak"
    description: str


@dataclass
class DetectedIndicator:
    """An indicator detected in a specific message."""
    definition: IndicatorDefinition
    evidence: str


# ---------------------------------------------------------------------------
# Indicator Registry
# ---------------------------------------------------------------------------

INDICATORS = {
    # Bank & Payment
    "BANK_URGENT_ACTION": IndicatorDefinition(
        code="BANK_URGENT_ACTION",
        label="Urgent request for account action",
        category="bank_payment",
        strength="medium",
        description="Message uses artificial urgency threatening account suspension, block, or penalty."
    ),
    "BANK_CREDENTIAL_HARVEST": IndicatorDefinition(
        code="BANK_CREDENTIAL_HARVEST",
        label="Request for sensitive credentials or security codes",
        category="bank_payment",
        strength="strong",
        description="Message asks the user to provide, reply with, or enter passwords, PINs, OTPs, or CVV."
    ),
    "BANK_UNAUTHORIZED_ALERT": IndicatorDefinition(
        code="BANK_UNAUTHORIZED_ALERT",
        label="Unverified transaction or security alert",
        category="bank_payment",
        strength="medium",
        description="Message fabricates an unauthorized debit or security charge to provoke an impulsive reaction."
    ),
    "BANK_PAYMENT_REDIRECT": IndicatorDefinition(
        code="BANK_PAYMENT_REDIRECT",
        label="Request to transfer funds to unusual or safe account",
        category="bank_payment",
        strength="strong",
        description="Message directs funds to be moved to a 'safe account', crypto wallet, or via gift cards."
    ),

    # Fake Job
    "JOB_UNREALISTIC_PAY": IndicatorDefinition(
        code="JOB_UNREALISTIC_PAY",
        label="Unrealistic compensation for minimal tasks",
        category="fake_job",
        strength="medium",
        description="Message advertises disproportionately high daily/hourly wages for simple or vague remote work."
    ),
    "JOB_NO_INTERVIEW_HIRE": IndicatorDefinition(
        code="JOB_NO_INTERVIEW_HIRE",
        label="Immediate hiring claim without formal interview",
        category="fake_job",
        strength="medium",
        description="Message claims the recipient is already selected or hired without an interview or application."
    ),
    "JOB_UPFRONT_PAYMENT": IndicatorDefinition(
        code="JOB_UPFRONT_PAYMENT",
        label="Demand for upfront onboarding or equipment fee",
        category="fake_job",
        strength="strong",
        description="Message requires upfront payment for registration, training kits, equipment, or background checks."
    ),
    "JOB_TASK_REBATE": IndicatorDefinition(
        code="JOB_TASK_REBATE",
        label="Task-based commission or review rebate scheme",
        category="fake_job",
        strength="medium",
        description="Message promotes commission for simple tasks (liking videos, rating apps) requiring deposits."
    ),
    "JOB_OFF_PLATFORM": IndicatorDefinition(
        code="JOB_OFF_PLATFORM",
        label="Directing job applicant to personal chat apps",
        category="fake_job",
        strength="weak",
        description="Message instructs candidate to contact recruiter or HR via Telegram or WhatsApp."
    ),

    # Investment
    "INV_GUARANTEED_RETURNS": IndicatorDefinition(
        code="INV_GUARANTEED_RETURNS",
        label="Guaranteed or risk-free return claims",
        category="investment",
        strength="strong",
        description="Message promises zero-risk, 100% guaranteed returns, or doubling money in short timeframes."
    ),
    "INV_URGENCY_FOMO": IndicatorDefinition(
        code="INV_URGENCY_FOMO",
        label="High-pressure investment urgency (FOMO)",
        category="investment",
        strength="medium",
        description="Message uses limited spots, countdowns, or exclusive VIP tier availability to rush investment."
    ),
    "INV_CRYPTO_PLATFORM": IndicatorDefinition(
        code="INV_CRYPTO_PLATFORM",
        label="Unverified crypto deposit or trading bot promotion",
        category="investment",
        strength="medium",
        description="Message solicits deposits into automated crypto bots, liquidity pools, or cloud mining."
    ),
    "INV_INSIDER_MENTOR": IndicatorDefinition(
        code="INV_INSIDER_MENTOR",
        label="Unsolicited trading signals or mentor claims",
        category="investment",
        strength="medium",
        description="Message promotes private insider trading signals, crypto gurus, or managed account schemes."
    ),

    # General / Cross-Cutting
    "GEN_SUSPICIOUS_LINK": IndicatorDefinition(
        code="GEN_SUSPICIOUS_LINK",
        label="Call to click an unverified link urgently",
        category=None,
        strength="medium",
        description="Message urges recipient to click an unverified link to resolve an issue or verify identity."
    ),
    "GEN_ANONYMOUS_SENDER": IndicatorDefinition(
        code="GEN_ANONYMOUS_SENDER",
        label="Impersonal or generic greeting",
        category=None,
        strength="weak",
        description="Message uses generic salutations like 'Dear Customer' or 'Attention User'."
    ),
    "GEN_CHANNEL_HOPPING": IndicatorDefinition(
        code="GEN_CHANNEL_HOPPING",
        label="Request to move conversation to private messaging",
        category=None,
        strength="weak",
        description="Message asks recipient to switch communication to WhatsApp, Telegram, or Signal."
    ),
}


# ---------------------------------------------------------------------------
# Contextual Matcher Functions
# ---------------------------------------------------------------------------

def detect_bank_urgent_action(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect urgency combined with account restrictions/penalties."""
    account_threat_pattern = r"\b(?:account|card|debit card|credit card|banking|wallet|profile|access)\b.*?\b(?:locked|suspended|blocked|frozen|restricted|closed|terminated|deactivated|disabled|compromised)\b"
    urgency_pattern = r"\b(?:urgent|immediately|within (?:24|12|48|2|1) (?:hours|hrs|hour)|right now|action required|as soon as possible|final notice|before (?:it is|account is)?\s*(?:closed|suspended|blocked))\b"

    if re.search(account_threat_pattern, text_lower) and re.search(urgency_pattern, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["BANK_URGENT_ACTION"],
            evidence="Combines account threat with immediate action requirement"
        )
    return None


def detect_bank_credential_harvest(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect requests for passwords, PINs, OTPs, or CVVs, while avoiding legitimate 2FA alerts."""
    # Guard against legitimate security advisories/2FA notifications
    negation_guard = r"\b(?:do not share|never share|never (?:ask|give)|will not ask|keep (?:it )?confidential|keep (?:this )?private|no one from)\b"
    if re.search(negation_guard, text_lower):
        return None

    request_verbs = r"\b(?:reply with|send (?:us|me)?|provide|enter (?:your)?|confirm (?:your)?|verify (?:your)?|share (?:your)?|input (?:your)?|submit (?:your)?|fill (?:out|in)|type)\b"
    credential_targets = r"\b(?:otp|one-time (?:passcode|password|code)|verification code|security code|pin|password|cvv|cvc|ssn|social security|full card (?:number|details)|banking (?:login|password|credentials))\b"

    combined_pattern = rf"{request_verbs}.*?{credential_targets}|{credential_targets}.*?{request_verbs}"
    if re.search(combined_pattern, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["BANK_CREDENTIAL_HARVEST"],
            evidence="Directly requests sensitive security credentials or one-time codes"
        )
    return None


def detect_bank_unauthorized_alert(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect fake transaction/fraud alerts designed to induce panic."""
    # Pattern indicating a specific debit or purchase alert
    tx_pattern = r"\b(?:charge|transaction|payment|debit|purchase|transfer)\b.*?(?:\$[0-9]+|[0-9]+\s*(?:usd|eur|gbp))\b.*?\b(?:approved|processed|attempted|authorized|declined)\b"
    # Action prompt that pushes to dispute or call
    panic_action = r"\b(?:if (?:this was )?not you|did not authorize|call (?:us|immediately)|click here to (?:cancel|reverse|dispute)|contact fraud)\b"

    if re.search(tx_pattern, text_lower) and re.search(panic_action, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["BANK_UNAUTHORIZED_ALERT"],
            evidence="Alerts of unauthorized transaction with urgent dispute prompt"
        )
    return None


def detect_bank_payment_redirect(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect instructions to transfer money to safe accounts, crypto, or gift cards."""
    redirect_pattern = r"\b(?:transfer|move|send)\b.*?\b(?:funds|money|balance)\b.*?\b(?:safe|secure|holding|reserve|investigation)\s+(?:account|wallet)\b"
    gift_card_pattern = r"\b(?:pay|resolve|verify)\b.*?\b(?:gift cards?|apple card|itunes card|google play card|target card)\b"
    crypto_redirect = r"\b(?:transfer|deposit|send)\b.*?\b(?:bitcoin|btc|usdt|crypto)\b.*?\b(?:to (?:protect|verify|resolve|secure)|to safe account)\b"

    if re.search(redirect_pattern, text_lower) or re.search(gift_card_pattern, text_lower) or re.search(crypto_redirect, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["BANK_PAYMENT_REDIRECT"],
            evidence="Directs payment to unusual holding accounts, crypto, or gift cards"
        )
    return None


def detect_job_unrealistic_pay(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect disproportionately high pay combined with simple/unskilled/remote work."""
    # Exclude standard annual corporate salaries (e.g., $100k-$150k/year)
    if re.search(r"\$[0-9]{2,3}(?:k|,000)\s*(?:-|to|/|per)\s*\$?[0-9]{2,3}(?:k|,000)?\s*(?:/|per)?\s*\b(?:year|annum|yr|annually)\b", text_lower):
        return None

    # High daily/hourly rate patterns
    high_pay = r"(?:\$[1-9][0-9]{2,}\s*(?:-|to|/|per)\s*\$?[0-9]*\s*(?:day|daily|hour|hr|per day|per hour)|[1-9][0-9]{2,}\s*usd\s*(?:daily|per day)|\$[3-9][0-9]\s*(?:per|/)\s*hour)"
    easy_work = r"\b(?:work from home|part[- ]time|no experience|on your phone|10-30 mins|simple tasks|typing|rating apps|watching videos|daily payout|flexible hours|remote data|online assistant|remote assistant)\b"

    if re.search(high_pay, text_lower) and re.search(easy_work, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["JOB_UNREALISTIC_PAY"],
            evidence="Advertises very high hourly/daily pay for minimal or simple remote tasks"
        )
    return None


def detect_job_no_interview_hire(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect claims of immediate hiring without screening."""
    hire_pattern = r"\b(?:you have been (?:selected|shortlisted|chosen)|you are (?:hired|accepted)|congratulations! your application was approved|no interview (?:needed|required)|start (?:working )?immediately without interview)\b"
    if re.search(hire_pattern, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["JOB_NO_INTERVIEW_HIRE"],
            evidence="Claims immediate hiring or selection without formal interview"
        )
    return None


def detect_job_upfront_payment(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect demands for upfront onboarding, registration, or equipment fees."""
    fee_pattern = r"\b(?:pay|deposit|purchase|send)\b.*?\b(?:upfront|registration|equipment|training|background check|clearance|onboarding)\s*(?:fee|deposit|cost|kit|materials)?\b"
    if re.search(fee_pattern, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["JOB_UPFRONT_PAYMENT"],
            evidence="Demands upfront payment for equipment, training, or onboarding"
        )
    return None


def detect_job_task_rebate(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect task or commission rebate schemes (e.g. like videos, deposit to unlock)."""
    task_pattern = r"\b(?:like (?:youtube|tiktok|instagram) videos?|rate (?:apps|hotels|movies|products)|subscribe to (?:channels|youtube)|complete (?:simple )?tasks for commission|deposit (?:money|funds|\$?[0-9]+) to unlock (?:tasks|commissions?|next level))\b"
    if re.search(task_pattern, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["JOB_TASK_REBATE"],
            evidence="Promotes task-based commission scheme requiring user interaction or deposits"
        )
    return None


def detect_job_off_platform(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect job communications directing candidate directly to chat apps."""
    off_platform = r"\b(?:contact|message|reach)\s*(?:our|the)?\s*(?:hr|manager|recruiter|assistant|team|supervisor)?\s*(?:on|via|at)?\s*(?:telegram|whatsapp|signal)\b|\bmessage @[a-zA-Z0-9_]+ on telegram\b"
    if re.search(off_platform, text_lower) and re.search(r"\b(?:job|position|interview|hiring|work|apply|salary|role|assistant)\b", text_lower):
        return DetectedIndicator(
            definition=INDICATORS["JOB_OFF_PLATFORM"],
            evidence="Directs job candidate to personal messaging apps for interview or details"
        )
    return None


def detect_inv_guaranteed_returns(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect guaranteed or zero-risk investment promises."""
    # Guard against legitimate disclaimers ("no guarantee", "cannot guarantee", "past performance is no guarantee")
    if re.search(r"\b(?:no guarantee|not guaranteed|cannot guarantee|past performance is no guarantee|no assurance)\b", text_lower):
        return None

    guarantee_pattern = r"\b(?:100%|completely )?guaranteed (?:profit|returns?|roi|earnings|income|payout)\b|\bzero risk (?:investment|profit|trading)\b|\bfixed (?:daily|weekly|monthly) returns? of [0-9]+%\b|\bdouble your (?:money|investment|crypto|bitcoin) in [0-9]+ (?:hours|days)\b"
    if re.search(guarantee_pattern, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["INV_GUARANTEED_RETURNS"],
            evidence="Promises guaranteed, risk-free, or fixed high investment returns"
        )
    return None


def detect_inv_urgency_fomo(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect investment-specific urgency or limited slot claims."""
    fomo_pattern = r"\b(?:only [0-9]+ spots? (?:left|remaining)|(?:vip|investment) (?:pool|slot|group) closing in [0-9]+ (?:hours|hrs|minutes)|exclusive investment (?:opportunity|window) act fast|don't miss this 100x (?:gem|opportunity))\b"
    if re.search(fomo_pattern, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["INV_URGENCY_FOMO"],
            evidence="Uses FOMO pressure and limited investment slot claims"
        )
    return None


def detect_inv_crypto_platform(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect promotions for automated trading bots, cloud mining, or unverified platforms."""
    crypto_pattern = r"\b(?:deposit\s+(?:crypto|btc|eth|usdt|bitcoin)|(?:automated|ai|algorithmic)?\s*(?:ai\s+)?(?:crypto|arbitrage|trading)\s+bot|liquidity mining (?:pool|platform)|cloud (?:mining|trading) platform)\b"
    if re.search(crypto_pattern, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["INV_CRYPTO_PLATFORM"],
            evidence="Promotes unverified crypto bots, mining pools, or deposit schemes"
        )
    return None


def detect_inv_insider_mentor(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect claims of financial gurus, insider trading signals, or account management."""
    mentor_pattern = r"\b(?:crypto guru|insider (?:trading )?signals?|expert analyst will manage your (?:portfolio|account|trades)|[0-9]{2}% accuracy (?:trading )?signals?|financial mentor)\b"
    if re.search(mentor_pattern, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["INV_INSIDER_MENTOR"],
            evidence="Promotes insider trading signals, gurus, or portfolio management"
        )
    return None


def detect_gen_suspicious_link(text_lower: str, original_text: str) -> Optional[DetectedIndicator]:
    """Detect urgent directives to click unverified links."""
    link_directive = r"\b(?:click (?:here|the link below|this link|link) (?:immediately|to verify|to confirm|to cancel|to claim|to update|to prevent|to resolve)|tap (?:here|the link) to (?:unlock|reactivate|verify))\b"
    urls = extract_urls(original_text)

    if re.search(link_directive, text_lower) or (urls and re.search(r"\b(?:click|tap|visit|verify now|cancel here)\b", text_lower)):
        return DetectedIndicator(
            definition=INDICATORS["GEN_SUSPICIOUS_LINK"],
            evidence="Urges clicking a link to resolve an issue or verify identity"
        )
    return None


def detect_gen_anonymous_sender(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect impersonal generic greetings at the beginning of a message."""
    greeting_pattern = r"^(?:dear (?:customer|user|client|account holder|valued customer|citizen)|attention (?:user|customer|account holder)|hello dear)\b"
    if re.search(greeting_pattern, text_lower.strip()):
        return DetectedIndicator(
            definition=INDICATORS["GEN_ANONYMOUS_SENDER"],
            evidence="Uses generic impersonal salutation without specific identity"
        )
    return None


def detect_gen_channel_hopping(text_lower: str) -> Optional[DetectedIndicator]:
    """Detect directives to move communication to personal chat apps."""
    channel_pattern = r"\b(?:chat with (?:us|me)|message (?:us|me)|add (?:me|us)|reach out (?:to us|to me)?)\s*(?:on|via)?\s*(?:whatsapp|telegram|signal)\b|\b(?:contact|dm) (?:us|me) on (?:whatsapp|telegram|signal)\b"
    if re.search(channel_pattern, text_lower):
        return DetectedIndicator(
            definition=INDICATORS["GEN_CHANNEL_HOPPING"],
            evidence="Prompts moving communication to private messaging platforms"
        )
    return None


# ---------------------------------------------------------------------------
# Master Detector Runner
# ---------------------------------------------------------------------------

def detect_all_indicators(text_normalized: str, original_text: str) -> List[DetectedIndicator]:
    """
    Run all contextual matchers across normalized and original text.
    Returns a deduplicated list of DetectedIndicator objects.
    """
    text_lower = text_normalized.lower()
    matchers = [
        # Bank / Payment
        lambda: detect_bank_credential_harvest(text_lower),
        lambda: detect_bank_urgent_action(text_lower),
        lambda: detect_bank_unauthorized_alert(text_lower),
        lambda: detect_bank_payment_redirect(text_lower),

        # Fake Job
        lambda: detect_job_upfront_payment(text_lower),
        lambda: detect_job_unrealistic_pay(text_lower),
        lambda: detect_job_no_interview_hire(text_lower),
        lambda: detect_job_task_rebate(text_lower),
        lambda: detect_job_off_platform(text_lower),

        # Investment
        lambda: detect_inv_guaranteed_returns(text_lower),
        lambda: detect_inv_urgency_fomo(text_lower),
        lambda: detect_inv_crypto_platform(text_lower),
        lambda: detect_inv_insider_mentor(text_lower),

        # General
        lambda: detect_gen_suspicious_link(text_lower, original_text),
        lambda: detect_gen_anonymous_sender(text_lower),
        lambda: detect_gen_channel_hopping(text_lower),
    ]

    detected: List[DetectedIndicator] = []
    seen_codes = set()

    for matcher in matchers:
        indicator = matcher()
        if indicator and indicator.definition.code not in seen_codes:
            seen_codes.add(indicator.definition.code)
            detected.append(indicator)

    return detected
