import pandas as pd
import difflib
from datetime import datetime
from typing import List, Optional, Any
from claims import SeverityLevel, Discrepancy, ValidationResult


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


class CrossValidationAgent:
    def __init__(self):
        pass

    def validate_identity(self, declared_name: str, extracted_id_data: dict) -> Optional[Discrepancy]:
        extracted_name = (
            extracted_id_data.get("full_name")
            or extracted_id_data.get("name_on_document")
            or extracted_id_data.get("borrower_name")
            or extracted_id_data.get("Name")
        )
        if not declared_name or not extracted_name:
            return None

        d_name = str(declared_name).strip()
        e_name = str(extracted_name).strip()

        similarity = difflib.SequenceMatcher(None, d_name.lower(), e_name.lower()).ratio()

        if similarity >= 0.95:
            return None

        variance = round((1.0 - similarity) * 100, 2)

        if similarity < 0.70:
            severity = SeverityLevel.CRITICAL
            reason = f"Identity Mismatch: Declared name '{d_name}' and ID document name '{e_name}' similarity score is {similarity:.2f} (< 0.70)."
        elif similarity < 0.80:
            severity = SeverityLevel.HIGH
            reason = f"Identity Variation: Declared name '{d_name}' and ID document name '{e_name}' similarity score is {similarity:.2f} (< 0.80)."
        else:
            severity = SeverityLevel.LOW
            reason = f"Minor Name Variation: Declared name '{d_name}' and ID document name '{e_name}' similarity score is {similarity:.2f} (between 0.80 and 0.95)."

        return Discrepancy(
            field="applicant_name",
            declared_value=d_name,
            extracted_value=e_name,
            variance_percentage=variance,
            severity=severity,
            document_source="ID Proof",
            reason=reason,
            evidence_ref="Identity Check"
        )

    def validate_income(self, declared_annual_income: float, extracted_docs: dict) -> List[Discrepancy]:
        discrepancies = []
        if declared_annual_income is None:
            return discrepancies

        monthly_net_pay = extracted_docs.get("monthly_net_pay")
        monthly_gross_pay = extracted_docs.get("monthly_gross_pay")
        annual_salary = extracted_docs.get("annual_salary")
        total_credited_income = extracted_docs.get("total_credited_income")
        monthly_income = extracted_docs.get("monthly_income")
        monthly_salary_credit = extracted_docs.get("monthly_salary_credit")
        annual_income_tax = extracted_docs.get("annual_income")

        doc_incomes = []
        if annual_salary is not None:
            doc_incomes.append(("annual_salary", float(annual_salary), "Employment Letter"))
        if annual_income_tax is not None:
            doc_incomes.append(("annual_income", float(annual_income_tax), "Tax Return"))
        if monthly_net_pay is not None:
            doc_incomes.append(("monthly_net_pay * 12", float(monthly_net_pay) * 12, "Payslip"))
        if monthly_gross_pay is not None:
            doc_incomes.append(("monthly_gross_pay * 12", float(monthly_gross_pay) * 12, "Payslip"))
        if monthly_income is not None:
            doc_incomes.append(("monthly_income * 12", float(monthly_income) * 12, "Payslip"))
        if monthly_salary_credit is not None:
            doc_incomes.append(("monthly_salary_credit * 12", float(monthly_salary_credit) * 12, "Bank Statement"))
        if total_credited_income is not None:
            doc_incomes.append(("total_credited_income", float(total_credited_income), "Bank Statement"))

        has_income_transactions = len(doc_incomes) > 0 and any(val > 0 for _, val, _ in doc_incomes)
        employer_name = extracted_docs.get("employer") or extracted_docs.get("employer_name")
        is_self_employed = str(extracted_docs.get("self_employed")).lower() in ("yes", "y", "true")
        employer_exists = (employer_name is not None and str(employer_name).strip() != "" and str(employer_name).lower() != "unknown") or is_self_employed

        if declared_annual_income > 0 and (not has_income_transactions or not employer_exists):
            reason_parts = []
            if not has_income_transactions:
                reason_parts.append("salary transactions are absent or document income is zero")
            if not employer_exists:
                reason_parts.append("employer name is missing or unverifiable")
            reason = "Unverifiable Income Source: Declared income > 0, but " + " and ".join(reason_parts) + "."
            discrepancies.append(Discrepancy(
                field="person_income",
                declared_value=declared_annual_income,
                extracted_value=0.0 if not doc_incomes else doc_incomes[0][1],
                variance_percentage=100.0,
                severity=SeverityLevel.CRITICAL,
                document_source="Payslip / Bank Statement",
                reason=reason,
                evidence_ref="Income Verification"
            ))
            return discrepancies

        for field_name, doc_income, doc_source in doc_incomes:
            if doc_income == 0:
                continue
            variance_pct = ((declared_annual_income - doc_income) / doc_income) * 100

            if declared_annual_income > doc_income:
                if variance_pct > 15.0:
                    discrepancies.append(Discrepancy(
                        field="person_income",
                        declared_value=declared_annual_income,
                        extracted_value=doc_income,
                        variance_percentage=round(variance_pct, 2),
                        severity=SeverityLevel.HIGH,
                        document_source=doc_source,
                        reason=f"Significant Income Over-declaration: Declared income ({declared_annual_income:,.2f}) is > 15% higher than document income ({doc_income:,.2f}) from {doc_source}.",
                        evidence_ref=f"{doc_source} ({field_name})"
                    ))
                elif variance_pct > 5.0:
                    discrepancies.append(Discrepancy(
                        field="person_income",
                        declared_value=declared_annual_income,
                        extracted_value=doc_income,
                        variance_percentage=round(variance_pct, 2),
                        severity=SeverityLevel.MEDIUM,
                        document_source=doc_source,
                        reason=f"Moderate Income Variance: Declared income ({declared_annual_income:,.2f}) is between 5% and 15% higher than document income ({doc_income:,.2f}) from {doc_source}.",
                        evidence_ref=f"{doc_source} ({field_name})"
                    ))
            elif declared_annual_income < doc_income:
                discrepancies.append(Discrepancy(
                    field="person_income",
                    declared_value=declared_annual_income,
                    extracted_value=doc_income,
                    variance_percentage=round(variance_pct, 2),
                    severity=SeverityLevel.LOW,
                    document_source=doc_source,
                    reason=f"Minor Under-declaration: Declared income ({declared_annual_income:,.2f}) is lower than document income ({doc_income:,.2f}) from {doc_source} (favorable variance).",
                    evidence_ref=f"{doc_source} ({field_name})"
                ))

        return discrepancies

    def validate_employment_history(self, declared_emp_length: float, extracted_docs: dict) -> Optional[Discrepancy]:
        if declared_emp_length is None:
            return None

        tenure_months = extracted_docs.get("tenure_months")
        years_at_company = extracted_docs.get("years_at_company")
        start_date_str = extracted_docs.get("employment_start_date") or extracted_docs.get("start_date")

        doc_tenure_years = None

        if years_at_company is not None:
            doc_tenure_years = float(years_at_company)
        elif tenure_months is not None:
            doc_tenure_years = float(tenure_months) / 12.0
        elif start_date_str is not None:
            current_date = datetime(2026, 8, 20)
            parsed_date = None
            for fmt in ("%Y-%m-%d", "%Y-%m", "%B %Y", "%b %Y", "%d-%m-%Y"):
                try:
                    parsed_date = datetime.strptime(str(start_date_str).strip(), fmt)
                    break
                except ValueError:
                    continue
            if parsed_date:
                delta = current_date - parsed_date
                doc_tenure_years = delta.days / 365.25

        if doc_tenure_years is None:
            return None

        diff_years = declared_emp_length - doc_tenure_years
        diff_days = diff_years * 365.25

        if diff_years <= 0.0:
            return None

        if diff_years > 2.0:
            severity = SeverityLevel.HIGH
            reason = f"Employment Length Exaggeration: Declared employment length ({declared_emp_length:.1f} years) exceeds verified document tenure ({doc_tenure_years:.2f} years) by > 2.0 years."
        elif diff_years > 0.5:
            severity = SeverityLevel.MEDIUM
            reason = f"Minor Employment Tenure Variance: Declared employment length ({declared_emp_length:.1f} years) is higher than verified document tenure ({doc_tenure_years:.2f} years) by {diff_years:.2f} years."
        else:
            severity = SeverityLevel.LOW
            if diff_days <= 15.0:
                reason = f"Minor Date Rounding: Employment length discrepancy ({diff_days:.1f} days) is within standard payroll cycle cutoff (<= 15 days)."
            else:
                reason = f"Minor Employment Tenure Variance: Declared employment length ({declared_emp_length:.1f} years) is slightly higher than verified document tenure ({doc_tenure_years:.2f} years)."

        return Discrepancy(
            field="person_emp_length",
            declared_value=declared_emp_length,
            extracted_value=round(doc_tenure_years, 2),
            variance_percentage=round(diff_years, 2),
            severity=severity,
            document_source="Payslip / Employment Letter",
            reason=reason,
            evidence_ref="Employment Tenure Check"
        )

    def validate_credit_profile(self, declared_defaults: str, declared_cred_len: float, credit_report: dict) -> List[Discrepancy]:
        discrepancies = []

        if declared_defaults is not None:
            hist_defaults = credit_report.get("historical_defaults_count") or credit_report.get("defaults")
            delinq_flag = credit_report.get("delinquency_flag")

            has_default_record = False
            if hist_defaults is not None and float(hist_defaults) > 0:
                has_default_record = True
            if delinq_flag is True or str(delinq_flag).lower() == "true":
                has_default_record = True

            if str(declared_defaults).upper().strip() == "N" and has_default_record:
                discrepancies.append(Discrepancy(
                    field="cb_person_default_on_file",
                    declared_value=declared_defaults,
                    extracted_value="Y" if hist_defaults else "delinquency_flag=True",
                    severity=SeverityLevel.CRITICAL,
                    document_source="Credit Report",
                    reason=f"Prior Default Concealment: Declared default on file is 'N', but credit report shows active/historical defaults (count={hist_defaults}, delinquency={delinq_flag}).",
                    evidence_ref="Bureau Default Record"
                ))

        if declared_cred_len is not None:
            cred_len_doc = credit_report.get("oldest_trade_line_years") or credit_report.get("credit_history_duration")
            if cred_len_doc is not None:
                cred_len_doc = float(cred_len_doc)
                diff = abs(declared_cred_len - cred_len_doc)
                if diff > 3.0:
                    discrepancies.append(Discrepancy(
                        field="cb_person_cred_hist_length",
                        declared_value=declared_cred_len,
                        extracted_value=cred_len_doc,
                        variance_percentage=round(diff, 2),
                        severity=SeverityLevel.HIGH,
                        reason=f"Credit History Length Variance: Declared credit history length ({declared_cred_len:.1f} years) differs from bureau record ({cred_len_doc:.1f} years) by > 3.0 years.",
                        document_source="Credit Report",
                        evidence_ref="Oldest Trade Line"
                    ))
                elif diff > 0.0:
                    discrepancies.append(Discrepancy(
                        field="cb_person_cred_hist_length",
                        declared_value=declared_cred_len,
                        extracted_value=cred_len_doc,
                        variance_percentage=round(diff, 2),
                        severity=SeverityLevel.LOW,
                        reason=f"Minor Credit History Length Variance: Declared credit history length ({declared_cred_len:.1f} years) differs from bureau record ({cred_len_doc:.1f} years) by {diff:.1f} years.",
                        document_source="Credit Report",
                        evidence_ref="Oldest Trade Line"
                    ))

        return discrepancies

    def calculate_consistency_score(self, discrepancies: List[Discrepancy]) -> float:
        score = 100.0
        for disc in discrepancies:
            if disc.severity == SeverityLevel.CRITICAL:
                score -= 40.0
            elif disc.severity == SeverityLevel.HIGH:
                score -= 20.0
            elif disc.severity == SeverityLevel.MEDIUM:
                score -= 10.0
            elif disc.severity == SeverityLevel.LOW:
                score -= 2.0
        return max(0.0, score)

    def cross_check_fields(self, declared_record: dict, extracted_fields: dict) -> ValidationResult:
        discrepancies = []

        declared_name = declared_record.get("applicant_name") or declared_record.get("borrower_name")
        if not declared_name and "loan_id" in declared_record:
            declared_name = f"Applicant {declared_record['loan_id']}"

        identity_disc = self.validate_identity(declared_name, extracted_fields)
        if identity_disc:
            discrepancies.append(identity_disc)

        declared_income = declared_record.get("person_income") or declared_record.get("income_annum")
        if declared_income is not None:
            income_discs = self.validate_income(float(declared_income), extracted_fields)
            discrepancies.extend(income_discs)

        declared_emp_len = declared_record.get("person_emp_length") or declared_record.get("employment_length")
        if declared_emp_len is not None:
            emp_disc = self.validate_employment_history(float(declared_emp_len), extracted_fields)
            if emp_disc:
                discrepancies.append(emp_disc)

        declared_defaults = declared_record.get("cb_person_default_on_file") or declared_record.get("default_on_file")
        declared_cred_len = declared_record.get("cb_person_cred_hist_length") or declared_record.get("credit_history_length")
        credit_discs = self.validate_credit_profile(declared_defaults, declared_cred_len, extracted_fields)
        discrepancies.extend(credit_discs)

        declared_age = declared_record.get("person_age") or declared_record.get("age")
        dob_val = extracted_fields.get("dob")
        calculated_age = extracted_fields.get("calculated_age")

        if declared_age is not None:
            declared_age = float(declared_age)
            doc_age = None
            if calculated_age is not None:
                doc_age = float(calculated_age)
            elif dob_val is not None:
                current_date = datetime(2026, 8, 20)
                parsed_dob = None
                for fmt in ("%Y-%m-%d", "%Y-%m", "%B %Y", "%d-%m-%Y"):
                    try:
                        parsed_dob = datetime.strptime(str(dob_val).strip(), fmt)
                        break
                    except ValueError:
                        continue
                if parsed_dob:
                    doc_age = current_date.year - parsed_dob.year - ((current_date.month, current_date.day) < (parsed_dob.month, parsed_dob.day))
            
            if doc_age is not None:
                age_diff = abs(declared_age - doc_age)
                if age_diff > 1.0:
                    discrepancies.append(Discrepancy(
                        field="person_age",
                        declared_value=declared_age,
                        extracted_value=doc_age,
                        variance_percentage=round(age_diff, 2),
                        severity=SeverityLevel.HIGH,
                        document_source="ID Proof",
                        reason=f"Age Discrepancy: Declared age ({declared_age:.0f}) differs from ID document DOB calculated age ({doc_age:.0f}) by > 1 year.",
                        evidence_ref="DOB Calculation"
                    ))
                elif age_diff > 0.0:
                    discrepancies.append(Discrepancy(
                        field="person_age",
                        declared_value=declared_age,
                        extracted_value=doc_age,
                        variance_percentage=round(age_diff, 2),
                        severity=SeverityLevel.LOW,
                        document_source="ID Proof",
                        reason=f"Minor Age Discrepancy: Declared age ({declared_age:.0f}) differs from ID document DOB calculated age ({doc_age:.0f}) by {age_diff:.0f} year.",
                        evidence_ref="DOB Calculation"
                    ))

        declared_home = declared_record.get("person_home_ownership") or declared_record.get("home_ownership")
        if declared_home is not None:
            rent_debits = extracted_fields.get("rent_debits")
            if str(declared_home).upper().strip() == "RENT" and (rent_debits is False or rent_debits == 0 or rent_debits is None):
                discrepancies.append(Discrepancy(
                    field="person_home_ownership",
                    declared_value=declared_home,
                    extracted_value="Missing rent debits",
                    severity=SeverityLevel.MEDIUM,
                    document_source="Bank Statement",
                    reason="Home Ownership Ambiguity: Declared RENT but recurring rent debit transactions are missing from bank statements.",
                    evidence_ref="Transaction Check"
                ))

        critical_count = sum(1 for d in discrepancies if d.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for d in discrepancies if d.severity == SeverityLevel.HIGH)
        medium_count = sum(1 for d in discrepancies if d.severity == SeverityLevel.MEDIUM)
        low_count = sum(1 for d in discrepancies if d.severity == SeverityLevel.LOW)

        score = self.calculate_consistency_score(discrepancies)
        is_consistent = (critical_count == 0 and high_count == 0)

        summary_lines = []
        if is_consistent:
            summary_lines.append("✓ Application declared fields are consistent with submitted documents.")
        else:
            summary_lines.append("⚠ Inconsistencies detected between declared application and submitted documents.")

        for disc in discrepancies:
            summary_lines.append(f"- [{disc.severity}] {disc.field}: {disc.reason}")

        summary_text = "\n".join(summary_lines)

        loan_id = str(declared_record.get("loan_id", "UNKNOWN"))
        return ValidationResult(
            case_id=loan_id,
            applicant_id=loan_id,
            is_consistent=is_consistent,
            total_discrepancies=len(discrepancies),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            discrepancies=discrepancies,
            consistency_score=score,
            summary_text=summary_text
        )