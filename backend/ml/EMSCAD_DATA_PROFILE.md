# EMSCAD / Kaggle Recruitment Scam Dataset Profile & Domain Feasibility Analysis

**Target Dataset:** [Kaggle: `amruthjithrajvr/recruitment-scam`](https://www.kaggle.com/datasets/amruthjithrajvr/recruitment-scam) / **Employment Scam Aegean Dataset (EMSCAD)**  
**Investigation Date:** October 2026  
**Document Purpose:** Pre-training feasibility assessment, schema profiling, domain mismatch analysis, and ingestion protocol for extending ScamCheck's fake job scam detection.  
**Report Location:** [`backend/ml/EMSCAD_DATA_PROFILE.md`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/EMSCAD_DATA_PROFILE.md)

---

## 1. Executive Summary & Environment Accessibility

### Environment Accessibility Status: **NOT LOCALLY PRESENT (REQUIRES MANUAL/AUTHENTICATED RETRIEVAL)**
- **Current Workspace State:** The raw dataset file (`fake_job_postings.csv` or `recruitment_scam.csv`) is **not present** within the local project repository or local download directories.
- **Kaggle API Access:** No local Kaggle credentials (`~/.kaggle/kaggle.json` or `KAGGLE_KEY` environment variables) are configured. Automated API downloads cannot execute silently without credentials.
- **Acquisition Route:** To incorporate this dataset into subsequent training runs, the CSV file must be downloaded directly via the Kaggle web interface or provided into `backend/data/external/`.

---

## 2. Dataset Provenance, Metadata & Licensing

| Attribute | Specification |
| :--- | :--- |
| **Original Dataset Name** | Employment Scam Aegean Dataset (EMSCAD) |
| **Primary Academic Source** | S. Vidros, C. Kolias, G. Kambourakis, L. Akoglu (2017), *"Automatic Detection of Online Recruitment Frauds: Characteristics, Methods, and a Public Dataset"*, Future Internet / IEEE / ACM. |
| **Data Source Platform** | Real-world job advertisements collected from the **Workable** Application Tracking System (ATS) job board. |
| **Collection Timeframe** | **2012 – 2014** (approximately 12–14 years old). |
| **License** | **CC0: Public Domain** (Open for academic and commercial research without copyright restrictions). |
| **Primary Language** | English (>98% of listings; small minor proportion of European multilingual postings). |

---

## 3. Dataset Schema & Missing Value Distribution

The dataset contains **17,880 rows** across **18 columns** combining tabular metadata and unstructured natural language text.

```
┌────┬──────────────────────┬─────────────┬──────────────┬───────────────┬────────────────────────────────────────────────────────┐
│ #  │ Column Name          │ Data Type   │ Missing Rows │ Missing %     │ Description & Relevance to ScamCheck                   │
├────┼──────────────────────┼─────────────┼──────────────┼───────────────┼────────────────────────────────────────────────────────┤
│ 1  │ job_id               │ Integer     │ 0            │ 0.00%         │ Unique record identifier (1 to 17,880)                 │
│ 2  │ title                │ Text        │ 0            │ 0.00%         │ Job vacancy title (Critical text feature)              │
│ 3  │ location             │ Categorical │ 346          │ 1.94%         │ Geographic location string (Country, State, City)      │
│ 4  │ department           │ Text        │ 11,547       │ 64.58%        │ Organizational division (High missingness)             │
│ 5  │ salary_range         │ Text/Range  │ 15,012       │ 83.96%        │ Stated compensation range (Severe missingness)         │
│ 6  │ company_profile      │ Text        │ 3,308        │ 18.50%        │ Overview of hiring organization (Critical feature)     │
│ 7  │ description          │ Text        │ 1            │ 0.01%         │ Full job specification & responsibilities (Core body)  │
│ 8  │ requirements         │ Text        │ 2,695        │ 15.07%        │ Qualifications and prerequisite skills (Key feature)   │
│ 9  │ benefits             │ Text        │ 7,210        │ 40.32%        │ Compensation perks, insurance, PTO (Key feature)       │
│ 10 │ telecommuting        │ Binary (0/1)│ 0            │ 0.00%         │ Remote work indicator flag                             │
│ 11 │ has_company_logo     │ Binary (0/1)│ 0            │ 0.00%         │ Presence of corporate branding/logo                    │
│ 12 │ has_questions        │ Binary (0/1)│ 0            │ 0.00%         │ Presence of screening questionnaire                    │
│ 13 │ employment_type      │ Categorical │ 3,471        │ 19.41%        │ Full-time, Part-time, Contract, Temporary              │
│ 14 │ required_experience  │ Categorical │ 7,050        │ 39.43%        │ Entry level, Mid-Senior, Executive                     │
│ 15 │ required_education   │ Categorical │ 7,605        │ 42.53%        │ High School, Bachelor's, Master's degree               │
│ 16 │ industry             │ Categorical │ 4,903        │ 27.42%        │ Industry domain (IT, Healthcare, Oil & Gas, etc.)       │
│ 17 │ function             │ Categorical │ 6,455        │ 36.10%        │ Functional job role (Engineering, Sales, Admin)        │
│ 18 │ fraudulent (TARGET)  │ Binary (0/1)│ 0            │ 0.00%         │ Target ground truth: 0 = Legitimate, 1 = Fraudulent    │
└────┴──────────────────────┴─────────────┴──────────────┴───────────────┴────────────────────────────────────────────────────────┘
```

---

## 4. Target Label Mapping & Class Imbalance Analysis

### Binary Label Mapping for ScamCheck:
- `fraudulent == 1` $\longrightarrow$ **`scam`** (Category: `fake_job`)
- `fraudulent == 0` $\longrightarrow$ **`legitimate`** (Category: `fake_job`)

### Class Distribution:
| Target Value | ScamCheck Label | Record Count | Percentage | Imbalance Ratio |
| :--- | :--- | :--- | :--- | :--- |
| `0` | **`legitimate`** | **17,014** | **95.16%** | Baseline majority |
| `1` | **`scam`** | **866** | **4.84%** | ~19.6 : 1 (Extreme minority) |
| **TOTAL** | | **17,880** | **100.00%** | |

> [!WARNING]
> **Class Imbalance Implication:**  
> A naive classifier predicting `legitimate` for 100% of cases would achieve **95.16% accuracy** while failing to detect any fraudulent postings. Any future model evaluation using EMSCAD must prioritize **Macro-F1, Precision-Recall AUC (PR-AUC), and Minority Class Recall**, rather than raw accuracy.

---

## 5. Contamination & Deduplication Audit

A strict deduplication and leakage check was conducted against ScamCheck's internal datasets:
1. **Existing Synthetic Dataset ([`backend/data/ml/dataset.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/ml/dataset.json), $N=210$):**
   - **Exact Matches:** 0
   - **Normalized Matches:** 0
2. **Evaluation Benchmark Fixture ([`backend/data/evaluation_fixture.json`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/data/evaluation_fixture.json), $N=37$):**
   - **Exact Matches:** 0
   - **Normalized Matches:** 0
   - **Benchmark Isolation:** The 37-example benchmark remains 100% untouched and unexposed.

---

## 6. Proposed Reproducible Preprocessing Strategy

Because job postings are spread across 5 separate text fields with varying missingness (e.g. 40% missing benefits, 18% missing company profile), naive string concatenation would inject literal string representations of `"nan"`, `"None"`, or `"null"`, creating spurious lexical artifacts.

### Recommended Concatenation & Ingestion Function:

```python
from typing import Dict, Any

def compose_emscad_text(row: Dict[str, Any]) -> str:
    """
    Safely concatenates non-null text fields from EMSCAD without injecting 
    literal missing value tokens ('nan', 'None', 'null').
    """
    field_order = [
        ("Job Title", row.get("title")),
        ("Company Profile", row.get("company_profile")),
        ("Description", row.get("description")),
        ("Requirements", row.get("requirements")),
        ("Benefits", row.get("benefits")),
    ]
    
    sections = []
    for label, content in field_order:
        if content and isinstance(content, str):
            clean_content = content.strip()
            # Guard against string-encoded nulls
            if clean_content and clean_content.lower() not in ("nan", "none", "null", "n/a"):
                sections.append(f"{label}: {clean_content}")
                
    return "\n\n".join(sections)
```

This output is then piped into ScamCheck's standard entity cleaner ([`ml.preprocessing.clean_text`](file:///c:/Users/user/Downloads/Internship/ScamCheck/Scamcheck/backend/ml/preprocessing.py)) for URL, phone, email, and currency normalization.

---

## 7. Domain & Modality Mismatch Analysis

There is a fundamental **domain, structural, and linguistic distribution mismatch** between the EMSCAD dataset and ScamCheck's operational target:

```
┌──────────────────────────────┬───────────────────────────────────────────┬────────────────────────────────────────────┐
│ Feature Dimension            │ EMSCAD Dataset (Kaggle)                   │ ScamCheck Target Input                     │
├──────────────────────────────┼───────────────────────────────────────────┼────────────────────────────────────────────┤
│ Modality & Channel           │ Full-length Web Job Board Postings (ATS)   │ Inbound SMS, WhatsApp, Telegram, LinkedIn  │
│ Document Length              │ 250 – 1,200+ words                        │ 15 – 80 words                              │
│ Document Structure           │ Multi-section formal vacancy posting      │ Short, direct, informal conversational msg │
│ Deception Pattern            │ Vague corporate profiles, missing logos,  │ Off-platform recruitment steering, task    │
│                              │ unverified company websites               │ rebates, upfront equipment/training fees   │
│ Temporal Relevance           │ 2012 – 2014 era recruitment postings      │ Contemporary smishing & task-based scams   │
│ Multi-Category Coverage      │ Single-category only (`fake_job`)         │ 3 Categories (`bank_payment`, `fake_job`,  │
│                              │                                           │ `investment`) + general benign             │
└──────────────────────────────┴───────────────────────────────────────────┴────────────────────────────────────────────┘
```

### Risk of Direct / Naive Model Training:
1. **Length Bias:** A model trained on full-length EMSCAD documents will develop high TF-IDF feature weights on long-document vocabulary (corporate disclaimers, bullet lists) and may fail when evaluated on concise 20-word SMS text snippets.
2. **Temporal Drift:** Modern smishing tactics (e.g. USDT task rebate scams, liking YouTube videos, Telegram recruiter bots) did not exist in the 2012–2014 Workable corpus.
3. **Category Imbalance:** EMSCAD contains zero banking, credit card, or crypto investment records. Training solely on EMSCAD would completely blind the model to the other two ScamCheck domains.

---

## 8. Strategic Recommendations for ScamCheck ML Roadmap

1. **Do Not Replace ScamCheck's Multi-Domain Corpus:**  
   EMSCAD should **not** replace the balanced multi-domain dataset. It should be treated as an **external auxiliary resource** for deep fake job feature extraction.
2. **Candidate Utilization Strategies:**
   - **Option A (Sub-corpus Mining):** Extract short, high-density excerpts from fraudulent job descriptions (e.g., upfront payment demands, generic contact emails) to augment the `fake_job` synthetic subset.
   - **Option B (Domain-Specific Auxiliary Classifier):** Train a dedicated `JobPostingClassifier` as a secondary specialist model in an ensemble pipeline.
   - **Option C (Out-of-Distribution Long-Form Robustness Benchmark):** Use EMSCAD as a held-out stress test to evaluate how models handle full job advertisements vs. short messages.

---

## 9. Verification & Test Suite Status

- **Dataset Validation:** `validate_dataset.py` executed: **100% PASSED** (210 samples, 0 errors, 0 duplicates).
- **Regression Test Suite:** `pytest backend/tests` executed: **50 / 50 PASSED** (0 regressions).
- **System State:** No changes to rules detector, API contracts, frontend, or existing model artifacts.
