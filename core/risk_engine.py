try:
    from ml_risk_model import predict_approval
except ImportError:
    try:
        from core.ml_risk_model import predict_approval
    except ImportError:
        predict_approval = None


def calculate_risk(
    verification_result: dict,
    applicant_features: dict = None
) -> dict:
    """
    Risk Engine for LoanLens Live Intake.
    Combines deterministic verification flags (missing docs, extraction failures, identity, income mismatch,
    CIBIL score bands, loan eligibility) with 5-feature LightGBM ML credit scoring.
    """
    if isinstance(verification_result, dict):
        missing_documents = verification_result.get("missing_documents", [])
        extraction_failures = verification_result.get("extraction_failures", [])
        identity_result = verification_result.get("identity_result", {})
        income_result = verification_result.get("income_result", {})
        cibil_check = verification_result.get("cibil_check", {})
        eligibility_check = verification_result.get("eligibility_check", {})
        if applicant_features is None:
            applicant_features = verification_result.get("applicant_features")
    else:
        missing_documents = verification_result
        extraction_failures = []
        identity_result = {}
        income_result = {}
        cibil_check = {}
        eligibility_check = {}

    score = 0
    findings = []
    hard_flags = []
    ml_prediction = None

    # =================================
    # 1. DETERMINISTIC HARD FLAGS & UNDERWRITING RULES
    # =================================

    # Missing documents
    for doc in missing_documents:
        score += 25
        flag = f"Missing required document: {doc}"
        findings.append(flag)
        hard_flags.append(flag)

    # Extraction failures
    for failure in extraction_failures:
        score += 20
        flag = f"Extraction Failed: {failure}"
        findings.append(flag)
        hard_flags.append(flag)

    # Identity mismatch
    if identity_result and identity_result.get("status") == "mismatch":
        score += 30
        flag = "Identity Mismatch: Borrower name differs across uploaded documents"
        findings.append(flag)
        hard_flags.append(flag)

    # Income mismatch (>15%)
    if income_result and income_result.get("mismatch"):
        score += 25
        pct = income_result.get("difference_percent", 0.0)
        flag = f"Income Mismatch: Payslip annualized salary differs from Tax Return by {pct}%"
        findings.append(flag)
        hard_flags.append(flag)

    # CIBIL Score Threshold Rules
    if cibil_check and cibil_check.get("flag"):
        c_flag = cibil_check["flag"]
        c_msg = cibil_check.get("message", "CIBIL Score Warning")
        if c_flag == "CIBIL_TOO_LOW":
            score += 35
        elif c_flag == "CIBIL_BORDERLINE":
            score += 20
        findings.append(c_msg)
        hard_flags.append(c_msg)

    # Loan Amount Eligibility Rules (5x Income)
    if eligibility_check and not eligibility_check.get("eligible", True):
        e_msg = eligibility_check.get("message", "Loan amount exceeds eligibility limit")
        score += 25
        findings.append(e_msg)
        hard_flags.append(e_msg)

    # =================================
    # 2. 5-FEATURE ML CREDIT RISK MODEL
    # =================================
    if applicant_features and predict_approval is not None:
        try:
            ml_prediction = predict_approval(applicant_features)
            ml_score = int(ml_prediction["risk_score"])
            score = max(score, ml_score)
            
            if ml_prediction["decision"] == "REJECT":
                findings.append(f"ML Credit Model: High default risk ({ml_prediction['approval_probability_pct']}% approval probability)")
            elif ml_prediction["decision"] == "MANUAL_REVIEW":
                findings.append(f"ML Credit Model: Marginal creditworthiness ({ml_prediction['approval_probability_pct']}% approval probability)")
        except Exception as e:
            findings.append(f"ML Prediction Warning: {e}")

    # Limit score 0-100
    score = min(max(score, 0), 100)

    # Risk level assignment
    if score >= 50:
        risk_level = "HIGH"
    elif score >= 20:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Decision policy
    if hard_flags:
        decision = "MANUAL_REVIEW"
        human_review_required = True
    elif ml_prediction:
        decision = ml_prediction.get("decision", "MANUAL_REVIEW")
        human_review_required = (decision != "APPROVE") or (score > 0)
    else:
        decision = "MANUAL_REVIEW" if score > 0 else "APPROVE"
        human_review_required = (score > 0)

    return {
        "decision": decision,
        "risk_score": score,
        "risk_level": risk_level,
        "human_review_required": human_review_required,
        "findings": findings,
        "hard_flags": hard_flags,
        "ml_prediction": ml_prediction
    }