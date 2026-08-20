"""
LoanLens - Document Classification Agent

Classifies loan-related documents into categories:
    payslip, bank_statement, tax_return, kyc, unknown

Provides two public APIs:
    classify_document(text, filename)          -> str   (backward-compatible)
    classify_document_detailed(text, filename) -> dict  (full detail)
"""


# =============================================================
# CLASSIFICATION KEYWORDS (weighted)
# =============================================================
#
# Each category maps keywords to integer weights.
# Higher weight = stronger signal for that category.

CATEGORY_KEYWORDS = {

    "payslip": {
        "monthly payslip":    5,
        "pay period":         4,
        "monthly income":     4,
        "net pay":            3,
        "gross salary":       3,
        "employer":           2,
        "salary slip":        4,
        "pay slip":           4,
        "basic pay":          3,
        "deductions":         2,
    },

    "bank_statement": {
        "bank statement":     5,
        "bank asset balance": 5,
        "salary credit":      4,
        "account holder":     3,
        "account number":     3,
        "closing balance":    3,
        "opening balance":    3,
        "transaction":        2,
        "statement period":   3,
    },

    "tax_return": {
        "income tax return":  5,
        "annual income":      4,
        "assessment year":    5,
        "taxable income":     4,
        "tax payable":        3,
        "taxpayer":           3,
        "return status":      3,
        "form 16":            4,
        "itr":                3,
    },

    "kyc": {
        "kyc document":       5,
        "identity verification": 5,
        "know your customer": 4,
        "aadhaar":            4,
        "pan card":           4,
        "passport":           3,
        "voter id":           3,
        "driving license":    3,
        "self employed":      2,
    },
}


# =============================================================
# FILENAME PATTERNS
# =============================================================
#
# If the filename contains any of these substrings,
# a bonus score is added to the matching category.

FILENAME_HINTS = {
    "payslip":        "payslip",
    "bank_statement": "bank",
    "tax_return":     "tax",
    "kyc":            "kyc",
}


# =============================================================
# CONFIDENCE THRESHOLDS
# =============================================================

CONFIDENCE_HIGH = 0.70       # >= this -> "classified"
CONFIDENCE_LOW  = 0.40       # >= this but < HIGH -> "low_confidence"
                              # < LOW -> "unrecognized"

FILENAME_BONUS  = 3          # Bonus weight when filename matches

AMBIGUITY_RATIO = 0.80       # If 2nd-best score >= 80% of best -> ambiguous


# =============================================================
# INTERNAL: _compute_scores
# =============================================================

def _compute_scores(text, filename=""):
    """
    Compute a raw score for each document category
    based on keyword matches and filename hints.

    Args:
        text:     Full text content of the document.
        filename: Original filename (optional).

    Returns:
        dict: {category: raw_score}
    """

    # Guard against None / non-string input
    if not isinstance(text, str):
        text = ""
    if not isinstance(filename, str):
        filename = ""

    content = (text + " " + filename).lower()

    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():

        score = 0

        for keyword, weight in keywords.items():
            if keyword in content:
                score += weight

        # Filename bonus
        hint = FILENAME_HINTS.get(category, "")
        if hint and hint in filename.lower():
            score += FILENAME_BONUS

        scores[category] = score

    return scores


# =============================================================
# INTERNAL: _normalize_scores
# =============================================================

def _normalize_scores(scores):
    """
    Convert raw scores to confidence values (0.0 - 1.0).

    The confidence for each category is its score divided
    by the total of all scores. If total is 0, all
    confidences are 0.0.

    Args:
        scores: dict of {category: raw_score}

    Returns:
        dict: {category: confidence_float}
    """

    total = sum(scores.values())

    if total == 0:
        return {cat: 0.0 for cat in scores}

    return {
        cat: round(score / total, 4)
        for cat, score in scores.items()
    }


# =============================================================
# INTERNAL: _determine_result
# =============================================================

def _determine_result(scores, confidences):
    """
    Determine the final classification result from
    computed scores and confidences.

    Handles:
        - No matches (unknown / unrecognized)
        - Ambiguous matches (two categories too close)
        - Low-confidence matches
        - High-confidence matches

    Args:
        scores:      dict of {category: raw_score}
        confidences: dict of {category: confidence_float}

    Returns:
        tuple: (document_type, confidence, status)
    """

    total = sum(scores.values())

    # No keywords matched at all
    if total == 0:
        return ("unknown", 0.0, "unrecognized")

    # Find the top category
    top_category = max(scores, key=scores.get)
    top_confidence = confidences[top_category]

    # Check for ambiguity: top two categories too close
    sorted_scores = sorted(
        scores.values(), reverse=True
    )

    if (
        len(sorted_scores) >= 2
        and sorted_scores[0] > 0
        and sorted_scores[1] > 0
    ):
        ratio = sorted_scores[1] / sorted_scores[0]

        # If second-best is >= AMBIGUITY_RATIO of the best
        if ratio >= AMBIGUITY_RATIO:
            return (
                top_category,
                top_confidence,
                "low_confidence"
            )

    # Apply confidence thresholds
    if top_confidence >= CONFIDENCE_HIGH:
        status = "classified"

    elif top_confidence >= CONFIDENCE_LOW:
        status = "low_confidence"

    else:
        status = "unrecognized"

    # If status is unrecognized, override type to unknown
    if status == "unrecognized":
        return ("unknown", top_confidence, status)

    return (top_category, top_confidence, status)


# =============================================================
# PUBLIC: classify_document_detailed
# =============================================================

def classify_document_detailed(text, filename=""):
    """
    Classify a loan document with full detail.

    Args:
        text:     Full text content extracted from the document.
        filename: Original filename (optional, used as hint).

    Returns:
        dict: {
            "document_type": str,     # "payslip" | "bank_statement" |
                                      # "tax_return" | "kyc" | "unknown"
            "confidence":    float,   # 0.0 - 1.0
            "status":        str,     # "classified" | "low_confidence" |
                                      # "unrecognized"
            "all_scores":    dict,    # {category: confidence}
        }
    """

    scores = _compute_scores(text, filename)
    confidences = _normalize_scores(scores)

    doc_type, confidence, status = _determine_result(
        scores, confidences
    )

    return {
        "document_type": doc_type,
        "confidence":    confidence,
        "status":        status,
        "all_scores":    confidences,
    }


# =============================================================
# PUBLIC: classify_document  (BACKWARD-COMPATIBLE)
# =============================================================

def classify_document(text, filename=""):
    """
    Identify the type of financial document.

    Backward-compatible API - returns a plain string.

    Args:
        text:     Full text content extracted from the document.
        filename: Original filename (optional, used as hint).

    Returns:
        str: "payslip" | "bank_statement" | "tax_return" |
             "kyc" | "unknown"
    """

    result = classify_document_detailed(text, filename)
    return result["document_type"]