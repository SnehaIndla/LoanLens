import pandas as pd


DATASET = "data/loan_dataset/loan_approval_dataset.csv"


def load_dataset():

    df = pd.read_csv(DATASET)

    # Remove unwanted spaces from column names
    df.columns = df.columns.str.strip()

    return df


def get_loan_record(loan_id):

    df = load_dataset()

    record = df[
        df["loan_id"] == loan_id
    ]

    if record.empty:
        return None

    return record.iloc[0].to_dict()


def compare_income(
    dataset_record,
    document_claims
):

    dataset_income = float(
        dataset_record["income_annum"]
    )

    document_income = document_claims.get(
        "annual_income"
    )

    monthly_income = document_claims.get(
        "monthly_income"
    )

    # If tax return is available,
    # use it as annual income.
    if document_income is not None:

        difference = abs(
            dataset_income - document_income
        )

        percentage = (
            difference / dataset_income
        ) * 100

        return {
            "check": "income_consistency",
            "dataset_income": dataset_income,
            "document_income": document_income,
            "difference": difference,
            "difference_percent": round(
                percentage,
                2
            )
        }

    # Otherwise convert payslip
    # monthly income into annual income.
    if monthly_income is not None:

        annualized_income = (
            monthly_income * 12
        )

        difference = abs(
            dataset_income -
            annualized_income
        )

        percentage = (
            difference / dataset_income
        ) * 100

        return {
            "check": "income_consistency",
            "dataset_income": dataset_income,
            "document_income": annualized_income,
            "difference": difference,
            "difference_percent": round(
                percentage,
                2
            )
        }

    return None


def compare_bank_assets(
    dataset_record,
    document_claims
):

    dataset_bank_assets = float(
        dataset_record["bank_asset_value"]
    )

    document_bank_assets = (
        document_claims.get(
            "bank_asset_value"
        )
    )

    if document_bank_assets is None:
        return None

    difference = abs(
        dataset_bank_assets -
        document_bank_assets
    )

    percentage = (
        difference /
        max(dataset_bank_assets, 1)
    ) * 100

    return {
        "check": "bank_asset_consistency",
        "dataset_bank_assets":
            dataset_bank_assets,
        "document_bank_assets":
            document_bank_assets,
        "difference":
            difference,
        "difference_percent":
            round(percentage, 2)
    }


def compare_profile(
    dataset_record,
    document_claims
):

    results = []

    # ----------------------------
    # Education
    # ----------------------------

    dataset_education = str(
        dataset_record["education"]
    ).strip().lower()

    document_education = (
        document_claims.get(
            "education"
        )
    )

    if document_education:

        document_education = (
            document_education
            .strip()
            .lower()
        )

        results.append({
            "check":
                "education_consistency",

            "dataset_value":
                dataset_education,

            "document_value":
                document_education,

            "match":
                dataset_education ==
                document_education
        })


    # ----------------------------
    # Self-employed
    # ----------------------------

    dataset_employment = str(
        dataset_record["self_employed"]
    ).strip().lower()

    document_employment = (
        document_claims.get(
            "self_employed"
        )
    )

    if document_employment:

        document_employment = (
            document_employment
            .strip()
            .lower()
        )

        results.append({
            "check":
                "employment_consistency",

            "dataset_value":
                dataset_employment,

            "document_value":
                document_employment,

            "match":
                dataset_employment ==
                document_employment
        })


    return results
def compare_document_identity(document_claims_list):
    """
    Compare borrower names across submitted documents.
    """

    names = []

    for document_type, claims in document_claims_list:

        name = claims.get("borrower_name")

        if name:
            names.append(
                {
                    "document": document_type,
                    "name": name.strip().lower()
                }
            )

    if len(names) < 2:
        return {
            "check": "identity_consistency",
            "status": "insufficient_evidence"
        }

    unique_names = set(
        item["name"]
        for item in names
    )

    if len(unique_names) == 1:

        return {
            "check": "identity_consistency",
            "status": "match",
            "names": names
        }

    return {
        "check": "identity_consistency",
        "status": "mismatch",
        "names": names
    }
def check_payslip_income(dataset_record, claims):

    dataset_income = float(
        dataset_record["income_annum"]
    )

    monthly_income = claims.get(
        "monthly_income"
    )

    if monthly_income is None:
        return None

    annualized_income = (
        monthly_income * 12
    )

    difference = abs(
        dataset_income - annualized_income
    )

    percentage = (
        difference /
        max(dataset_income, 1)
    ) * 100

    return {
        "check": "payslip_income",
        "dataset_income": dataset_income,
        "payslip_annualized_income":
            annualized_income,
        "difference_percent":
            round(percentage, 2)
    }


def check_tax_income(dataset_record, claims):

    dataset_income = float(
        dataset_record["income_annum"]
    )

    tax_income = claims.get(
        "annual_income"
    )

    if tax_income is None:
        return None

    difference = abs(
        dataset_income - tax_income
    )

    percentage = (
        difference /
        max(dataset_income, 1)
    ) * 100

    return {
        "check": "tax_return_income",
        "dataset_income": dataset_income,
        "tax_return_income":
            tax_income,
        "difference_percent":
            round(percentage, 2)
    }