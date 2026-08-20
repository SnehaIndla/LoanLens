from pathlib import Path
import pytest
from unittest.mock import patch
from claims import SeverityLevel
from verification import CrossValidationAgent

from extractor import extract_text
from classifier import classify_document
from claims import extract_claims

from verification import (
    get_loan_record,
    compare_bank_assets,
    compare_profile,
    compare_document_identity,
    check_payslip_income,
    check_tax_income
)

from document_requirements import check_missing_documents
from risk_engine import calculate_risk
from summary_generator import generate_summary
from genai_agent import generate_ai_summary


# =====================================
# READ ALL DOCUMENTS FOR A LOAN
# =====================================

def read_loan_documents(loan_id):

    folder = Path(
        f"data/documents/loan_{loan_id}"
    )

    all_claims = {}
    document_claims = []

    for pdf_file in folder.glob("*.pdf"):

        pages = extract_text(pdf_file)

        full_text = "\n".join(
            page["text"]
            for page in pages
        )

        document_type = classify_document(
            full_text,
            pdf_file.name
        )

        claims = extract_claims(
            full_text,
            document_type
        )

        # Combined claims
        all_claims.update(claims)

        # Individual document claims
        document_claims.append(
            (
                document_type,
                claims
            )
        )

    return all_claims, document_claims


# =====================================
# ANALYZE ONE LOAN
# =====================================

def analyze_loan(loan_id):

    print("\n" + "=" * 60)
    print(f"ANALYZING LOAN ID: {loan_id}")
    print("=" * 60)

    # =================================
    # GET KAGGLE RECORD
    # =================================

    record = get_loan_record(loan_id)

    if record is None:

        print("Loan record not found.")

        return None

    # =================================
    # READ DOCUMENTS
    # =================================

    claims, document_claims = read_loan_documents(
        loan_id
    )

    print("\nDOCUMENT CLAIMS:")
    print(claims)

    # =================================
    # MISSING DOCUMENT CHECK
    # =================================

    missing_documents = check_missing_documents(
        document_claims
    )

    print("\nDOCUMENT COMPLETENESS CHECK:")

    if missing_documents:

        print("⚠ MISSING DOCUMENTS:")

        for document in missing_documents:

            print(f"- {document}")

    else:

        print(
            "✓ All required documents submitted"
        )

    # =================================
    # PAYSLIP INCOME CHECK
    # =================================

    payslip_result = check_payslip_income(
        record,
        claims
    )

    if payslip_result:

        print("\nPAYSLIP INCOME CHECK:")

        print(
            f"Difference: "
            f"{payslip_result['difference_percent']}%"
        )

        if payslip_result["difference_percent"] > 10:

            print(
                "⚠ PAYSLIP INCOME MISMATCH"
            )

        else:

            print(
                "✓ Payslip income consistent"
            )

    # =================================
    # TAX RETURN INCOME CHECK
    # =================================

    tax_result = check_tax_income(
        record,
        claims
    )

    if tax_result:

        print("\nTAX RETURN INCOME CHECK:")

        print(
            f"Difference: "
            f"{tax_result['difference_percent']}%"
        )

        if tax_result["difference_percent"] > 10:

            print(
                "⚠ TAX RETURN INCOME MISMATCH"
            )

        else:

            print(
                "✓ Tax return income consistent"
            )

    # =================================
    # BANK ASSET CHECK
    # =================================

    bank_result = compare_bank_assets(
        record,
        claims
    )

    if bank_result:

        print("\nBANK ASSET CHECK:")

        print(
            f"Difference: "
            f"{bank_result['difference_percent']}%"
        )

        if bank_result["difference_percent"] > 10:

            print(
                "⚠ BANK ASSET MISMATCH"
            )

        else:

            print(
                "✓ Bank assets consistent"
            )

    # =================================
    # PROFILE CHECK
    # =================================

    profile_results = compare_profile(
        record,
        claims
    )

    print("\nPROFILE CHECK:")

    for result in profile_results:

        status = (
            "✓ MATCH"
            if result["match"]
            else "⚠ MISMATCH"
        )

        print(
            f"{result['check']}: {status}"
        )

    # =================================
    # CROSS-DOCUMENT IDENTITY CHECK
    # =================================

    identity_result = compare_document_identity(
        document_claims
    )

    print("\nIDENTITY CHECK:")

    if identity_result["status"] == "match":

        print(
            "✓ Identity consistent"
        )

    elif identity_result["status"] == "mismatch":

        print(
            "⚠ IDENTITY MISMATCH"
        )

        for item in identity_result["names"]:

            print(
                f"{item['document']}: "
                f"{item['name']}"
            )

    else:

        print(
            "⚠ Insufficient identity evidence"
        )

    # =================================
    # RISK ASSESSMENT
    # =================================

    risk_result = calculate_risk(
        missing_documents,
        payslip_result,
        tax_result,
        bank_result,
        profile_results,
        identity_result
    )

    print("\n" + "=" * 60)
    print("LOANLENS RISK ASSESSMENT")
    print("=" * 60)

    print(
        f"Risk Score: "
        f"{risk_result['risk_score']} / 100"
    )

    print(
        f"Risk Level: "
        f"{risk_result['risk_level']}"
    )

    print(
        "Human Review Required: "
        f"{'YES' if risk_result['human_review_required'] else 'NO'}"
    )

    print("\nFINDINGS:")

    if risk_result["findings"]:

        for finding in risk_result["findings"]:

            print(
                f"⚠ {finding}"
            )

    else:

        print(
            "✓ No significant issues detected"
        )

    # =================================
    # LOAN PROCESSING SUMMARY
    # =================================

    summary = generate_summary(
        loan_id,
        risk_result,
        missing_documents,
        payslip_result,
        tax_result,
        bank_result,
        profile_results,
        identity_result
    )

    print("\n" + "=" * 60)
    print("GENAI-READY LOAN SUMMARY")
    print("=" * 60)

    print(summary)

    # =================================
    # LOCAL GENAI SUMMARY
    # =================================

    ai_summary = generate_ai_summary(
        loan_id,
        risk_result,
        missing_documents,
        payslip_result,
        tax_result,
        bank_result,
        profile_results,
        identity_result
    )

    print("\n" + "=" * 60)
    print("LOANLENS AI SUMMARY")
    print("=" * 60)

    print(ai_summary)

    # =================================
    # RETURN RESULTS FOR STREAMLIT
    # =================================

    return {
        "loan_id": loan_id,
        "record": record,
        "claims": claims,
        "missing_documents": missing_documents,
        "payslip_result": payslip_result,
        "tax_result": tax_result,
        "bank_result": bank_result,
        "profile_results": profile_results,
        "identity_result": identity_result,
        "risk_result": risk_result,
        "summary": summary,
        "ai_summary": ai_summary
    }


# =====================================
# TEST LOANS 5–8
# =====================================

# =====================================
# PYTEST UNIT TESTS
# =====================================

@pytest.fixture(autouse=True)
def mock_ollama():
    with patch("ollama.chat") as mock_chat:
        mock_chat.return_value = {
            "message": {
                "content": "Mocked AI explanation."
            }
        }
        yield mock_chat


def test_perfect_match():
    record = {
        "applicant_name": "John Doe",
        "person_income": 120000.0,
        "person_emp_length": 5.0,
        "cb_person_default_on_file": "N",
        "cb_person_cred_hist_length": 10.0,
        "person_age": 30.0,
        "person_home_ownership": "OWN",
        "loan_amnt": 20000.0,
        "loan_id": 101
    }
    extracted = {
        "borrower_name": "John Doe",
        "employer": "Tech Corp",
        "monthly_income": 10000.0,  # 10000 * 12 = 120000
        "years_at_company": 5.0,
        "defaults": 0,
        "credit_history_duration": 10.0,
        "calculated_age": 30.0,
        "dob": "1996-08-20"
    }

    agent = CrossValidationAgent()
    res = agent.cross_check_fields(record, extracted)

    assert res.is_consistent is True
    assert res.consistency_score == 100.0
    assert res.total_discrepancies == 0


def test_income_inflation():
    record = {
        "applicant_name": "John Doe",
        "person_income": 95000.0,
        "loan_id": 102
    }
    extracted = {
        "borrower_name": "John Doe",
        "employer": "Tech Corp",
        "monthly_income": 5000.0,  # 5000 * 12 = 60000
    }

    agent = CrossValidationAgent()
    res = agent.cross_check_fields(record, extracted)

    assert res.is_consistent is False
    assert res.high_count == 1
    
    income_disc = next(d for d in res.discrepancies if d.field == "person_income")
    assert income_disc.severity == SeverityLevel.HIGH
    assert income_disc.variance_percentage > 35.0


def test_default_concealment():
    record = {
        "applicant_name": "John Doe",
        "cb_person_default_on_file": "N",
        "loan_id": 103
    }
    extracted = {
        "borrower_name": "John Doe",
        "defaults": 2,
    }

    agent = CrossValidationAgent()
    res = agent.cross_check_fields(record, extracted)

    assert res.is_consistent is False
    assert res.critical_count == 1
    
    default_disc = next(d for d in res.discrepancies if d.field == "cb_person_default_on_file")
    assert default_disc.severity == SeverityLevel.CRITICAL


def test_fuzzy_name():
    record = {
        "applicant_name": "Robert C. Jenkins",
        "loan_id": 104
    }
    extracted = {
        "borrower_name": "Robert Jenkins",
    }

    agent = CrossValidationAgent()
    res = agent.cross_check_fields(record, extracted)

    assert res.low_count == 1
    name_disc = next(d for d in res.discrepancies if d.field == "applicant_name")
    assert name_disc.severity == SeverityLevel.LOW


def test_multiple_stacking_discrepancies():
    record = {
        "applicant_name": "John Doe",
        "person_income": 100000.0,
        "person_emp_length": 8.0,
        "person_home_ownership": "RENT",
        "loan_id": 105
    }
    extracted = {
        "borrower_name": "John Doe",
        "employer": "Tech Corp",
        "monthly_income": 7000.0,  # 84k (100k vs 84k -> 19.05% higher -> HIGH: -20)
        "years_at_company": 6.5,  # 8 vs 6.5 -> 1.5 year variance -> MEDIUM: -10
        "rent_debits": None,  # missing rent debits -> MEDIUM: -10
    }

    agent = CrossValidationAgent()
    res = agent.cross_check_fields(record, extracted)

    assert res.is_consistent is False
    assert res.consistency_score == 60.0
    assert res.high_count == 1
    assert res.medium_count == 2
    assert res.total_discrepancies == 3


if __name__ == "__main__":
    for loan_id in range(1, 11):
        analyze_loan(loan_id)