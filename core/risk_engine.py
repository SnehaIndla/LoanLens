def calculate_risk(
    missing_documents,
    payslip_result,
    tax_result,
    bank_result,
    profile_results,
    identity_result
):

    score = 0

    findings = []


    # =================================
    # Missing documents
    # =================================

    for document in missing_documents:

        score += 20

        findings.append(
            f"Missing document: {document}"
        )


    # =================================
    # Payslip income
    # =================================

    if payslip_result:

        difference = payslip_result[
            "difference_percent"
        ]

        if difference > 10:

            score += 25

            findings.append(
                "Payslip income mismatch"
            )


    # =================================
    # Tax return
    # =================================

    if tax_result:

        difference = tax_result[
            "difference_percent"
        ]

        if difference > 10:

            score += 25

            findings.append(
                "Tax return income mismatch"
            )


    # =================================
    # Bank assets
    # =================================

    if bank_result:

        difference = bank_result[
            "difference_percent"
        ]

        if difference > 10:

            score += 20

            findings.append(
                "Bank asset mismatch"
            )


    # =================================
    # Education / employment
    # =================================

    for result in profile_results:

        if not result["match"]:

            score += 15

            findings.append(
                result["check"]
                + " mismatch"
            )


    # =================================
    # Identity
    # =================================

    if identity_result[
        "status"
    ] == "mismatch":

        score += 30

        findings.append(
            "Identity mismatch across documents"
        )


    # =================================
    # Limit score
    # =================================

    score = min(
        score,
        100
    )


    # =================================
    # Risk level
    # =================================

    if score >= 50:

        risk_level = "HIGH"

    elif score >= 20:

        risk_level = "MEDIUM"

    else:

        risk_level = "LOW"


    # =================================
    # Human review
    # =================================

    human_review = (
        score > 0
    )


    return {
        "risk_score": score,
        "risk_level": risk_level,
        "human_review_required":
            human_review,
        "findings": findings
    }