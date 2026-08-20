from typing import Any, Dict, List

from .schemas import SummaryState


MAX_SUMMARY_LENGTH = 3000
MIN_CONFIDENCE = 0.70


def _contains_unknown_information(summary: str) -> bool:

    suspicious_phrases = [
        "i think",
        "probably",
        "might be",
        "it seems",
        "perhaps",
        "likely",
        "assume",
        "assuming",
    ]

    summary_lower = summary.lower()

    return any(
        phrase in summary_lower
        for phrase in suspicious_phrases
    )


def _get_validation_discrepancies(
    validation: Dict[str, Any]
) -> List[str]:

    discrepancies = validation.get(
        "discrepancies",
        []
    )

    if isinstance(discrepancies, list):
        return discrepancies

    return []


def _get_missing_fields(
    extraction: Dict[str, Any]
) -> List[str]:

    missing_fields = extraction.get(
        "missing_fields",
        []
    )

    if isinstance(missing_fields, list):
        return missing_fields

    return []


def run_guardrail(state: SummaryState) -> SummaryState:

    summary = state.get(
        "summary",
        ""
    )

    confidence = state.get(
        "confidence",
        0.0
    )

    validation = state.get(
        "validation",
        {}
    )

    extraction = state.get(
        "extraction",
        {}
    )

    risk_analysis = state.get(
        "risk_analysis",
        {}
    )

    reasons: List[str] = []
    violations: List[str] = []

    # --------------------------------------------------
    # 1. Summary existence check
    # --------------------------------------------------

    if not summary.strip():

        violations.append(
            "Summary is empty."
        )

    # --------------------------------------------------
    # 2. Length check
    # --------------------------------------------------

    if len(summary) > MAX_SUMMARY_LENGTH:

        violations.append(
            "Summary exceeds maximum allowed length."
        )

    # --------------------------------------------------
    # 3. Confidence check
    # --------------------------------------------------

    if confidence < MIN_CONFIDENCE:

        reasons.append(
            f"Summary confidence is below threshold: {confidence:.2f}"
        )

    # --------------------------------------------------
    # 4. Uncertain language check
    # --------------------------------------------------

    if _contains_unknown_information(summary):

        reasons.append(
            "Summary contains uncertain or speculative language."
        )

    # --------------------------------------------------
    # 5. Missing fields
    # --------------------------------------------------

    missing_fields = _get_missing_fields(
        extraction
    )

    if missing_fields:

        reasons.append(
            "Required fields are missing: "
            + ", ".join(map(str, missing_fields))
        )

    # --------------------------------------------------
    # 6. Validation discrepancies
    # --------------------------------------------------

    discrepancies = _get_validation_discrepancies(
        validation
    )

    if discrepancies:

        reasons.append(
            f"{len(discrepancies)} validation discrepancy/discrepancies detected."
        )

    # --------------------------------------------------
    # 7. High risk
    # --------------------------------------------------

    risk_level = str(
        risk_analysis.get(
            "risk_level",
            ""
        )
    ).upper()

    if risk_level == "HIGH":

        reasons.append(
            "High-risk case requires human review."
        )

    # --------------------------------------------------
    # 8. Explicit risk flags
    # --------------------------------------------------

    risk_flags = risk_analysis.get(
        "flags",
        []
    )

    if risk_flags:

        reasons.append(
            "Risk flags detected."
        )

    # --------------------------------------------------
    # Final decision
    # --------------------------------------------------

    critical_failure = len(violations) > 0

    human_review_required = (
        critical_failure
        or len(reasons) > 0
    )

    approved = not human_review_required

    return {
        **state,

        "guardrail_approved": approved,

        "requires_human_review": human_review_required,

        "guardrail_reasons": reasons,

        "guardrail_violations": violations,

        "final_status": (
            "GUARDRAIL_APPROVED"
            if approved
            else "HUMAN_REVIEW_REQUIRED"
        ),
    }