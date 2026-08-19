import re


def extract_claims(text, document_type):
    """
    Extract structured fields from a document.
    """

    claims = {}

    # -----------------------------
    # Loan ID
    # -----------------------------

    match = re.search(
        r"Loan ID:\s*(\d+)",
        text,
        re.IGNORECASE
    )

    if match:
        claims["loan_id"] = int(
            match.group(1)
        )

    # -----------------------------
    # Borrower / Account Holder
    # -----------------------------

    match = re.search(
        r"(?:Borrower|Account Holder|Taxpayer|Name):\s*(.+)",
        text,
        re.IGNORECASE
    )

    if match:
        claims["borrower_name"] = (
            match.group(1).strip()
        )

    # -----------------------------
    # Payslip
    # -----------------------------

    if document_type == "payslip":

        match = re.search(
            r"Monthly Income:\s*([\d,]+)",
            text,
            re.IGNORECASE
        )

        if match:
            claims["monthly_income"] = float(
                match.group(1).replace(",", "")
            )

    # -----------------------------
    # Bank Statement
    # -----------------------------

    elif document_type == "bank_statement":

        match = re.search(
            r"Bank Asset Balance:\s*([\d,]+)",
            text,
            re.IGNORECASE
        )

        if match:
            claims["bank_asset_value"] = float(
                match.group(1).replace(",", "")
            )

        match = re.search(
            r"Monthly Salary Credit:\s*([\d,]+)",
            text,
            re.IGNORECASE
        )

        if match:
            claims["monthly_salary_credit"] = float(
                match.group(1).replace(",", "")
            )

    # -----------------------------
    # Tax Return
    # -----------------------------

    elif document_type == "tax_return":

        match = re.search(
            r"Annual Income:\s*([\d,]+)",
            text,
            re.IGNORECASE
        )

        if match:
            claims["annual_income"] = float(
                match.group(1).replace(",", "")
            )

    # -----------------------------
    # KYC
    # -----------------------------

    elif document_type == "kyc":

        match = re.search(
            r"Education:\s*(.+)",
            text,
            re.IGNORECASE
        )

        if match:
            claims["education"] = (
                match.group(1).strip()
            )

        match = re.search(
            r"Self Employed:\s*(.+)",
            text,
            re.IGNORECASE
        )

        if match:
            claims["self_employed"] = (
                match.group(1).strip()
            )

    return claims