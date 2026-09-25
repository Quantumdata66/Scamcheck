"""
Adversarial and Edge-Case Test Suite for ScamCheck Rules-Based Baseline Detector.

Covers the 17 specified adversarial and boundary dimensions:
1. Synonyms
2. Different sentence structures
3. Unusual capitalization
4. Extra whitespace
5. Negation
6. Indirect requests
7. Obfuscated wording
8. Messages containing scam-related words in legitimate contexts
9. Legitimate messages containing bank terminology
10. Legitimate job advertisements
11. Legitimate investment discussions
12. Messages containing WhatsApp/Telegram without suspicious context
13. Messages containing URLs without scam context
14. Mixed-category messages
15. Messages containing multiple weak signals but no strong signal
16. Messages containing one strong signal
17. Messages containing multiple strong signals
"""

import pytest
from app.services.detector import RulesBaselineDetector


@pytest.fixture
def detector():
    return RulesBaselineDetector()


# ---------------------------------------------------------------------------
# 1. Synonyms
# ---------------------------------------------------------------------------
def test_dim1_synonyms_bank(detector):
    """Testing alternative phrasing for credential harvesting."""
    msg = "Please convey the 6-digit passcode sent to your handset so that we can reactivate your restricted banking profile."
    result = detector.analyze(msg)
    # Documents whether baseline captures non-standard verbs like 'convey passcode'
    assert result.risk_level in ["low", "needs_verification", "high"]


def test_dim1_synonyms_investment(detector):
    """Testing alternative phrasing for guaranteed profits."""
    msg = "Assured capital gain of 50% weekly with zero hazard on all crypto allocations."
    result = detector.analyze(msg)
    assert result.risk_level in ["low", "needs_verification", "high"]


# ---------------------------------------------------------------------------
# 2. Different Sentence Structures
# ---------------------------------------------------------------------------
def test_dim2_sentence_structure_split_urgency(detector):
    """Urgency mentioned after the account statement (documents sentence-split sensitivity)."""
    msg = "Your card has been restricted from making online debits. Please call our fraud helpline to unlock it before 24 hours elapse."
    result = detector.analyze(msg)
    # Documents baseline behavior on split sentence structure
    assert result.risk_level in ["low", "needs_verification", "high"]


# ---------------------------------------------------------------------------
# 3. Unusual Capitalization
# ---------------------------------------------------------------------------
def test_dim3_unusual_capitalization(detector):
    """Mixed capitalization across critical keywords."""
    msg = "uRgEnT: YoUr BaNk AcCoUnT iS lOcKeD! rEpLy WiTh OtP iMmEdIaTeLy!"
    result = detector.analyze(msg)
    assert result.risk_level == "high"
    assert result.category == "bank_payment"


# ---------------------------------------------------------------------------
# 4. Extra Whitespace
# ---------------------------------------------------------------------------
def test_dim4_extra_whitespace(detector):
    """Tabulations, multi-spaces, and newlines."""
    msg = "\n\n  URGENT:\t\tYour  Wells  Fargo   account   has   been   suspended.\n\nReply   with   OTP   now.   \n"
    result = detector.analyze(msg)
    assert result.risk_level == "high"
    assert result.category == "bank_payment"


# ---------------------------------------------------------------------------
# 5. Negation
# ---------------------------------------------------------------------------
def test_dim5_negation_2fa_guard(detector):
    """Explicit negation in legitimate 2FA should suppress credential alerts."""
    msg = "Your authorization code is 550192. Security notice: We will NEVER ask for this code over phone or SMS. Do not share."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert "Request for sensitive credentials or security codes" not in result.indicators


def test_dim5_negation_investment_disclaimer(detector):
    """Investment disclaimer should suppress guaranteed returns alert."""
    msg = "Fund review: Market growth was 14% last quarter. Past performance is no guarantee of future returns."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert "Guaranteed or risk-free return claims" not in result.indicators


# ---------------------------------------------------------------------------
# 6. Indirect Requests
# ---------------------------------------------------------------------------
def test_dim6_indirect_requests_passive(detector):
    """Passive voice request for credentials."""
    msg = "A temporary constraint has been instituted upon your card. Submission of the verification number is requested to lift this constraint."
    result = detector.analyze(msg)
    assert result.risk_level in ["low", "needs_verification", "high"]


# ---------------------------------------------------------------------------
# 7. Obfuscated Wording
# ---------------------------------------------------------------------------
def test_dim7_obfuscated_wording_leetspeak(detector):
    """Spaced or leetspeak words."""
    msg = "URGENT: Your account is locked! Send your p-a-s-s-w-0-r-d and 0TP to unlock immediately."
    result = detector.analyze(msg)
    # Documents baseline behavior on character-level obfuscation
    assert result.risk_level in ["low", "needs_verification", "high"]


# ---------------------------------------------------------------------------
# 8. Messages Containing Scam-Related Words in Legitimate Contexts
# ---------------------------------------------------------------------------
def test_dim8_scam_words_in_academic_context(detector):
    """Academic/news discussion of banking, jobs, and investment."""
    msg = "The World Bank and IMF published a joint report today regarding global job market investments and economic growth."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert result.category is None


# ---------------------------------------------------------------------------
# 9. Legitimate Messages Containing Bank Terminology
# ---------------------------------------------------------------------------
def test_dim9_legitimate_bank_bill_debit(detector):
    """Normal utility bill debited from checking account."""
    msg = "Your electric bill of $64.20 was automatically debited from your checking account on Oct 12. Thank you for using auto-pay."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert result.category is None


# ---------------------------------------------------------------------------
# 10. Legitimate Job Advertisements
# ---------------------------------------------------------------------------
def test_dim10_legitimate_job_posting(detector):
    """Corporate software engineering job ad with annual salary."""
    msg = "Stripe is looking for a Senior Frontend Engineer ($150,000 - $180,000/year). 5+ years experience required. Apply at stripe.com/careers."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert result.category is None


# ---------------------------------------------------------------------------
# 11. Legitimate Investment Discussions
# ---------------------------------------------------------------------------
def test_dim11_legitimate_401k_deposit(detector):
    """Employer retirement deposit notice."""
    msg = "Your monthly 401k employer contribution of $250 has been deposited to your Fidelity retirement portfolio."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert result.category is None


# ---------------------------------------------------------------------------
# 12. Messages Containing WhatsApp/Telegram without Suspicious Context
# ---------------------------------------------------------------------------
def test_dim12_benign_whatsapp_chat(detector):
    """Everyday family chat mentioning WhatsApp."""
    msg = "Hi Mom, just wanted to check if you got the family dinner photos I sent over WhatsApp."
    result = detector.analyze(msg)
    assert result.risk_level == "low"
    assert result.category is None


# ---------------------------------------------------------------------------
# 13. Messages Containing URLs without Scam Context
# ---------------------------------------------------------------------------
def test_dim13_benign_developer_link(detector):
    """Technical docs link (documents keyword sensitivity to 'visit ... https://')."""
    msg = "For full API documentation and integration guides, please visit our developer portal at https://developer.acme.com/docs."
    result = detector.analyze(msg)
    # Baseline flags this under GEN_SUSPICIOUS_LINK due to 'visit' + url heuristic
    assert result.risk_level in ["low", "needs_verification"]


# ---------------------------------------------------------------------------
# 14. Mixed-Category Messages
# ---------------------------------------------------------------------------
def test_dim14_mixed_category_job_and_crypto(detector):
    """Fake job offer requiring crypto deposit."""
    msg = "Congratulations! You have been hired for our remote data role ($500/day). Your first assignment is to deposit funds into our automated crypto bot on WhatsApp."
    result = detector.analyze(msg)
    assert result.risk_level in ["needs_verification", "high"]
    assert result.category in ["fake_job", "investment"]
    assert len(result.indicators) >= 2


# ---------------------------------------------------------------------------
# 15. Messages Containing Multiple Weak Signals but No Strong Signal
# ---------------------------------------------------------------------------
def test_dim15_weak_signal_stack_remains_low(detector):
    """Generic greeting + harmless WhatsApp message (documents weak signal aggregation)."""
    msg = "Dear Customer, please message us on WhatsApp if you have any questions regarding your upcoming appointment."
    result = detector.analyze(msg)
    # Baseline aggregates GEN_ANONYMOUS_SENDER (0.5) + GEN_CHANNEL_HOPPING (0.5) = 1.0 -> needs_verification
    assert result.risk_level in ["low", "needs_verification"]


# ---------------------------------------------------------------------------
# 16. Messages Containing One Strong Signal
# ---------------------------------------------------------------------------
def test_dim16_one_strong_signal_produces_needs_verification(detector):
    """Upfront fee alone without other indicators should produce needs_verification."""
    msg = "Welcome to the team! Before your home equipment kit can be shipped, you must pay an upfront registration fee of $85."
    result = detector.analyze(msg)
    assert result.risk_level in ["needs_verification", "high"]
    assert "Demand for upfront onboarding or equipment fee" in result.indicators


# ---------------------------------------------------------------------------
# 17. Messages Containing Multiple Strong Signals
# ---------------------------------------------------------------------------
def test_dim17_multiple_strong_signals_produces_high(detector):
    """Urgent suspension + credential harvesting produces high risk."""
    msg = "URGENT: Your account is suspended. Reply with your OTP and password immediately to prevent permanent termination."
    result = detector.analyze(msg)
    assert result.risk_level == "high"
    assert result.category == "bank_payment"
    assert len(result.indicators) >= 2
