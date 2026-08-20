from claims import ValidationResult, SeverityLevel

def calculate_risk(
    missing_documents=None,
    payslip_result=None,
    tax_result=None,
    bank_result=None,
    profile_results=None,
    identity_result=None,
    validation_result=None
):
    # Support new ValidationResult / dictionary input
    val_res = validation_result
    if val_res is None and missing_documents is not None:
        if isinstance(missing_documents, dict) and "consistency_score" in missing_documents:
            val_res = missing_documents
        elif hasattr(missing_documents, "consistency_score"):
            val_res = missing_documents

    if val_res is not None:
        if hasattr(val_res, "consistency_score"):
            score = 100.0 - val_res.consistency_score
            discrepancies = val_res.discrepancies
            critical_count = val_res.critical_count
            high_count = val_res.high_count
        else:
            score = 100.0 - val_res.get("consistency_score", 100.0)
            discrepancies = val_res.get("discrepancies", [])
            critical_count = val_res.get("critical_count", 0)
            high_count = val_res.get("high_count", 0)

        findings = []
        for d in discrepancies:
            if hasattr(d, "reason"):
                findings.append(f"{d.field}: {d.reason}")
            else:
                findings.append(f"{d.get('field')}: {d.get('reason')}")

        score = min(max(score, 0.0), 100.0)

        # Risk level mapping:
        # HIGH if score >= 50 or has CRITICAL discrepancies
        # MEDIUM if score >= 20 or has HIGH/MEDIUM/etc discrepancies
        if score >= 50.0 or critical_count > 0:
            risk_level = "HIGH"
        elif score >= 20.0 or high_count > 0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        human_review = (len(discrepancies) > 0 or score > 0.0)

        return {
            "risk_score": int(score),
            "risk_level": risk_level,
            "human_review_required": human_review,
            "findings": findings
        }

    # ==================================================
    # Old Fallback Signature Logic
    # ==================================================
    score = 0
    findings = []

    # Missing documents
    if missing_documents:
        for document in missing_documents:
            score += 20
            findings.append(f"Missing document: {document}")

    # Payslip income
    if payslip_result:
        difference = payslip_result.get("difference_percent", 0.0)
        if difference > 10:
            score += 25
            findings.append("Payslip income mismatch")

    # Tax return
    if tax_result:
        difference = tax_result.get("difference_percent", 0.0)
        if difference > 10:
            score += 25
            findings.append("Tax return income mismatch")

    # Bank assets
    if bank_result:
        difference = bank_result.get("difference_percent", 0.0)
        if difference > 10:
            score += 20
            findings.append("Bank asset mismatch")

    # Education / employment
    if profile_results:
        for result in profile_results:
            if not result.get("match", True):
                score += 15
                findings.append(result.get("check", "profile") + " mismatch")

    # Identity
    if identity_result and identity_result.get("status") == "mismatch":
        score += 30
        findings.append("Identity mismatch across documents")

    score = min(score, 100)

    if score >= 50:
        risk_level = "HIGH"
    elif score >= 20:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    human_review = (score > 0)

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "human_review_required": human_review,
        "findings": findings
    }