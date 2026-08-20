import math


# =================================
# CIBIL Score Bands
# =================================
# Band         | Range     | Risk Pts
# -------------|-----------|--------
# Very Low     | < 500     | +30
# Low          | 500 - 599 | +20
# Fair         | 600 - 699 | +10
# Good         | 700 - 799 | +0
# Excellent    | >= 800    | +0
# =================================

CIBIL_BANDS = [
    {
        "name": "very_low",
        "min": 0,
        "max": 499,
        "risk_points": 30
    },
    {
        "name": "low",
        "min": 500,
        "max": 599,
        "risk_points": 20
    },
    {
        "name": "fair",
        "min": 600,
        "max": 699,
        "risk_points": 10
    },
    {
        "name": "good",
        "min": 700,
        "max": 799,
        "risk_points": 0
    },
    {
        "name": "excellent",
        "min": 800,
        "max": 900,
        "risk_points": 0
    }
]


# =================================
# Similar-case search weights
# =================================
# Feature weights for the weighted
# Euclidean distance calculation.
# Income and loan amount are the
# most discriminative for risk.
# =================================

SIMILARITY_WEIGHTS = {
    "income_annum": 0.4,
    "loan_amount": 0.4,
    "cibil_score": 0.2
}

SIMILAR_CASES_TOP_N = 5

REJECTION_RATE_THRESHOLD = 0.6

SIMILAR_CASES_RISK_POINTS = 10


# =================================
# Get CIBIL band
# =================================

def get_cibil_band(cibil_score):

    for band in CIBIL_BANDS:

        if (
            band["min"]
            <= cibil_score
            <= band["max"]
        ):

            return band

    # Default: if score is out of
    # expected range, treat as
    # very_low for safety.

    return CIBIL_BANDS[0]


# =================================
# Search similar cases
# =================================

def search_similar_cases(
    record,
    dataset,
    top_n=SIMILAR_CASES_TOP_N
):
    """
    Find the N most similar historical
    applicants by weighted Euclidean
    distance on income_annum,
    loan_amount, and cibil_score.

    Returns a dict with:
      - similar_cases: list of neighbor
        dicts (loan_id, similarity_score,
        loan_status)
      - rejection_rate: float
      - risk_contribution: int
      - flag: str or None
    """

    if dataset is None or dataset.empty:

        return {
            "similar_cases": [],
            "rejection_rate": 0.0,
            "risk_contribution": 0,
            "flag": None
        }

    # ---------------------------------
    # Get applicant values
    # ---------------------------------

    applicant_income = float(
        record.get("income_annum", 0)
    )

    applicant_loan = float(
        record.get("loan_amount", 0)
    )

    applicant_cibil = float(
        record.get("cibil_score", 0)
    )

    applicant_loan_id = record.get(
        "loan_id",
        None
    )

    # ---------------------------------
    # Compute min/max for
    # normalization from dataset
    # ---------------------------------

    features = [
        "income_annum",
        "loan_amount",
        "cibil_score"
    ]

    mins = {}
    maxs = {}
    ranges = {}

    for feature in features:

        col = dataset[feature].astype(float)

        mins[feature] = col.min()
        maxs[feature] = col.max()

        feature_range = (
            maxs[feature] - mins[feature]
        )

        ranges[feature] = (
            feature_range
            if feature_range > 0
            else 1.0
        )

    # ---------------------------------
    # Normalize applicant values
    # ---------------------------------

    applicant_norm = {
        "income_annum": (
            (applicant_income - mins["income_annum"])
            / ranges["income_annum"]
        ),
        "loan_amount": (
            (applicant_loan - mins["loan_amount"])
            / ranges["loan_amount"]
        ),
        "cibil_score": (
            (applicant_cibil - mins["cibil_score"])
            / ranges["cibil_score"]
        )
    }

    # ---------------------------------
    # Compute distance to each row
    # ---------------------------------

    distances = []

    for idx, row in dataset.iterrows():

        row_loan_id = row.get(
            "loan_id",
            None
        )

        # Skip the applicant's own
        # record if it exists in the
        # dataset.

        if (
            applicant_loan_id is not None
            and row_loan_id == applicant_loan_id
        ):
            continue

        row_norm = {}

        for feature in features:

            row_val = float(
                row[feature]
            )

            row_norm[feature] = (
                (row_val - mins[feature])
                / ranges[feature]
            )

        # Weighted Euclidean distance

        dist_sq = 0.0

        for feature in features:

            diff = (
                applicant_norm[feature]
                - row_norm[feature]
            )

            weight = SIMILARITY_WEIGHTS[
                feature
            ]

            dist_sq += weight * (diff ** 2)

        distance = math.sqrt(dist_sq)

        # Similarity = 1 / (1 + distance)
        # so closer records get a
        # higher similarity score.

        similarity = round(
            1.0 / (1.0 + distance),
            4
        )

        distances.append({
            "loan_id": int(row_loan_id)
                if row_loan_id is not None
                else idx,
            "distance": distance,
            "similarity_score": similarity,
            "loan_status": str(
                row.get("loan_status", "")
            ).strip()
        })

    # ---------------------------------
    # Sort by distance (ascending)
    # and take top N
    # ---------------------------------

    distances.sort(
        key=lambda x: x["distance"]
    )

    top_cases = distances[:top_n]

    # ---------------------------------
    # Compute rejection rate
    # ---------------------------------

    if top_cases:

        rejected_count = sum(
            1
            for case in top_cases
            if case["loan_status"].lower()
            in [
                "rejected",
                " rejected"
            ]
        )

        rejection_rate = round(
            rejected_count / len(top_cases),
            4
        )

    else:

        rejection_rate = 0.0

    # ---------------------------------
    # Determine risk contribution
    # ---------------------------------

    risk_contribution = 0
    flag = None

    if (
        rejection_rate
        > REJECTION_RATE_THRESHOLD
    ):

        risk_contribution = (
            SIMILAR_CASES_RISK_POINTS
        )

        flag = (
            "SIMILAR_CASES_HIGH_REJECTION_RATE"
        )

    # ---------------------------------
    # Build output (remove internal
    # distance field from output)
    # ---------------------------------

    similar_cases_output = []

    for case in top_cases:

        similar_cases_output.append({
            "loan_id":
                case["loan_id"],
            "similarity_score":
                case["similarity_score"],
            "loan_status":
                case["loan_status"]
        })

    return {
        "similar_cases":
            similar_cases_output,
        "rejection_rate":
            rejection_rate,
        "risk_contribution":
            risk_contribution,
        "flag":
            flag
    }


# =================================
# Calculate risk
# =================================

def calculate_risk(
    missing_documents,
    payslip_result,
    tax_result,
    bank_result,
    profile_results,
    identity_result,
    record=None,
    dataset=None
):

    score = 0

    findings = []

    flags = set()


    # =================================
    # Missing documents
    # =================================

    for document in missing_documents:

        score += 20

        findings.append(
            f"Missing document: {document}"
        )

        flags.add(
            "MISSING_DOCUMENTS"
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

            flags.add(
                "INCOME_DISCREPANCY"
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

            flags.add(
                "INCOME_DISCREPANCY"
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

            flags.add(
                "BANK_ASSET_MISMATCH"
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

            flags.add(
                "PROFILE_MISMATCH"
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

        flags.add(
            "IDENTITY_MISMATCH"
        )


    # =================================
    # Credit history (CIBIL score)
    # =================================

    credit_history_result = None

    if record is not None:

        cibil_score = record.get(
            "cibil_score",
            None
        )

        if cibil_score is not None:

            cibil_score = int(cibil_score)

            band = get_cibil_band(
                cibil_score
            )

            risk_points = band[
                "risk_points"
            ]

            score += risk_points

            credit_history_result = {
                "cibil_score":
                    cibil_score,
                "band":
                    band["name"],
                "risk_contribution":
                    risk_points
            }

            if risk_points > 0:

                findings.append(
                    f"CIBIL score {cibil_score}"
                    f" ({band['name']})"
                    f" — credit risk"
                    f" contribution: +{risk_points}"
                )

            if band["name"] in [
                "very_low",
                "low"
            ]:

                flags.add(
                    "LOW_CIBIL_SCORE"
                )


    # =================================
    # Similar historical cases
    # =================================

    similar_result = search_similar_cases(
        record if record else {},
        dataset
    )

    similar_past_cases = (
        similar_result["similar_cases"]
    )

    if similar_result["risk_contribution"] > 0:

        score += similar_result[
            "risk_contribution"
        ]

        rejection_pct = round(
            similar_result["rejection_rate"]
            * 100,
            1
        )

        findings.append(
            f"Similar historical cases show"
            f" {rejection_pct}% rejection rate"
            f" — anomaly risk"
            f" contribution:"
            f" +{similar_result['risk_contribution']}"
        )

    if similar_result["flag"]:

        flags.add(
            similar_result["flag"]
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
        "findings": findings,
        "flags":
            sorted(list(flags)),
        "credit_history_result":
            credit_history_result,
        "similar_past_cases":
            similar_past_cases
    }