"""
LoanLens - Document Classification Agent Tests

Tests for classifier.py covering:
    - High-confidence classification for all 4 document types
    - Unknown / unrecognized documents
    - Ambiguous documents
    - Low-confidence edge cases
    - Empty / invalid input
    - Filename-only classification
    - Backward compatibility
    - All scores present in output
"""

import pytest

from classifier import (
    classify_document,
    classify_document_detailed,
)


# ----------------------------------------------------------
# 1. Payslip - high confidence
# ----------------------------------------------------------

def test_payslip_high_confidence():
    """Payslip with strong keywords should be classified
    with high confidence."""

    text = (
        "MONTHLY PAYSLIP\n"
        "Borrower: John\n"
        "Monthly Income: 50,000\n"
        "Pay Period: August 2026\n"
        "Employer: ABC Technologies"
    )

    result = classify_document_detailed(text)

    assert result["document_type"] == "payslip"
    assert result["confidence"] >= 0.70
    assert result["status"] == "classified"


# ----------------------------------------------------------
# 2. Bank statement - high confidence
# ----------------------------------------------------------

def test_bank_statement_high_confidence():
    """Bank statement with strong keywords should be
    classified with high confidence."""

    text = (
        "BANK STATEMENT\n"
        "Account Holder: John\n"
        "Bank Asset Balance: 1,000,000\n"
        "Monthly Salary Credit: 50,000\n"
        "Statement Period: January 2026 - August 2026"
    )

    result = classify_document_detailed(text)

    assert result["document_type"] == "bank_statement"
    assert result["confidence"] >= 0.70
    assert result["status"] == "classified"


# ----------------------------------------------------------
# 3. KYC / ID proof - high confidence
# ----------------------------------------------------------

def test_kyc_high_confidence():
    """KYC document with strong keywords should be
    classified with high confidence."""

    text = (
        "KYC DOCUMENT\n"
        "Name: John\n"
        "Identity Verification: Valid\n"
        "Self Employed: No"
    )

    result = classify_document_detailed(text)

    assert result["document_type"] == "kyc"
    assert result["confidence"] >= 0.70
    assert result["status"] == "classified"


# ----------------------------------------------------------
# 4. Tax return - high confidence
# ----------------------------------------------------------

def test_tax_return_high_confidence():
    """Tax return with strong keywords should be
    classified with high confidence."""

    text = (
        "INCOME TAX RETURN\n"
        "Taxpayer: John\n"
        "Annual Income: 600,000\n"
        "Assessment Year: 2026\n"
        "Return Status: Filed"
    )

    result = classify_document_detailed(text)

    assert result["document_type"] == "tax_return"
    assert result["confidence"] >= 0.70
    assert result["status"] == "classified"


# ----------------------------------------------------------
# 5. Unknown document
# ----------------------------------------------------------

def test_unknown_document():
    """Text with no matching keywords should be
    classified as unknown / unrecognized."""

    text = (
        "Shopping receipt for groceries "
        "at the local supermarket. Total: 500."
    )

    result = classify_document_detailed(text)

    assert result["document_type"] == "unknown"
    assert result["status"] == "unrecognized"


# ----------------------------------------------------------
# 6. Ambiguous document
# ----------------------------------------------------------

def test_ambiguous_document():
    """Text with keywords from multiple categories
    should result in low confidence or classified
    with reduced certainty."""

    text = (
        "Monthly Income: 50000\n"
        "Annual Income: 600000\n"
        "Bank Asset Balance: 1000000\n"
        "Identity Verification: Valid"
    )

    result = classify_document_detailed(text)

    # When keywords from many categories are present,
    # the classifier should flag ambiguity
    assert result["status"] in (
        "low_confidence", "classified"
    )


# ----------------------------------------------------------
# 7. Low confidence
# ----------------------------------------------------------

def test_low_confidence():
    """Text with weak keyword matches from multiple
    categories should result in low confidence."""

    text = (
        "This document mentions an employer "
        "and some transaction records. "
        "The taxpayer also provided a passport."
    )

    result = classify_document_detailed(text)

    # Weak matches across payslip ("employer"),
    # bank_statement ("transaction"),
    # tax_return ("taxpayer"), kyc ("passport").
    # No single category dominates strongly.
    assert result["status"] in (
        "low_confidence", "unrecognized"
    ) or result["confidence"] < 0.70


# ----------------------------------------------------------
# 8. Empty input
# ----------------------------------------------------------

def test_empty_input():
    """Empty text and filename should return unknown
    with zero confidence."""

    result = classify_document_detailed("", "")

    assert result["document_type"] == "unknown"
    assert result["confidence"] == 0.0
    assert result["status"] == "unrecognized"


# ----------------------------------------------------------
# 9. None / invalid input
# ----------------------------------------------------------

def test_none_input():
    """None values should be handled gracefully
    and return unknown."""

    result = classify_document_detailed(None, None)

    assert result["document_type"] == "unknown"
    assert result["confidence"] == 0.0
    assert result["status"] == "unrecognized"


# ----------------------------------------------------------
# 10. Filename-only classification
# ----------------------------------------------------------

def test_filename_only():
    """Empty text but a meaningful filename should
    still produce a classification via filename hints."""

    result = classify_document_detailed(
        "", "payslip.pdf"
    )

    assert result["document_type"] == "payslip"
    assert result["confidence"] > 0.0


# ----------------------------------------------------------
# 11. Backward compatibility - returns string
# ----------------------------------------------------------

def test_backward_compatibility_returns_string():
    """classify_document() must return a plain string,
    not a dict, for backward compatibility."""

    text = (
        "MONTHLY PAYSLIP\n"
        "Monthly Income: 50,000\n"
        "Pay Period: August 2026"
    )

    result = classify_document(text)

    assert isinstance(result, str)
    assert result == "payslip"


# ----------------------------------------------------------
# 12. All scores present in output
# ----------------------------------------------------------

def test_all_scores_present():
    """classify_document_detailed() must include
    all_scores with all 4 categories."""

    text = (
        "INCOME TAX RETURN\n"
        "Annual Income: 600,000\n"
        "Assessment Year: 2026"
    )

    result = classify_document_detailed(text)

    assert "all_scores" in result

    assert set(result["all_scores"].keys()) == {
        "payslip",
        "bank_statement",
        "tax_return",
        "kyc",
    }
