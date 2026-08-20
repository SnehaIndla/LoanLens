from pathlib import Path

from extractor import extract_text
from classifier import classify_document
from claims import extract_claims

from verification import (
    get_loan_record,
    load_dataset,
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
        identity_result,
        record,
        load_dataset()
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
    # FLAGS
    # =================================

    if risk_result.get("flags"):

        print("\nFLAGS:")

        for flag in risk_result["flags"]:

            print(
                f"🚩 {flag}"
            )

    # =================================
    # SIMILAR PAST CASES
    # =================================

    similar_cases = risk_result.get(
        "similar_past_cases",
        []
    )

    if similar_cases:

        print("\nSIMILAR PAST CASES:")

        for case in similar_cases:

            print(
                f"  Loan {case['loan_id']}"
                f" | Similarity:"
                f" {case['similarity_score']}"
                f" | Status:"
                f" {case['loan_status']}"
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

if __name__ == "__main__":

    for loan_id in range(1, 11):
        analyze_loan(loan_id)