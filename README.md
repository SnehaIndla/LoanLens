# LoanLens: Cross-Validation & Consistency Agent

LoanLens is an intelligent, transparent, and explainable document verification and risk assessment platform for loan processing. This repository implements the **Cross-Validation & Consistency Agent**, which cross-verifies declared loan application fields against extracted document data (from Payslips, Bank Statements, ID Proofs, and Credit Bureau reports) and computes a consistency score with precise severity-based discrepancy tracking.

---

## 🚀 Key Features

- **Pydantic V2 Data Models**: Clean, validated structure for discrepancies and verification results.
- **Rule & Fuzzy Validation Engine**:
  - **Fuzzy Name Matching**: Cross-document name verification using Jaro-Winkler/Levenshtein principles (implemented via Python's robust `difflib.SequenceMatcher`).
  - **Annualized Income check**: Annualized net/gross salary and statement transaction checks against declared income.
  - **Employment Tenure date-math**: Validates declared years of employment against document start dates or tenure records (calculated relative to reference date `2026-08-20`).
  - **Age check**: Verified DOB date calculations vs declared age.
  - **Credit profile validation**: Discovers default concealment and credit history duration variance.
- **Deterministic Scoring & Risk Assessment**: Starts with a baseline score of `100.0` and deducts penalties based on severity (`CRITICAL`: -40, `HIGH`: -20, `MEDIUM`: -10, `LOW`: -2).
- **LangGraph supervisor integration**: Seamlessly hooks into the orchestration pipeline.
- **Streamlit Interactive Dashboard**: Responsive UI for manual reviews, displaying findings, AI explanations, and document checks.

---

## 📊 Comparison Matrix

| Declared Field | Primary Extracted Source Document | Extracted Target Field | Comparison Type |
| :--- | :--- | :--- | :--- |
| `person_income` | Payslip / Bank Statement | `monthly_net_pay * 12`, `monthly_gross_pay * 12`, `annual_salary`, `total_credited_income` | Numerical / Range Variance |
| `person_emp_length` | Payslip / Employment Letter | `employment_start_date`, `tenure_months`, `years_at_company` | Date Math / Float Delta |
| `person_age` | ID Proof (PAN / Aadhaar / Passport / DL) | `dob`, `calculated_age` | Exact Date Calculation |
| `loan_amnt` | Loan Application Form | `requested_loan_amount` | Numerical Match |
| `cb_person_default_on_file` | Credit Report | `historical_defaults_count`, `delinquency_flag` | Boolean / Categorical Match |
| `cb_person_cred_hist_length` | Credit Report | `oldest_trade_line_years`, `credit_history_duration` | Numerical / Float Delta |
| `person_home_ownership` | Bank Statement / ID address proof | `rent_debits`, `mortgage_debits`, `address_type` | Categorical / Transaction Check |
| `applicant_name` | ID Proof vs. Payslip vs. Bank Statement | `full_name`, `name_on_document` | Fuzzy String Match |

---

## ⚠️ Severity Thresholds & Rules

### A. Critical Severity (`CRITICAL`) - Penalty: -40
- **Identity Mismatch**: Name similarity score $< 0.70$.
- **Prior Default Concealment**: Declared default is `"N"`, but Credit Report shows defaults $> 0$ or delinquency flag.
- **Unverifiable Income Source**: Declared income $> 0$, but salary transactions are absent or employer is missing.

### B. High Severity (`HIGH`) - Penalty: -20
- **Significant Income Over-declaration**: Declared income $> 15\%$ higher than annualized document income.
- **Employment Length Exaggeration**: Declared years of employment exceeds verified tenure by $> 2.0$ years.
- **Credit History Length Variance**: Declared credit history length differs from bureau record by $> 3.0$ years.
- **Age Discrepancy**: Declared age differs from ID DOB calculated age by $> 1$ year.

### C. Medium Severity (`MEDIUM`) - Penalty: -10
- **Moderate Income Variance**: Declared income is between $5\%$ and $15\%$ higher than document income.
- **Minor Employment Tenure Variance**: Declared employment length is between $0.5$ and $2.0$ years higher than document tenure.
- **Home Ownership Ambiguity**: Declared `RENT` but recurring rent debit transactions are missing from bank statements.

### D. Low Severity (`LOW`) - Penalty: -2
- **Minor Under-declaration**: Declared income is lower than verified document income (favorable variance).
- **Minor Name Variation**: Similarity score between $0.80$ and $0.95$.
- **Minor Date Rounding**: Discrepancies within standard payroll cycle cutoff ($\le 15$ days).

---

## ⚙️ Installation & Setup

1. **Clone & Navigate**:
   ```bash
   git clone <your-repository-url>
   cd Cross-Validation-&-Consistency-Agent
   ```
2. **Install Dependencies**:
   Ensure python 3.10+ is installed, then run:
   ```bash
   pip install -r requirements.txt
   ```
3. **Download Dataset & Generate Mock Data**:
   ```bash
   # Run the document generator to populate mock PDF files
   python scripts/generate_documents.py
   ```

---

## 🧪 Running Tests

The test suite runs using `pytest` and verifies the 5 primary test cases (Perfect Match, Income Inflation, Default Concealment, Fuzzy Name Match, and Penalty Stacking):

```bash
# Set PYTHONPATH to include the core directory and run pytest
export PYTHONPATH=core
pytest core/test_verification.py
```

On Windows PowerShell:
```powershell
$env:PYTHONPATH="core"
python -m pytest core/test_verification.py
```

---

## 🖥️ Running the Streamlit App

Start the Streamlit dashboard to inspect loan applications:

```bash
python -m streamlit run app.py
```
Open your browser and navigate to `http://localhost:8501`.
