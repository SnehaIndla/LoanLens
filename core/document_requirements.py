REQUIRED_DOCUMENTS = {
    "payslip",
    "bank_statement",
    "tax_return",
    "kyc"
}


def check_missing_documents(document_claims):

    submitted_documents = {
        document_type
        for document_type, claims
        in document_claims
    }

    missing_documents = (
        REQUIRED_DOCUMENTS -
        submitted_documents
    )

    return sorted(
        missing_documents
    )