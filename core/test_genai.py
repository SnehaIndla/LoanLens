from genai_agent import generate_ai_summary


risk_result = {
    "risk_score": 20,
    "risk_level": "MEDIUM",
    "human_review_required": True,
    "findings": [
        "Bank asset mismatch"
    ]
}


missing_documents = []


payslip_result = {
    "difference_percent": 0.0
}


tax_result = {
    "difference_percent": 0.0
}


bank_result = {
    "difference_percent": 65.0
}


profile_results = [
    {
        "check": "education_consistency",
        "match": True
    },
    {
        "check": "employment_consistency",
        "match": True
    }
]


identity_result = {
    "status": "match"
}


summary = generate_ai_summary(
    loan_id=6,
    risk_result=risk_result,
    missing_documents=missing_documents,
    payslip_result=payslip_result,
    tax_result=tax_result,
    bank_result=bank_result,
    profile_results=profile_results,
    identity_result=identity_result
)


print("\n")
print("=" * 60)
print("LOANLENS AI SUMMARY")
print("=" * 60)

print(summary)