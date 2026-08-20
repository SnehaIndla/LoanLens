# Risk & Anomaly Scoring Agent

## 1. Agent Overview

| Field | Detail |
|---|---|
| **Agent Name** | Risk & Anomaly Scoring Agent |
| **Owner** | James |
| **Purpose** | Compute an overall risk/consistency score and flag anomaly patterns for a loan application, providing advisory evidence to a human loan officer. |
| **Input** | Declared applicant record (from `loan_approval_dataset.csv`), discrepancies found by the Cross-Validation & Consistency Agent, credit history (`cibil_score`), and the full historical dataset for similar-case search. |
| **Output** | `risk_score` (0–100), `risk_level` (LOW / MEDIUM / HIGH), `human_review_required` (bool), `findings` (human-readable list), `flags` (machine-readable tags), `credit_history_result` (CIBIL sub-object), `similar_past_cases` (nearest neighbors with outcomes). |
| **Tools / Dependencies** | Pure Python + pandas. No LLM calls, no external APIs, no vector databases. |
| **Decision Authority** | The numeric risk score and which flags apply. |
| **Hard Restriction** | **Advisory only** — this agent can never approve or reject a loan. It produces evidence and a score; the final decision is always made by a human officer (per the team's HITL guardrail). This agent is **deterministic and rule-based** (not an LLM call) to satisfy the team's auditability requirement. |

---

## 2. Risk Methodology

### 2.1 Scoring Factor Table

Every factor contributes points to a running `score`. The score is capped at **100** after all factors are summed.

| # | Factor | Condition | Risk Points | Flag Tag | Finding (human-readable) |
|---|--------|-----------|-------------|----------|--------------------------|
| 1 | Missing document | Each required document not submitted | +20 per doc | `MISSING_DOCUMENTS` | `Missing document: {name}` |
| 2 | Payslip income mismatch | Annualized payslip income differs from declared `income_annum` by > 10% | +25 | `INCOME_DISCREPANCY` | `Payslip income mismatch` |
| 3 | Tax return income mismatch | Tax return annual income differs from declared `income_annum` by > 10% | +25 | `INCOME_DISCREPANCY` | `Tax return income mismatch` |
| 4 | Bank asset mismatch | Document bank assets differ from declared `bank_asset_value` by > 10% | +20 | `BANK_ASSET_MISMATCH` | `Bank asset mismatch` |
| 5 | Profile mismatch | Education or self-employment status doesn't match between documents and record | +15 per field | `PROFILE_MISMATCH` | `{check} mismatch` |
| 6 | Identity mismatch | Borrower name is inconsistent across submitted documents | +30 | `IDENTITY_MISMATCH` | `Identity mismatch across documents` |
| 7 | Credit history (CIBIL) | Based on `cibil_score` band (see §2.2) | +0 to +30 | `LOW_CIBIL_SCORE` (if band is very_low or low) | `CIBIL score {score} ({band}) — credit risk contribution: +{pts}` |
| 8 | Similar-case anomaly | Historical nearest neighbors show > 60% rejection rate | +10 | `SIMILAR_CASES_HIGH_REJECTION_RATE` | `Similar historical cases show {pct}% rejection rate — anomaly risk contribution: +10` |

### 2.2 CIBIL Score Bands

| Band | CIBIL Range | Risk Points |
|------|-------------|-------------|
| Very Low | 0 – 499 | +30 |
| Low | 500 – 599 | +20 |
| Fair | 600 – 699 | +10 |
| Good | 700 – 799 | +0 |
| Excellent | 800 – 900 | +0 |

### 2.3 Risk Level Thresholds

| Score Range | Risk Level |
|-------------|------------|
| ≥ 50 | **HIGH** |
| 20 – 49 | **MEDIUM** |
| 0 – 19 | **LOW** |

### 2.4 Human Review Rule

`human_review_required = True` whenever `risk_score > 0`.

---

## 3. Scoring Explanation — Worked Example

### Scenario: Real Dataset Applicant with Very Low Credit and High Historical Rejection Rate

This worked example uses the **real applicant `loan_id = 4253` from `loan_approval_dataset.csv`** rather than a hypothetical record.

| Field | Value |
|-------|-------|
| `loan_id` | 4253 |
| `income_annum` | 4,100,000 |
| `loan_amount` | 14,100,000 |
| `cibil_score` | 300 |
| `education` | Not Graduate |
| `self_employed` | No |
| `bank_asset_value` | 2,200,000 |
| `loan_status` (dataset label) | **Rejected** |

**Important:** `loan_status` is the historical label stored in the dataset. It is **not used as an input to the Risk Agent's score**. The Risk Agent uses the applicant's financial fields and historical similar cases; the applicant's own row is excluded from the neighbor search.

The dataset contains no document-level verification results, so this worked example uses **no additional discrepancy points** (no missing-document, income-mismatch, bank-mismatch, profile-mismatch, or identity-mismatch findings). The resulting score therefore demonstrates the two Risk Agent additions that come directly from the dataset: **CIBIL scoring** and **similar-case anomaly scoring**.

### Step-by-step Scoring

| Step | Factor | Applies? | Points | Running Total |
|------|--------|----------|--------|---------------|
| 1 | Missing documents | No document-level discrepancy data in the dataset; no points applied | +0 | 0 |
| 2 | Payslip income mismatch | No document-level data | +0 | 0 |
| 3 | Tax return income mismatch | No document-level data | +0 | 0 |
| 4 | Bank asset mismatch | No document-level data | +0 | 0 |
| 5 | Profile mismatch | No document-level data | +0 | 0 |
| 6 | Identity mismatch | No document-level data | +0 | 0 |
| 7 | CIBIL score: 300 → band = `very_low` | Yes | +30 | 30 |
| 8 | Similar cases: 5/5 rejected = 100.0% | Yes (> 60% threshold) | +10 | 40 |
| 9 | Cap at 100 | 40 ≤ 100, no cap needed | — | **40** |

### Historical Similar Cases

Using the documented deterministic nearest-neighbor method (normalized `income_annum`, `loan_amount`, and `cibil_score`, weighted 0.4 / 0.4 / 0.2), the top five similar historical applicants are:

| Rank | `loan_id` | `income_annum` | `loan_amount` | `cibil_score` | `similarity_score` | `loan_status` |
|------|-----------|---------------:|--------------:|--------------:|------------------:|---------------|
| 1 | 389 | 4,300,000 | 14,500,000 | 302 | 0.9856 | Rejected |
| 2 | 1094 | 3,800,000 | 14,400,000 | 301 | 0.9802 | Rejected |
| 3 | 1959 | 4,200,000 | 14,600,000 | 324 | 0.9797 | Rejected |
| 4 | 2124 | 4,100,000 | 15,400,000 | 304 | 0.9793 | Rejected |
| 5 | 2451 | 4,100,000 | 12,400,000 | 309 | 0.9725 | Rejected |

All **5 of 5** nearest historical cases were rejected, giving a rejection rate of **100.0%**. Because this exceeds the **60%** threshold, the Risk Agent adds **+10** points and sets `SIMILAR_CASES_HIGH_REJECTION_RATE`.

### Final Output

```json
{
    "risk_score": 40,
    "risk_level": "MEDIUM",
    "human_review_required": true,
    "findings": [
        "CIBIL score 300 (very_low) — credit risk contribution: +30",
        "Similar historical cases show 100.0% rejection rate — anomaly risk contribution: +10"
    ],
    "flags": [
        "LOW_CIBIL_SCORE",
        "SIMILAR_CASES_HIGH_REJECTION_RATE"
    ],
    "credit_history_result": {
        "cibil_score": 300,
        "band": "very_low",
        "risk_contribution": 30
    },
    "similar_past_cases": [
        {"loan_id": 389, "similarity_score": 0.9856, "loan_status": "Rejected"},
        {"loan_id": 1094, "similarity_score": 0.9802, "loan_status": "Rejected"},
        {"loan_id": 1959, "similarity_score": 0.9797, "loan_status": "Rejected"},
        {"loan_id": 2124, "similarity_score": 0.9793, "loan_status": "Rejected"},
        {"loan_id": 2451, "similarity_score": 0.9725, "loan_status": "Rejected"}
    ]
}
```

The loan officer sees: this real applicant is **MEDIUM risk (score 40/100)** under the documented scoring rules. The score comes from a **very low CIBIL score (+30)** and the fact that **100.0% of the five most similar historical applicants were rejected (+10)**. Because the resulting score is above zero, `human_review_required` is `true`. The `similar_past_cases` provide transparent, auditable evidence backing the anomaly flag.

## 4. Anomaly / Similar-Case Concept

### 4.1 What "Similar Past Cases" Means

When evaluating a new loan application, the Risk Agent searches the historical loan dataset for the **N most similar past applicants** (default N=5). "Similar" means applicants whose `income_annum`, `loan_amount`, and `cibil_score` are numerically close to the current applicant. The idea is simple: **if past applicants who looked just like this one were mostly rejected, that's a red flag worth surfacing**.

### 4.2 How the Nearest-Neighbor Search Works

1. **Feature selection**: Three numeric columns are used — `income_annum`, `loan_amount`, and `cibil_score`.

2. **Normalization**: Each feature is min-max normalized using the dataset's own min/max values, so all three features are on a 0–1 scale and none dominates the distance calculation just because it has larger raw numbers.

3. **Weighted Euclidean distance**: The distance between the applicant and each historical record is:

   ```
   distance = sqrt(
       0.4 × (Δincome_norm)² +
       0.4 × (Δloan_amount_norm)² +
       0.2 × (Δcibil_score_norm)²
   )
   ```

   Weights: `income_annum = 0.4`, `loan_amount = 0.4`, `cibil_score = 0.2`. Income and loan amount are weighted higher because they are the primary financial dimensions of risk in this dataset.

4. **Similarity score**: Converted from distance via `similarity = 1 / (1 + distance)`, so closer neighbors get a higher score (range 0–1, where 1 = identical).

5. **Self-exclusion**: If the applicant's own `loan_id` appears in the dataset, it is excluded from the neighbor search.

6. **Rejection rate**: Among the top N neighbors, the proportion with `loan_status = Rejected` is computed. If this exceeds **60%**, a `SIMILAR_CASES_HIGH_REJECTION_RATE` flag and +10 risk points are added.

### 4.3 Why Deterministic, Not LLM/Embedding-Based

For this MVP, the similar-case search is a **deterministic, rule-based calculation** — not an LLM embedding or vector-database lookup. This was a deliberate team architecture decision for the following reasons:

- **Auditability**: Every step (normalization, weights, distance formula) is fully transparent and reproducible. Given the same inputs, the same output is always produced. There is no stochastic element.
- **Speed**: No API call or model inference latency — the search runs in-memory over a pandas DataFrame.
- **Simplicity**: For a hackathon MVP with a ~4,000-row Kaggle dataset, a brute-force distance calculation over three features is perfectly adequate.
- **No dependencies**: No need for a vector database, embedding model, or external service.

### 4.4 Future: Vector-Search Upgrade Path

Per the team's architecture document, the `search_similar_cases()` function is designed as a **pluggable interface** that can be upgraded in a fuller production build:

1. **Same contract**: The function signature `search_similar_cases(record, dataset, top_n=5)` and its return shape (`similar_cases`, `rejection_rate`, `risk_contribution`, `flag`) would remain the same.
2. **Vector store backend**: Instead of brute-force pandas iteration, the implementation would:
   - Generate embeddings for each applicant record (using a pre-trained or fine-tuned model).
   - Store embeddings in a vector database (e.g., Pinecone, Weaviate, ChromaDB, or FAISS).
   - Perform approximate nearest-neighbor (ANN) search at query time.
3. **Richer features**: A vector-based approach could incorporate more features (text fields like occupation, address, employer name) that are hard to compare with simple Euclidean distance.
4. **Scale**: ANN search scales to millions of records with sub-millisecond latency, whereas brute-force pandas iteration becomes slow beyond ~100K rows.

The current deterministic implementation is the correct starting point: it validates the concept, provides auditable results, and establishes the interface contract that a vector-search upgrade would seamlessly replace.

---

## 5. Suggestions for Other Teammates

> **Note for Sneha / app.py owner**: The risk engine now returns three new keys in `risk_result`:
> - `flags` — a sorted list of machine-readable tags (e.g., `["LOW_CIBIL_SCORE", "MISSING_DOCUMENTS"]`)
> - `similar_past_cases` — a list of neighbor dicts with `loan_id`, `similarity_score`, `loan_status`
> - `credit_history_result` — a dict with `cibil_score`, `band`, `risk_contribution`
>
> The Streamlit dashboard (`app.py`) could display these to give the loan officer richer evidence. For example:
> - Show flags as colored badges in the risk assessment panel.
> - Show `similar_past_cases` as a small table so the officer can see comparable historical applicants.
> - Show the CIBIL band and its contribution in the credit section.
>
> These are additive suggestions — the existing `app.py` output continues to work unchanged since the original keys (`risk_score`, `risk_level`, `human_review_required`, `findings`) are preserved.
