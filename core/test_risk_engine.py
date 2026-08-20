import sys
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

from risk_engine import (
    calculate_risk,
    search_similar_cases,
    get_cibil_band
)


# =====================================
# HELPERS
# =====================================

def make_identity_match():
    """Return a matching identity result."""

    return {
        "check": "identity_consistency",
        "status": "match",
        "names": []
    }


def make_identity_mismatch():
    """Return a mismatching identity result."""

    return {
        "check": "identity_consistency",
        "status": "mismatch",
        "names": [
            {
                "document": "payslip",
                "name": "alice"
            },
            {
                "document": "kyc",
                "name": "bob"
            }
        ]
    }


def make_synthetic_dataset():
    """
    Build a small synthetic dataset
    for similar-case testing.
    """

    data = {
        "loan_id": [
            101, 102, 103,
            104, 105, 106,
            107, 108
        ],
        "income_annum": [
            500000, 510000, 520000,
            900000, 950000, 480000,
            505000, 495000
        ],
        "loan_amount": [
            2000000, 2100000, 1900000,
            8000000, 8500000, 2050000,
            2000000, 1950000
        ],
        "cibil_score": [
            600, 590, 610,
            800, 810, 580,
            605, 595
        ],
        "loan_status": [
            " Rejected", " Rejected", " Rejected",
            " Approved", " Approved", " Rejected",
            " Rejected", " Rejected"
        ]
    }

    return pd.DataFrame(data)


# =====================================
# TEST 1: High CIBIL + no discrepancies
#         -> LOW risk, no credit flag
# =====================================

print("\n" + "=" * 60)
print("TEST 1: High CIBIL + no discrepancies")
print("=" * 60)

record_good = {
    "loan_id": 999,
    "income_annum": 900000,
    "loan_amount": 5000000,
    "cibil_score": 780
}

result_1 = calculate_risk(
    missing_documents=[],
    payslip_result=None,
    tax_result=None,
    bank_result=None,
    profile_results=[],
    identity_result=make_identity_match(),
    record=record_good,
    dataset=make_synthetic_dataset()
)

assert result_1["risk_level"] == "LOW", (
    f"Expected LOW, got {result_1['risk_level']}"
)

assert result_1["risk_score"] == 0, (
    f"Expected 0, got {result_1['risk_score']}"
)

assert "LOW_CIBIL_SCORE" not in result_1["flags"], (
    "LOW_CIBIL_SCORE flag should not be present"
)

print(f"Risk Score: {result_1['risk_score']}")
print(f"Risk Level: {result_1['risk_level']}")
print(f"Flags: {result_1['flags']}")
print("✓ PASSED")


# =====================================
# TEST 2: Low CIBIL -> risk contribution
#         + LOW_CIBIL_SCORE flag
# =====================================

print("\n" + "=" * 60)
print("TEST 2: Low CIBIL score")
print("=" * 60)

record_low_cibil = {
    "loan_id": 998,
    "income_annum": 600000,
    "loan_amount": 3000000,
    "cibil_score": 450
}

result_2 = calculate_risk(
    missing_documents=[],
    payslip_result=None,
    tax_result=None,
    bank_result=None,
    profile_results=[],
    identity_result=make_identity_match(),
    record=record_low_cibil,
    dataset=make_synthetic_dataset()
)

assert result_2["risk_score"] >= 30, (
    f"Expected >= 30 from very_low CIBIL,"
    f" got {result_2['risk_score']}"
)

assert "LOW_CIBIL_SCORE" in result_2["flags"], (
    "LOW_CIBIL_SCORE flag should be present"
)

credit = result_2["credit_history_result"]

assert credit is not None, (
    "credit_history_result should not be None"
)

assert credit["band"] == "very_low", (
    f"Expected very_low band,"
    f" got {credit['band']}"
)

assert credit["risk_contribution"] == 30, (
    f"Expected 30 pts,"
    f" got {credit['risk_contribution']}"
)

print(f"Risk Score: {result_2['risk_score']}")
print(f"CIBIL Band: {credit['band']}")
print(f"Flags: {result_2['flags']}")
print("✓ PASSED")


# =====================================
# TEST 3: Neighbors mostly rejected
#         -> anomaly flag + cases
# =====================================

print("\n" + "=" * 60)
print("TEST 3: Similar cases — high rejection")
print("=" * 60)

# This applicant is very close to the
# cluster of rejected loans (IDs 101-108)
# in the synthetic dataset.

record_risky_neighborhood = {
    "loan_id": 997,
    "income_annum": 500000,
    "loan_amount": 2000000,
    "cibil_score": 600
}

result_3 = calculate_risk(
    missing_documents=[],
    payslip_result=None,
    tax_result=None,
    bank_result=None,
    profile_results=[],
    identity_result=make_identity_match(),
    record=record_risky_neighborhood,
    dataset=make_synthetic_dataset()
)

assert (
    "SIMILAR_CASES_HIGH_REJECTION_RATE"
    in result_3["flags"]
), (
    "SIMILAR_CASES_HIGH_REJECTION_RATE"
    " flag should be present"
)

assert len(
    result_3["similar_past_cases"]
) > 0, (
    "similar_past_cases should be populated"
)

# Verify each case has required fields.
for case in result_3["similar_past_cases"]:

    assert "loan_id" in case, (
        "Missing loan_id in case"
    )

    assert "similarity_score" in case, (
        "Missing similarity_score in case"
    )

    assert "loan_status" in case, (
        "Missing loan_status in case"
    )

print(f"Risk Score: {result_3['risk_score']}")
print(f"Flags: {result_3['flags']}")
print(
    f"Similar Cases:"
    f" {len(result_3['similar_past_cases'])}"
)

for case in result_3["similar_past_cases"]:
    print(
        f"  Loan {case['loan_id']}"
        f" | Sim: {case['similarity_score']}"
        f" | {case['loan_status']}"
    )

print("✓ PASSED")


# =====================================
# TEST 4: Missing docs + discrepancies
#         + poor credit -> HIGH risk,
#         human_review_required = True
# =====================================

print("\n" + "=" * 60)
print("TEST 4: Multiple signals -> HIGH risk")
print("=" * 60)

record_bad = {
    "loan_id": 996,
    "income_annum": 500000,
    "loan_amount": 2000000,
    "cibil_score": 400
}

result_4 = calculate_risk(
    missing_documents=[
        "payslip",
        "tax_return"
    ],
    payslip_result={
        "difference_percent": 50.0
    },
    tax_result={
        "difference_percent": 60.0
    },
    bank_result={
        "difference_percent": 25.0
    },
    profile_results=[
        {
            "check": "education_consistency",
            "match": False
        }
    ],
    identity_result=make_identity_mismatch(),
    record=record_bad,
    dataset=make_synthetic_dataset()
)

assert result_4["risk_level"] == "HIGH", (
    f"Expected HIGH, got {result_4['risk_level']}"
)

assert result_4["risk_score"] >= 50, (
    f"Expected >= 50, got {result_4['risk_score']}"
)

assert result_4["human_review_required"] is True, (
    "human_review_required should be True"
)

assert "MISSING_DOCUMENTS" in result_4["flags"], (
    "MISSING_DOCUMENTS flag expected"
)

assert "INCOME_DISCREPANCY" in result_4["flags"], (
    "INCOME_DISCREPANCY flag expected"
)

assert "IDENTITY_MISMATCH" in result_4["flags"], (
    "IDENTITY_MISMATCH flag expected"
)

assert "LOW_CIBIL_SCORE" in result_4["flags"], (
    "LOW_CIBIL_SCORE flag expected"
)

print(f"Risk Score: {result_4['risk_score']}")
print(f"Risk Level: {result_4['risk_level']}")
print(
    f"Human Review:"
    f" {result_4['human_review_required']}"
)
print(f"Flags: {result_4['flags']}")
print(f"Findings: {result_4['findings']}")
print("✓ PASSED")


# =====================================
# TEST 5: Score never exceeds 100
# =====================================

print("\n" + "=" * 60)
print("TEST 5: Score capped at 100")
print("=" * 60)

# Stack every possible signal to get
# a raw score well above 100.

record_worst = {
    "loan_id": 995,
    "income_annum": 500000,
    "loan_amount": 2000000,
    "cibil_score": 300
}

result_5 = calculate_risk(
    missing_documents=[
        "payslip",
        "tax_return",
        "bank_statement",
        "kyc"
    ],
    payslip_result={
        "difference_percent": 90.0
    },
    tax_result={
        "difference_percent": 90.0
    },
    bank_result={
        "difference_percent": 90.0
    },
    profile_results=[
        {
            "check": "education_consistency",
            "match": False
        },
        {
            "check": "employment_consistency",
            "match": False
        }
    ],
    identity_result=make_identity_mismatch(),
    record=record_worst,
    dataset=make_synthetic_dataset()
)

# Raw score breakdown:
# 4 missing docs: 4 * 20 = 80
# Payslip mismatch:          25
# Tax mismatch:              25
# Bank mismatch:             20
# 2 profile mismatches: 2*15=30
# Identity mismatch:         30
# CIBIL very_low:            30
# Similar cases:             10
# Total raw:                250
# Capped at:                100

assert result_5["risk_score"] == 100, (
    f"Expected 100, got {result_5['risk_score']}"
)

assert result_5["risk_score"] <= 100, (
    "Score must not exceed 100"
)

print(f"Risk Score: {result_5['risk_score']}")
print(f"Risk Level: {result_5['risk_level']}")
print("✓ PASSED")


# =====================================
# ALL TESTS PASSED
# =====================================

print("\n" + "=" * 60)
print("ALL 5 TESTS PASSED ✓")
print("=" * 60)
