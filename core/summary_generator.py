def generate_summary(
    loan_id,
    risk_result,
    missing_documents,
    payslip_result,
    tax_result,
    bank_result,
    profile_results,
    identity_result
):

    risk_score = risk_result["risk_score"]

    risk_level = risk_result["risk_level"]

    human_review = (
        risk_result[
            "human_review_required"
        ]
    )

    findings = risk_result["findings"]


    # =================================
    # Header
    # =================================

    summary = []

    summary.append(
        "LOANLENS LOAN PROCESSING SUMMARY"
    )

    summary.append(
        "=" * 45
    )

    summary.append(
        f"Loan ID: {loan_id}"
    )

    summary.append(
        f"Risk Score: {risk_score}/100"
    )

    summary.append(
        f"Risk Level: {risk_level}"
    )

    summary.append(
        "Human Review Required: "
        + (
            "YES"
            if human_review
            else "NO"
        )
    )


    # =================================
    # Document completeness
    # =================================

    summary.append(
        "\nDOCUMENT COMPLETENESS"
    )

    if missing_documents:

        summary.append(
            "Missing: "
            + ", ".join(
                missing_documents
            )
        )

    else:

        summary.append(
            "All required documents submitted."
        )


    # =================================
    # Findings
    # =================================

    summary.append(
        "\nVERIFICATION FINDINGS"
    )

    if not findings:

        summary.append(
            "No significant inconsistencies detected."
        )

    else:

        for finding in findings:

            summary.append(
                "• " + finding
            )


    # =================================
    # Detailed explanation
    # =================================

    summary.append(
        "\nEXPLANATION"
    )


    # Payslip
    if payslip_result:

        difference = payslip_result[
            "difference_percent"
        ]

        if difference > 10:

            summary.append(
                f"Payslip income differs from "
                f"the reference income by "
                f"{difference}%."
            )

        else:

            summary.append(
                "Payslip income is consistent "
                "with the reference income."
            )


    # Tax return
    if tax_result:

        difference = tax_result[
            "difference_percent"
        ]

        if difference > 10:

            summary.append(
                f"Tax return income differs "
                f"from the reference income by "
                f"{difference}%."
            )

        else:

            summary.append(
                "Tax return income is consistent "
                "with the reference income."
            )


    # Bank assets
    if bank_result:

        difference = bank_result[
            "difference_percent"
        ]

        if difference > 10:

            summary.append(
                f"Bank asset information differs "
                f"from the reference value by "
                f"{difference}%."
            )

        else:

            summary.append(
                "Bank asset information is "
                "consistent."
            )


    # Identity
    if identity_result["status"] == "mismatch":

        summary.append(
            "Identity information is inconsistent "
            "across submitted documents."
        )

    elif identity_result["status"] == "match":

        summary.append(
            "Identity information is consistent "
            "across submitted documents."
        )


    # =================================
    # Recommendation
    # =================================

    summary.append(
        "\nRECOMMENDATION"
    )

    if risk_level == "HIGH":

        summary.append(
            "Do not automatically approve. "
            "Escalate the application for "
            "detailed human investigation."
        )

    elif risk_level == "MEDIUM":

        summary.append(
            "Route the application to a human "
            "reviewer before final processing."
        )

    else:

        summary.append(
            "No significant document issues "
            "detected. Application may proceed "
            "to the next processing stage."
        )


    return "\n".join(summary)