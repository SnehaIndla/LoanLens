import os

try:
    import ollama
except ImportError:
    ollama = None


def generate_ai_summary(
    loan_id,
    risk_result,
    missing_documents,
    payslip_result,
    tax_result,
    bank_result,
    profile_results,
    identity_result
):

    # --------------------------------------------------
    # Build VERIFIED EVIDENCE
    # --------------------------------------------------

    evidence = {
        "loan_id": loan_id,

        "risk": {
            "risk_score": risk_result["risk_score"],
            "risk_level": risk_result["risk_level"],
            "human_review_required": risk_result[
                "human_review_required"
            ]
        },

        "ml_credit_risk": (
            {
                "decision": risk_result["ml_prediction"]["decision"],
                "approval_probability": f"{risk_result['ml_prediction']['approval_probability_pct']}%",
                "top_shap_factors": [
                    f"{f['feature']}: {f['direction']}"
                    for f in risk_result["ml_prediction"].get("top_factors", [])
                ]
            }
            if risk_result.get("ml_prediction")
            else "NOT_AVAILABLE"
        ),

        "findings": list(
            risk_result["findings"]
        ),

        "missing_documents": list(
            missing_documents
        ),

        "payslip": {
            "status": (
                "VERIFIED"
                if payslip_result
                else "MISSING"
            ),
            "difference_percent": (
                payslip_result.get("difference_percent")
                if isinstance(payslip_result, dict)
                else None
            )
        },

        "tax_return": {
            "status": (
                "VERIFIED"
                if tax_result
                else "MISSING"
            ),
            "difference_percent": (
                tax_result.get("difference_percent")
                if isinstance(tax_result, dict)
                else None
            )
        },

        "bank_assets": {
            "dataset_value": (
                bank_result.get("dataset_bank_assets")
                if isinstance(bank_result, dict)
                else None
            ),
            "document_value": (
                bank_result.get("document_bank_assets")
                if isinstance(bank_result, dict)
                else None
            ),
            "difference_percent": (
                bank_result.get("difference_percent")
                if isinstance(bank_result, dict)
                else None
            )
        },

        "profile": [
            {
                "check": result.get("check"),
                "match": result.get("match")
            }
            for result in profile_results
            if isinstance(result, dict)
        ],

        "identity": {
            "status": identity_result.get("status", "unknown") if isinstance(identity_result, dict) else "unknown"
        }
    }


    # --------------------------------------------------
    # Grounded GenAI Prompt
    # --------------------------------------------------

    prompt = f"""
You are LoanLens, an AI explanation assistant for a
loan document verification system.

The VERIFIED EVIDENCE below is the source of truth.

Your ONLY job is to explain the verified result clearly
and professionally to a human loan officer.

IMPORTANT:

The deterministic verification system has already checked
the loan documents.

You must NOT perform verification yourself.

You must NOT create new findings.

You must NOT reinterpret the evidence.

You must ONLY explain what is explicitly present
in the VERIFIED EVIDENCE.

STRICT RULES:

1. Use ONLY information present in VERIFIED EVIDENCE.

2. NEVER invent or infer any finding.

3. NEVER invent numbers, names, dates, percentages,
   financial values, or document information.

4. NEVER perform additional calculations.

5. NEVER calculate absolute differences.

6. NEVER convert monthly income into annual income.

7. NEVER add a currency such as INR, USD, RMB, or EUR.

8. NEVER infer fraud, criminal activity, or intent.

9. NEVER approve or reject the loan.

10. NEVER change the supplied risk score.

11. NEVER change the supplied risk level.

12. NEVER change the supplied human_review_required value.

13. The "findings" list is authoritative.

14. ONLY findings present in the "findings" list
    may be described as issues.

15. If "findings" is empty, state:
    "No significant issues detected."

16. If "missing_documents" is empty, state:
    "No missing documents were identified."

17. If "missing_documents" contains documents,
    mention ONLY those documents as missing.

18. NEVER describe a document as missing if it is not
    present in "missing_documents".

19. NEVER describe a verified document as missing.

20. The "identity.status" value is authoritative.

21. If identity.status is "match", describe the identity
    as consistent or matched.

22. If identity.status is "mismatch", describe the identity
    as inconsistent or mismatched.

23. NEVER mention an identity mismatch when
    identity.status is "match".

24. The profile "match" values are authoritative.

25. NEVER change a profile MATCH into a MISMATCH.

26. NEVER change a profile MISMATCH into a MATCH.

27. If a verification result has a difference_percent of 0.0,
    describe it as consistent or verified.

28. NEVER call a 0.0% difference a mismatch.

29. If a verification result is unavailable,
    state:
    "Not available in the verified evidence."

30. Recommendations must be based ONLY on:
    - the findings list
    - the human_review_required value.

31. Do not recommend investigation of information that
    is not present in the verified evidence.

32. Keep the explanation concise and professional.

33. Do not add information outside the verified evidence.

34. Do not create additional sections.

AUTHORITATIVE FINDINGS:

{risk_result["findings"]}

AUTHORITATIVE MISSING DOCUMENTS:

{missing_documents}

AUTHORITATIVE IDENTITY STATUS:

{identity_result["status"]}

AUTHORITATIVE PROFILE RESULTS:

{profile_results}

VERIFIED EVIDENCE:

{evidence}

Write ONLY a short professional explanation of the
verified result.

Do NOT create headings.

Do NOT create a separate verification report.

Do NOT repeat the entire evidence.

Focus on:
- the risk level
- the official finding(s)
- document completeness
- financial consistency
- identity/profile consistency
- whether human review is required

The explanation must strictly follow the verified evidence.
"""


    # --------------------------------------------------
    # Generate AI Explanation via Ollama Local LLM
    # --------------------------------------------------

    if ollama is None:
        return "[AI Generation Offline: 'ollama' Python package is not installed in the active environment.]"

    model_name = os.getenv("OLLAMA_MODEL", "qwen2:7b")

    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response["message"]["content"]
    except Exception as e:
        return (
            f"[AI Generation Offline: Ollama service or model '{model_name}' not reachable.\n"
            f"Error: {e}\n"
            f"To start Ollama locally, run: ollama serve (and ollama run {model_name})]"
        )