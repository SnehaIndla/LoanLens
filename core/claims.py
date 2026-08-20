import re
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Discrepancy(BaseModel):
    field: str
    declared_value: Any
    extracted_value: Any
    variance_percentage: Optional[float] = None
    severity: SeverityLevel
    document_source: str
    reason: str
    evidence_ref: Optional[str] = None


class ValidationResult(BaseModel):
    case_id: str
    applicant_id: str
    is_consistent: bool
    total_discrepancies: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    discrepancies: List[Discrepancy]
    consistency_score: float  # 0.0 to 100.0
    summary_text: str


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

        match = re.search(
            r"Employer:\s*(.+)",
            text,
            re.IGNORECASE
        )

        if match:
            claims["employer"] = match.group(1).strip()

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