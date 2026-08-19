def classify_document(text, filename=""):
    """
    Identify the type of financial document.
    """

    text_lower = text.lower()
    filename_lower = filename.lower()

    content = text_lower + " " + filename_lower

    # Payslip
    if (
        "monthly payslip" in content
        or "monthly income" in content
        or "pay period" in content
    ):
        return "payslip"

    # Bank statement
    if (
        "bank statement" in content
        or "bank asset balance" in content
        or "salary credit" in content
    ):
        return "bank_statement"

    # Tax return
    if (
        "income tax return" in content
        or "annual income" in content
        or "assessment year" in content
    ):
        return "tax_return"

    # KYC
    if (
        "kyc document" in content
        or "identity verification" in content
    ):
        return "kyc"

    return "unknown"