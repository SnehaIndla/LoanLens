import re
from pathlib import Path
from difflib import SequenceMatcher

def normalize_name(name: str) -> str:
    """Normalize names for fuzzy identity matching."""
    if not name:
        return ""
    clean = re.sub(r"[^\w\s]", "", str(name).lower())
    return " ".join(clean.split())


def check_identity_consistency(claims_by_doc: dict) -> dict:
    """
    Check if borrower name matches across uploaded document types (Payslip, Bank, Tax, KYC).
    """
    names_found = []
    for doc_type, claims in claims_by_doc.items():
        if isinstance(claims, dict) and claims.get("borrower_name"):
            names_found.append({
                "document": doc_type,
                "name": claims["borrower_name"],
                "normalized": normalize_name(claims["borrower_name"])
            })

    if not names_found:
        return {"check": "identity_consistency", "status": "match", "names": []}

    ref_norm = names_found[0]["normalized"]
    mismatches = []

    for item in names_found[1:]:
        norm = item["normalized"]
        ratio = SequenceMatcher(None, ref_norm, norm).ratio()
        if ratio < 0.70 and ref_norm not in norm and norm not in ref_norm:
            mismatches.append(item["document"])

    status = "mismatch" if mismatches else "match"
    return {
        "check": "identity_consistency",
        "status": status,
        "names": names_found,
        "mismatch_docs": mismatches
    }


def check_cross_income(claims_by_doc: dict) -> dict:
    """
    Cross-check annual income between Payslip (monthly x 12) and Tax Return.
    """
    payslip_claims = claims_by_doc.get("payslip", {})
    tax_claims = claims_by_doc.get("tax_return", {})

    monthly_income = payslip_claims.get("monthly_income") if isinstance(payslip_claims, dict) else None
    tax_annual = tax_claims.get("annual_income") if isinstance(tax_claims, dict) else None

    payslip_annual = monthly_income * 12.0 if monthly_income is not None else None

    if payslip_annual is not None and tax_annual is not None:
        diff = abs(payslip_annual - tax_annual)
        ref = max(tax_annual, 1.0)
        pct = (diff / ref) * 100.0
        return {
            "check": "income_consistency",
            "payslip_annualized": round(payslip_annual, 2),
            "tax_annual": round(tax_annual, 2),
            "difference": round(diff, 2),
            "difference_percent": round(pct, 2),
            "mismatch": pct > 15.0
        }

    return {
        "check": "income_consistency",
        "payslip_annualized": round(payslip_annual, 2) if payslip_annual else None,
        "tax_annual": round(tax_annual, 2) if tax_annual else None,
        "difference_percent": 0.0,
        "mismatch": False
    }


def check_cibil_threshold(cibil_score: float) -> dict:
    """
    Evaluates CIBIL score against underwriting threshold bands:
    - >= 700: Normal creditworthiness
    - 650 - 699: CIBIL_BORDERLINE -> Forces Manual Review
    - < 650: CIBIL_TOO_LOW -> Hard Flag / Forces Manual Review
    """
    if cibil_score >= 700:
        return {"status": "PASS", "flag": None, "message": "CIBIL score is acceptable (>= 700)"}
    elif cibil_score >= 650:
        return {"status": "BORDERLINE", "flag": "CIBIL_BORDERLINE", "message": f"CIBIL score is borderline ({int(cibil_score)}), requires manual review"}
    else:
        return {"status": "FAIL", "flag": "CIBIL_TOO_LOW", "message": f"CIBIL score is too low ({int(cibil_score)} < 650), credit threshold failed"}


def check_loan_eligibility(loan_amount: float, annual_income: float, multiplier: float = 5.0) -> dict:
    """
    Evaluates loan amount request against 5x annual income eligibility multiplier.
    """
    max_eligible = annual_income * multiplier
    if loan_amount > max_eligible:
        return {
            "eligible": False,
            "flag": "LOAN_AMOUNT_EXCEEDS_ELIGIBILITY",
            "max_eligible": max_eligible,
            "message": f"Requested loan ({loan_amount:,.0f}) exceeds {multiplier:.0f}x annual income limit ({max_eligible:,.0f})"
        }
    return {
        "eligible": True,
        "flag": None,
        "max_eligible": max_eligible,
        "message": f"Loan amount is within eligible limit ({max_eligible:,.0f})"
    }


def verify_cross_documents(claims_by_doc: dict, form_inputs: dict) -> dict:
    """
    Main cross-document verification engine.
    Executes cross-document consistency checks, CIBIL threshold evaluation, loan eligibility checks,
    and assembles the 5-feature applicant vector.
    """
    required_docs = ["payslip", "bank_statement", "tax_return", "kyc"]
    missing_docs = [doc for doc in required_docs if doc not in claims_by_doc or not claims_by_doc[doc]]

    # 1. Identity & Income Checks
    identity_result = check_identity_consistency(claims_by_doc)
    income_result = check_cross_income(claims_by_doc)

    # 2. Extraction Failures & Bank Assets
    bank_claims = claims_by_doc.get("bank_statement", {})
    bank_asset_val = bank_claims.get("bank_asset_value", 0.0) if isinstance(bank_claims, dict) else 0.0

    extraction_failures = []
    if "payslip" in claims_by_doc and isinstance(claims_by_doc["payslip"], dict):
        if claims_by_doc["payslip"].get("monthly_income") is None:
            extraction_failures.append("Payslip: Monthly Income missing")
    if "bank_statement" in claims_by_doc and isinstance(claims_by_doc["bank_statement"], dict):
        if claims_by_doc["bank_statement"].get("bank_asset_value") is None:
            extraction_failures.append("Bank Statement: Bank Asset Balance missing")

    # 3. Income Resolution for Underwriting
    payslip_annual = income_result.get("payslip_annualized")
    tax_annual = income_result.get("tax_annual")
    income_annum = tax_annual or payslip_annual or float(form_inputs.get("income_annum", 5000000.0))

    # 4. CIBIL & Loan Amount Eligibility Rules
    cibil_score = float(form_inputs.get("cibil_score", 650.0))
    loan_amount = float(form_inputs.get("loan_amount", 15000000.0))

    cibil_check = check_cibil_threshold(cibil_score)
    eligibility_check = check_loan_eligibility(loan_amount, income_annum, multiplier=5.0)

    # 5. Assemble 5-Feature Vector for ML Model
    applicant_features = {
        "income_annum": float(income_annum),
        "loan_amount": float(loan_amount),
        "loan_term": float(form_inputs.get("loan_term", 10.0)),
        "cibil_score": float(cibil_score),
        "bank_asset_value": float(bank_asset_val or form_inputs.get("bank_asset_value", 0.0))
    }

    return {
        "missing_documents": missing_docs,
        "extraction_failures": extraction_failures,
        "identity_result": identity_result,
        "income_result": income_result,
        "cibil_check": cibil_check,
        "eligibility_check": eligibility_check,
        "claims_by_doc": claims_by_doc,
        "applicant_features": applicant_features
    }