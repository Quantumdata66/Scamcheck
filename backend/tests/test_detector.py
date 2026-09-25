"""
Comprehensive test suite for the RulesBaselineDetector engine.
Tests indicator detection, category classification, risk assessments,
legitimate false-positive mitigations, and edge cases.
"""

import pytest
from app.services.detector import RulesBaselineDetector


@pytest.fixture
def detector():
    return RulesBaselineDetector()


# ---------------------------------------------------------------------------
# 1. Bank & Payment Scams
# ---------------------------------------------------------------------------

def test_bank_urgent_and_credential_harvest(detector):
    """Urgent threat + credential request should flag as high-risk bank_payment."""
    msg = "URGENT: Your bank account has been suspended due to unauthorized activity. Reply with your OTP code immediately within 24 hours to restore access."
    result = detector.analyze(msg)
    assert result.risk_level == "high"
    assert result.category == "bank_payment"
    assert "Urgent request for account action" in result.indicators
    assert "Request for sensitive credentials or security codes" in result.indicators
    assert len(result.safety_guidance) > 0


def test_bank_payment_redirect_safe_account(detector):
    """Directing user to move funds to a safe account should flag bank_payment."""
    msg = "Security Alert: Your funds are at risk. Please transfer your balance to our safe account immediately."
    result = detector.analyze(msg)
    assert result.category == "bank_payment"
    assert result.risk_level in ["needs_verification", "high"]
    assert "Request to transfer funds to unusual or safe account" in result.indicators


def test_bank_unauthorized_transaction_alert(detector):
    """Panic debit alert prompting urgent dispute should flag bank_payment."""
    msg = "Fraud Alert: A transaction of $749.00 was approved on your card. If this was not you, call us immediately to cancel."
    result = detector.analyze(msg)
    assert result.category == "bank_payment"
    assert "Unverified transaction or security alert" in result.indicators


def test_legitimate_bank_2fa_alert(detector):
    """Standard 2FA notification with 'do not share' security notice should be low risk."""
    msg = "Your Chase verification code is 849201. We will NEVER ask for this code. Do not share it with anyone."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert "Request for sensitive credentials or security codes" not in result.indicators


def test_legitimate_bank_receipt(detector):
    """Standard payment receipt without threats should be low risk."""
    msg = "Your payment of $45.00 to City Water Utility was processed successfully on March 15. Thank you for your payment."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert result.category is None


# ---------------------------------------------------------------------------
# 2. Fake Job Offers
# ---------------------------------------------------------------------------

def test_fake_job_unrealistic_pay_and_no_interview(detector):
    """Unrealistic daily wage + immediate hire claim should flag fake_job."""
    msg = "Congratulations! You have been selected for our online assistant role. Earn $500/day working from home on your phone. No experience needed."
    result = detector.analyze(msg)
    assert result.risk_level == "high"
    assert result.category == "fake_job"
    assert "Unrealistic compensation for minimal tasks" in result.indicators
    assert "Immediate hiring claim without formal interview" in result.indicators


def test_fake_job_upfront_fee(detector):
    """Requiring upfront payment for onboarding kit should flag fake_job."""
    msg = "Welcome to the team! You must pay an upfront equipment fee of $75 to receive your training kit before starting."
    result = detector.analyze(msg)
    assert result.category == "fake_job"
    assert "Demand for upfront onboarding or equipment fee" in result.indicators


def test_fake_job_task_rebate(detector):
    """Task-based commission for liking videos should flag fake_job."""
    msg = "Earn daily income! Like YouTube videos for commission. Deposit funds to unlock the next level of tasks."
    result = detector.analyze(msg)
    assert result.category == "fake_job"
    assert "Task-based commission or review rebate scheme" in result.indicators


def test_legitimate_job_posting(detector):
    """Professional corporate job advertisement with salary should be low risk."""
    msg = "Stripe is hiring a Senior Frontend Engineer ($150k-$180k/year). 5+ years React experience required. Apply at stripe.com/careers."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert "Unrealistic compensation for minimal tasks" not in result.indicators


def test_legitimate_recruiter_outreach(detector):
    """Normal recruiter message on LinkedIn or email should be low risk."""
    msg = "Hi Alex, I came across your GitHub profile and was impressed by your open source work. Would you be open for a brief intro call next week?"
    result = detector.analyze(msg)
    assert result.risk_level == "low"


# ---------------------------------------------------------------------------
# 3. Investment Scams
# ---------------------------------------------------------------------------

def test_investment_guaranteed_returns(detector):
    """Guaranteed 100% profit promise should flag investment scam."""
    msg = "Join our crypto platform and enjoy 100% guaranteed profit of 50% weekly with zero risk investment."
    result = detector.analyze(msg)
    assert result.risk_level == "high"
    assert result.category == "investment"
    assert "Guaranteed or risk-free return claims" in result.indicators


def test_investment_fomo_urgency(detector):
    """Limited spot FOMO pressure should flag investment."""
    msg = "Exclusive investment opportunity! Only 3 spots left in the VIP pool closing in 2 hours. Don't miss this."
    result = detector.analyze(msg)
    assert result.category == "investment"
    assert "High-pressure investment urgency (FOMO)" in result.indicators


def test_investment_crypto_bot(detector):
    """Automated crypto trading bot / liquidity pool deposit solicitation."""
    msg = "Deposit USDT into our automated AI crypto trading bot to generate passive daily income."
    result = detector.analyze(msg)
    assert result.category == "investment"
    assert "Unverified crypto deposit or trading bot promotion" in result.indicators


def test_legitimate_financial_disclaimer(detector):
    """Legitimate market commentary containing standard disclaimers should be low risk."""
    msg = "Vanguard Index Fund Quarterly Update: Past performance is no guarantee of future results. Read fund prospectus carefully before investing."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert "Guaranteed or risk-free return claims" not in result.indicators


def test_legitimate_401k_notification(detector):
    """Standard employer retirement contribution message should be low risk."""
    msg = "Your monthly 401(k) retirement investment contribution of $200 has been credited to your portfolio account."
    result = detector.analyze(msg)
    assert result.risk_level == "low"


# ---------------------------------------------------------------------------
# 4. Cross-Cutting Signals & Weak Context
# ---------------------------------------------------------------------------

def test_suspicious_link_prompt(detector):
    """Urgent directive to click a link should be flagged."""
    msg = "Action required: click the link below immediately to verify your identity: https://verify-login.net"
    result = detector.analyze(msg)
    assert "Call to click an unverified link urgently" in result.indicators
    assert result.risk_level in ["needs_verification", "high"]


def test_generic_greeting_alone_is_low_risk(detector):
    """An isolated generic greeting without other indicators should remain low risk."""
    msg = "Dear Customer, thank you for shopping with us today. Have a wonderful weekend."
    result = detector.analyze(msg)
    assert result.risk_level == "low"


def test_benign_whatsapp_mention_is_low_risk(detector):
    """A normal message mentioning WhatsApp support without pressure should be low risk."""
    msg = "Hi Mom, I sent the family photos on WhatsApp. Let me know if you received them."
    result = detector.analyze(msg)
    assert result.risk_level == "low"


# ---------------------------------------------------------------------------
# 5. Edge Cases & Robustness
# ---------------------------------------------------------------------------

def test_mixed_categories_selects_dominant(detector):
    """When both fake job and crypto investment cues appear, dominant category is selected."""
    msg = "Congratulations! You have been selected for our remote data role ($400/day). You will be trained by our crypto guru on WhatsApp."
    result = detector.analyze(msg)
    assert result.risk_level in ["needs_verification", "high"]
    assert result.category in ["fake_job", "investment"]
    assert len(result.indicators) >= 2


def test_unusual_casing_and_whitespace(detector):
    """Mixed capitalization and whitespace should be normalized seamlessly."""
    msg = "   uRgEnT:  yOuR  bAnK  aCcOuNt   iS  lOcKeD!   RePlY  wItH   yOuR   OtP   nOw!   "
    result = detector.analyze(msg)
    assert result.risk_level == "high"
    assert result.category == "bank_payment"


def test_completely_clean_text(detector):
    """Ordinary conversation text returns clean low-risk response."""
    msg = "Hey Dave, are we still meeting for lunch at 1pm at the cafe?"
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert result.risk_label == "No obvious warning signs detected"
    assert result.category is None
    assert result.indicators == []
    assert len(result.safety_guidance) > 0
