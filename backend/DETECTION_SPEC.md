# ScamCheck Technical Detection Specification

**Document Version:** 1.0.0  
**Status:** Approved Specification (Pre-Implementation)  
**Target Components:** Heuristic Baseline Engine & Lightweight ML Classifier  
**Architectural Scope:** Text-Only Detection & Explainable Decision Support

---

## 1. Detection Philosophy & Scope

ScamCheck is a **detection-only decision support tool**. Its sole purpose is to identify known warning signs and patterns in suspicious text messages, explain those indicators in plain language, and recommend protective next steps.

### Core Principles
1. **Decision Support, Not Authority:** The system provides cautious assessments, never definitive verdicts.
2. **No False Certainty:** The system will not declare a message as "100% scam" or "100% safe."
3. **Explainability First:** Every flagged risk level must be directly tied to identifiable textual signals.
4. **Text-Only Processing:** Analysis is conducted purely on message text without live domain crawling, active network requests, sender reputation lookup, or credential inspection.

---

## 2. Supported Scam Categories

ScamCheck focuses on three high-prevalence categories in its MVP:

```
┌────────────────────────────────────────────────────────┐
│               SUPPORTED CATEGORIES                     │
├─────────────────────┬──────────────────┬───────────────┤
│   1. bank_payment   │   2. fake_job    │ 3. investment │
└─────────────────────┴──────────────────┴───────────────┘
```

| Category ID | Name | Core Definition | Typical Delivery Channels |
| :--- | :--- | :--- | :--- |
| `bank_payment` | Bank & Payment Scams | Impersonation of financial institutions, mobile wallets, or payment platforms to induce urgent panic, credential surrender, or money transfers. | SMS (Smishing), WhatsApp, Email |
| `fake_job` | Fake Job Offers | Fraudulent employment propositions offering unrealistic compensation, immediate hiring, task-based pay, or requiring upfront payments for onboarding. | WhatsApp, Telegram, SMS, Email |
| `investment` | Investment Scams | Solicitations promising guaranteed, risk-free, or unusually high financial/crypto returns, often involving unauthorized platforms or trading signals. | Telegram, WhatsApp, Social DMs, SMS |

---

## 3. Indicator Taxonomy & Textual Signals

An **indicator** is a distinct textual pattern or semantic cue commonly associated with fraudulent communications. **No single indicator proves a message is a scam.** Indicators operate as cumulative signals.

### 3.1 Category-Specific Indicators

#### A. Bank & Payment (`bank_payment`)
| Indicator Code | Human-Readable Label | Textual Signal Description | Example Snippets |
| :--- | :--- | :--- | :--- |
| `BANK_URGENT_ACTION` | Urgent account action required | Artificial panic regarding account suspension, unauthorized freeze, or immediate deadline. | *"Your card has been blocked. Verify immediately within 12 hours."* |
| `BANK_CREDENTIAL_HARVEST` | Request for sensitive credentials | Solicitations for passwords, PINs, full card numbers, CVV, OTP codes, or identity documents. | *"Please reply with your one-time passcode to cancel this transfer."* |
| `BANK_UNAUTHORIZED_ALERT` | Fake transaction alert | Fabricated alerts claiming large transfers or debit charges to provoke an impulsive reaction. | *"A charge of $849.99 to Apple Store was approved. If not you, call..."* |
| `BANK_PAYMENT_REDIRECT` | Unusual payment/transfer request | Instructions to transfer funds to a "safe account", via crypto, gift cards, or wire transfer. | *"Transfer your balance to our secure holding account to protect funds."* |

#### B. Fake Job Offers (`fake_job`)
| Indicator Code | Human-Readable Label | Textual Signal Description | Example Snippets |
| :--- | :--- | :--- | :--- |
| `JOB_UNREALISTIC_PAY` | Unrealistic compensation | Disproportionately high hourly or daily pay for unskilled, vague, or minimal part-time work. | *"Earn $300-$800 daily working 30 mins from home on your phone."* |
| `JOB_NO_INTERVIEW_HIRE` | Immediate hiring without screening | Immediate job confirmation or selection with no formal application, CV review, or interview. | *"Congratulations! You have been selected for the Data Assistant role."* |
| `JOB_UPFRONT_PAYMENT` | Upfront fee or equipment charge | Requirement to pay for training materials, onboarding kits, background checks, or software. | *"You must pay a $50 registration and background check fee before start."* |
| `JOB_TASK_REBATE` | Task or review rebate scheme | Solicitations to like videos, subscribe to channels, or rate apps for commission payouts. | *"Like 5 YouTube videos to earn $20 commission. Deposit to level up."* |
| `JOB_OFF_PLATFORM` | Direct to personal chat app | Directing applicant from recruitment platforms to Telegram or WhatsApp for "interviews". | *"Contact our HR manager on Telegram @JobManager24 for your interview."* |

#### C. Investment Scams (`investment`)
| Indicator Code | Human-Readable Label | Textual Signal Description | Example Snippets |
| :--- | :--- | :--- | :--- |
| `INV_GUARANTEED_RETURNS` | Guaranteed high returns | Promises of zero-risk, fixed daily/weekly profits, or guaranteed ROI. | *"100% guaranteed profit of 50% in 48 hours. Zero risk involved."* |
| `INV_URGENCY_FOMO` | High-pressure urgency (FOMO) | Time-limited investment slots, countdowns, or exclusive VIP tier availability. | *"Only 3 spots left in the VIP mining pool! Act now before closing."* |
| `INV_CRYPTO_PLATFORM` | Unregulated crypto/trading platform | Solicitations to deposit cryptocurrency into unfamiliar, unverified trading bots or platforms. | *"Deposit 0.1 BTC to our automated AI arbitrage bot to start trading."* |
| `INV_INSIDER_MENTOR` | Financial guru or insider signals | Unsolicited claims of private trading groups, insider signals, or personal wealth mentorship. | *"Our professional crypto analyst will manage your portfolio with 99% accuracy."* |

### 3.2 Cross-Cutting General Indicators
| Indicator Code | Human-Readable Label | Textual Signal Description |
| :--- | :--- | :--- |
| `GEN_SUSPICIOUS_LINK` | Call to click an unverified link | Vague or urgent directives to click shortened or obfuscated links (*"Click here to update"*). |
| `GEN_ANONYMOUS_SENDER` | Generic or impersonal greeting | Generic openers like *"Dear Customer"*, *"Attention User"*, or *"Hello Dear"*. |
| `GEN_CHANNEL_HOPPING` | Request to move to private channel | Unprompted requests to move conversations to Telegram, Signal, or WhatsApp. |

---

## 4. Legitimate Comparison Cases (False Positive Scenarios)

To avoid naive keyword matching, the detection engine must recognize legitimate communication patterns that share surface similarities with scam texts.

```
┌───────────────────────────┬──────────────────────────────────────────────────────────────┐
│ Category                  │ Legitimate Pattern (Baseline) vs Scam Characteristic         │
├───────────────────────────┼──────────────────────────────────────────────────────────────┤
│ Bank 2FA Authentication   │ Legitimate: "Your code is 492011. ScamCheck will NEVER ask    │
│                           │ for this code. Do not share."                                │
│                           │ Scam: "Reply with the OTP you just received to verify."      │
├───────────────────────────┼──────────────────────────────────────────────────────────────┤
│ Bank Fraud Inquiry        │ Legitimate: "Did you attempt a $25 charge at Target?         │
│                           │ Reply YES or NO. We will not ask for your password."         │
│                           │ Scam: "Suspicious charge! Click [link] and login to stop it."│
├───────────────────────────┼──────────────────────────────────────────────────────────────┤
│ Job Recruiter Outreach    │ Legitimate: "Hi Alex, saw your React profile. Opening at XYZ.│
│                           │ Apply via company.com/careers."                              │
│                           │ Scam: "You are hired! Earn $500/day. Message on WhatsApp."   │
├───────────────────────────┼──────────────────────────────────────────────────────────────┤
│ Financial / Market News   │ Legitimate: "Past market performance is no guarantee of      │
│                           │ future results. Read fund prospectus."                       │
│                           │ Scam: "Guaranteed 10x returns on this new coin in 24 hours." │
└───────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 5. Risk Assessment & Output States

ScamCheck uses **three explainable risk tiers**. These tiers reflect **indicator convergence**, not uncalibrated statistical probabilities.

```
                  ┌────────────────────────────────────────┐
                  │          OUTPUT RISK STATES            │
                  └───────────────────┬────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
   ┌───────────┐            ┌───────────────────┐            ┌───────────┐
   │    low    │            │needs_verification │            │   high    │
   └───────────┘            └───────────────────┘            └───────────┘
```

### Risk Tier Definitions

| State (`risk_level`) | Display Badge (`risk_label`) | Definition & Trigger Criteria |
| :--- | :--- | :--- |
| `low` | `No obvious warning signs detected` | Message contains no detectable indicators from the taxonomy. Cautious disclaimer reinforces that stealthy attacks can still exist. |
| `needs_verification` | `Needs further verification` | Message contains 1–2 isolated or weak indicators (e.g., general urgency, recruiter asking for communication on another channel). |
| `high` | `Multiple warning signs detected` | Message contains 2 or more strong, converging indicators (e.g., unrealistic salary + upfront fee + Telegram redirect). |

---

## 6. Data Representation & Contracts

### 6.1 Indicator Representation
The system uses human-readable string descriptions for presentation in the frontend `indicators` list, derived from standardized taxonomy codes internally.

```json
"indicators": [
  "Urgent request for account action or payment",
  "Solicitation of sensitive credentials or one-time codes"
]
```

### 6.2 Category Representation
The `category` field indicates the primary identified scam domain:
- `"bank_payment"`: Bank and payment impersonation
- `"fake_job"`: Fraudulent employment or task scam
- `"investment"`: Investment, crypto, or high-yield fraud
- `null`: No distinct category detected (e.g., clean message, unclassified, or generic spam)

*Multi-category handling:* When a message contains signals from multiple domains (e.g., job offer requiring crypto investment), the primary dominant domain is assigned to `category`, and indicators from both categories are included in the `indicators` array.

---

## 7. Explanation Strategy

Explanations must be **cautious, specific, and non-accusatory**.

### Formula for Explanation Generation:
1. **Acknowledge the Assessment:** State what patterns were observed.
2. **Contextualize the Risk:** Explain why this combination of patterns is commonly associated with fraud.
3. **State the Boundary:** Reiterate that this is decision support, not legal/forensic proof.

### Examples:
- **For `high` (Bank):**  
  *"This message was flagged because it combines urgent threats of account suspension with a request to verify sensitive details. Financial institutions typically do not request sensitive credentials or direct transfers through unsolicited messages. This assessment is not proof of fraud, but extreme caution is advised."*
- **For `low`:**  
  *"No obvious warning signs or known scam indicators were detected in this text. However, sophisticated scams or targeted communications may not match standard keyword patterns. Always verify unfamiliar contacts independently."*

---

## 8. Safety Guidance Library

Actionable, protective steps are dynamically paired with the detected category and risk level.

```
┌───────────────────┬──────────────────────────────────────────────────────────────┐
│ Category Context  │ Prescribed Safety Guidance Items                             │
├───────────────────┼──────────────────────────────────────────────────────────────┤
│ `bank_payment`    │ • Contact your bank directly using the official phone number │
│                   │   on the back of your card or official mobile app.           │
│                   │ • Never share one-time passcodes (OTPs), PINs, or passwords. │
│                   │ • Do not click links in unexpected text messages or emails.  │
├───────────────────┼──────────────────────────────────────────────────────────────┤
│ `fake_job`        │ • Verify job postings directly on the company's careers site.│
│                   │ • Legitimate employers never charge upfront fees for work.   │
│                   │ • Avoid conducting formal hiring solely via chat apps.       │
├───────────────────┼──────────────────────────────────────────────────────────────┤
│ `investment`      │ • Remember that guaranteed high returns with zero risk do    │
│                   │   not exist in legitimate financial markets.                 │
│                   │ • Check official financial regulatory registries before funds│
│                   │   transfers.                                                 │
│                   │ • Never transfer cryptocurrency to unverified private wallets│
├───────────────────┼──────────────────────────────────────────────────────────────┤
│ General / Low     │ • When in doubt, verify through an independent channel.      │
│                   │ • Do not forward suspicious messages to others.              │
└───────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 9. False-Positive Analysis & Mitigations

| Scam Signal | Potential False-Positive Source | Mitigation Heuristic |
| :--- | :--- | :--- |
| Urgency terms (*"immediate"*, *"now"*) | Delivery alerts, calendar reminders, limited-time retail sales. | Require co-occurrence with financial, credential, or account-lockout signals. |
| Money mentions (*"$500"*, *"transfer"*) | Person-to-person split bills, utility bills, freelance invoicing. | Require co-occurrence with pressure, unverified platforms, or credential requests. |
| Job discussions (*"hiring"*, *"salary"*) | Genuine recruiter outreach on LinkedIn, networking messages. | Distinguish vague high-yield task phrasing from standard corporate job descriptions. |

---

## 10. Technical Limitations (Explicit Exclusions)

The text-only detection engine has the following boundaries:
1. **No URL Destination Resolution:** The detector does not expand shortened URLs, follow redirects, or inspect destination web content.
2. **No Sender Verification:** The detector cannot verify sender phone numbers, email headers, or detect caller ID/SMS spoofing.
3. **No File/Attachment Inspection:** PDF, image, or document attachments are not processed.
4. **No Conversational History:** The detector evaluates single message snippets without prior multi-turn context.
5. **Adversarial Obfuscation:** Deliberate leetspeak, zero-width characters, or homoglyphs may evade simple lexical rules.

---

## 11. API Contract Compatibility Assessment

The current API contract established in `backend/app/schemas.py`:

```json
{
  "risk_level": "needs_verification",
  "risk_label": "Needs further verification",
  "summary": "...",
  "category": "bank_payment",
  "explanation": "...",
  "indicators": ["..."],
  "safety_guidance": ["..."]
}
```

### Evaluation:
- **No breaking changes required:** The established schema completely satisfies this specification.
- **`indicators` & `safety_guidance`:** Maintained as `List[str]` for clean, zero-friction rendering in the React frontend.
- **`category`:** Accepts `Optional[str]` (`"bank_payment"`, `"fake_job"`, `"investment"`, `null`).
- **`risk_level`:** Supports `"low"`, `"needs_verification"`, `"high"`.
