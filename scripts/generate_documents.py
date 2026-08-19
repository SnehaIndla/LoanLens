import pandas as pd
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


# ==========================================
# PATHS
# ==========================================

DATASET = Path(
    "data/loan_dataset/loan_approval_dataset.csv"
)

OUTPUT_DIR = Path(
    "data/documents"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# LOAD DATASET
# ==========================================

df = pd.read_csv(DATASET)

# Remove accidental spaces from column names
df.columns = df.columns.str.strip()

# Select first 10 applicants
applicants = df.head(10).copy()


# ==========================================
# PDF CREATOR
# ==========================================

def create_pdf(path, title, lines):

    c = canvas.Canvas(
        str(path),
        pagesize=A4
    )

    width, height = A4

    y = height - 70

    # Title
    c.setFont(
        "Helvetica-Bold",
        18
    )

    c.drawString(
        50,
        y,
        title
    )

    y -= 45

    # Content
    c.setFont(
        "Helvetica",
        11
    )

    for line in lines:

        c.drawString(
            50,
            y,
            str(line)
        )

        y -= 25

    c.save()


# ==========================================
# GENERATE DOCUMENTS
# ==========================================

for index, row in applicants.iterrows():

    loan_id = int(row["loan_id"])

    folder = (
        OUTPUT_DIR /
        f"loan_{loan_id}"
    )

    folder.mkdir(
        parents=True,
        exist_ok=True
    )


    # --------------------------------------
    # ORIGINAL DATASET VALUES
    # --------------------------------------

    annual_income = float(
        row["income_annum"]
    )

    monthly_income = (
        annual_income / 12
    )

    bank_assets = float(
        row["bank_asset_value"]
    )

    education = row["education"]

    self_employed = row[
        "self_employed"
    ]


    # --------------------------------------
    # BORROWER NAME
    # --------------------------------------

    borrower_name = (
        f"Applicant {loan_id}"
    )


    # ======================================
    # NORMAL VALUES
    # ======================================

    payslip_income = monthly_income

    tax_income = annual_income

    bank_balance = bank_assets


    # ======================================
    # CREATE INTENTIONAL ANOMALIES
    # ======================================

    # Loan 4:
    # Income mismatch

    if loan_id == 4:

        payslip_income = (
            monthly_income * 0.65
        )


    # Loan 5:
    # Tax income mismatch

    if loan_id == 5:

        tax_income = (
            annual_income * 0.55
        )


    # Loan 6:
    # Bank asset mismatch

    if loan_id == 6:

        bank_balance = (
            bank_assets * 0.35
        )


    # Loan 7:
    # Identity mismatch

    kyc_name = borrower_name

    if loan_id == 7:

        kyc_name = (
            f"ApplicantX {loan_id}"
        )


    # ======================================
    # PAYSLIP
    # ======================================

    payslip_path = (
        folder /
        "payslip.pdf"
    )

    create_pdf(
        payslip_path,
        "MONTHLY PAYSLIP",
        [
            f"Borrower: {borrower_name}",

            f"Loan ID: {loan_id}",

            "Employer: ABC Technologies",

            f"Employment Type: "
            f"{'Self Employed' if self_employed == 'Yes' else 'Salaried'}",

            f"Education: {education}",

            f"Monthly Income: "
            f"{payslip_income:,.0f}",

            "Pay Period: August 2026"
        ]
    )


    # ======================================
    # BANK STATEMENT
    # ======================================

    bank_path = (
        folder /
        "bank_statement.pdf"
    )

    create_pdf(
        bank_path,
        "BANK STATEMENT",
        [
            f"Account Holder: {borrower_name}",

            f"Loan ID: {loan_id}",

            f"Bank Asset Balance: "
            f"{bank_balance:,.0f}",

            f"Monthly Salary Credit: "
            f"{monthly_income:,.0f}",

            "Statement Period: "
            "January 2026 - August 2026"
        ]
    )


    # ======================================
    # TAX RETURN
    # ======================================

    tax_path = (
        folder /
        "tax_return.pdf"
    )

    create_pdf(
        tax_path,
        "INCOME TAX RETURN",
        [
            f"Taxpayer: {borrower_name}",

            f"Loan ID: {loan_id}",

            f"Annual Income: "
            f"{tax_income:,.0f}",

            "Assessment Year: 2026",

            "Return Status: Filed"
        ]
    )


    # ======================================
    # KYC
    # ======================================

    kyc_path = (
        folder /
        "kyc.pdf"
    )

    create_pdf(
        kyc_path,
        "KYC DOCUMENT",
        [
            f"Name: {kyc_name}",

            f"Loan ID: {loan_id}",

            f"Education: {education}",

            f"Self Employed: {self_employed}",

            "Identity Verification: Valid"
        ]
    )


    print(
        f"Created documents for loan_id={loan_id}"
    )


print(
    "\nDocument generation completed."
)