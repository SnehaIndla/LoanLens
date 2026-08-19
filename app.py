import streamlit as st
import sys
from pathlib import Path

# Add core folder to Python path
sys.path.append(str(Path(__file__).parent / "core"))

from test_verification import analyze_loan


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="LoanLens",
    page_icon="🏦",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 20px;
        font-weight: 500;
    }

    .description {
        font-size: 16px;
        color: #AAAAAA;
    }

    .risk-low {
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        background-color: #123D2B;
    }

    .risk-medium {
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        background-color: #4A3510;
    }

    .risk-high {
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        background-color: #4A1717;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🏦 LoanLens</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">Intelligent Loan Document Verification System</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="description">
    LoanLens analyzes loan documents, verifies extracted claims against
    reference data, identifies inconsistencies, calculates risk, and
    provides an explainable AI-assisted review.
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# =========================================================
# LOAN SELECTION
# =========================================================

st.header("📋 Loan Application")

col1, col2 = st.columns([4, 1])

with col1:

    loan_id = st.selectbox(
        "Select Loan ID",
        list(range(1, 11))
    )

with col2:

    st.write("")
    st.write("")

    analyze_button = st.button(
        "🔍 Analyze Loan",
        type="primary",
        use_container_width=True
    )


# =========================================================
# ANALYSIS
# =========================================================

if analyze_button:

    with st.spinner(
        f"Analyzing Loan ID {loan_id}..."
    ):

        try:

            result = analyze_loan(loan_id)

        except Exception as e:

            st.error(
                f"Analysis failed: {e}"
            )
            st.stop()

    if result is None:

        st.error(
            "Loan record not found."
        )
        st.stop()

    st.success(
        "✓ Loan analysis completed successfully."
    )


    # =====================================================
    # DATA
    # =====================================================

    record = result["record"]
    claims = result["claims"]

    risk = result["risk_result"]

    missing_documents = result[
        "missing_documents"
    ]

    payslip = result[
        "payslip_result"
    ]

    tax = result[
        "tax_result"
    ]

    bank = result[
        "bank_result"
    ]

    profile_results = result[
        "profile_results"
    ]

    identity = result[
        "identity_result"
    ]

    ai_summary = result[
        "ai_summary"
    ]


    # =====================================================
    # APPLICANT INFORMATION
    # =====================================================

    st.divider()

    st.header("👤 Applicant Information")

    # Use record first, claims as fallback
    borrower_name = (
        record.get("borrower_name")
        if isinstance(record, dict)
        else None
    )

    if not borrower_name:
        borrower_name = claims.get(
            "borrower_name",
            "Not Available"
        )

    education = claims.get(
        "education",
        record.get("education", "Not Available")
        if isinstance(record, dict)
        else "Not Available"
    )

    employment = claims.get(
        "self_employed",
        record.get("self_employed", "Not Available")
        if isinstance(record, dict)
        else "Not Available"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Loan ID",
            result["loan_id"]
        )

    with col2:

        st.metric(
            "Applicant",
            borrower_name
        )

    with col3:

        st.metric(
            "Education",
            education
        )

    st.caption(
        f"Self Employed: {employment}"
    )


    # =====================================================
    # RISK OVERVIEW
    # =====================================================

    st.divider()

    st.header("⚠️ Risk Assessment")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Risk Score",
            f"{risk['risk_score']} / 100"
        )

    with col2:

        st.metric(
            "Risk Level",
            risk["risk_level"]
        )

    with col3:

        review = (
            "YES"
            if risk["human_review_required"]
            else "NO"
        )

        st.metric(
            "Human Review Required",
            review
        )


    # Risk message
    if risk["risk_level"] == "LOW":

        st.success(
            "🟢 LOW RISK — No significant issues detected."
        )

    elif risk["risk_level"] == "MEDIUM":

        st.warning(
            "🟠 MEDIUM RISK — Human review is required."
        )

    else:

        st.error(
            "🔴 HIGH RISK — Human review is required."
        )


    # =====================================================
    # DOCUMENT VERIFICATION
    # =====================================================

    st.divider()

    st.header("📄 Document Verification")

    if missing_documents:

        st.warning(
            "⚠️ Missing Documents"
        )

        for document in missing_documents:

            st.write(
                f"• {document}"
            )

    else:

        st.success(
            "✓ All required documents submitted"
        )


    # =====================================================
    # FINANCIAL CONSISTENCY
    # =====================================================

    st.divider()

    st.header("💰 Financial Consistency")

    col1, col2, col3 = st.columns(3)


    # ---------------- Payslip ----------------

    with col1:

        st.subheader("Payslip")

        if payslip:

            difference = payslip[
                "difference_percent"
            ]

            if difference > 10:

                st.error(
                    f"⚠ Mismatch\n\n"
                    f"Difference: {difference}%"
                )

            else:

                st.success(
                    f"✓ Consistent\n\n"
                    f"Difference: {difference}%"
                )

        else:

            st.warning(
                "Not Available"
            )


    # ---------------- Tax Return ----------------

    with col2:

        st.subheader("Tax Return")

        if tax:

            difference = tax[
                "difference_percent"
            ]

            if difference > 10:

                st.error(
                    f"⚠ Mismatch\n\n"
                    f"Difference: {difference}%"
                )

            else:

                st.success(
                    f"✓ Consistent\n\n"
                    f"Difference: {difference}%"
                )

        else:

            st.warning(
                "⚠ Missing"
            )


    # ---------------- Bank Assets ----------------

    with col3:

        st.subheader("Bank Assets")

        if bank:

            difference = bank[
                "difference_percent"
            ]

            if difference > 10:

                st.error(
                    f"⚠ Mismatch\n\n"
                    f"Difference: {difference}%"
                )

            else:

                st.success(
                    f"✓ Consistent\n\n"
                    f"Difference: {difference}%"
                )

        else:

            st.warning(
                "Not Available"
            )


    # =====================================================
    # PROFILE VERIFICATION
    # =====================================================

    st.divider()

    st.header("👤 Profile & Identity Verification")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("Profile")

        for profile in profile_results:

            if profile["match"]:

                st.success(
                    f"✓ {profile['check']}"
                )

            else:

                st.error(
                    f"⚠ {profile['check']}"
                )

    with col2:

        st.subheader("Identity")

        if identity["status"] == "match":

            st.success(
                "✓ Identity Consistent"
            )

        elif identity["status"] == "mismatch":

            st.error(
                "⚠ Identity Mismatch"
            )

            if "names" in identity:

                for item in identity["names"]:

                    st.write(
                        f"**{item['document']}**: "
                        f"{item['name']}"
                    )

        else:

            st.warning(
                "⚠ Insufficient Identity Evidence"
            )


    # =====================================================
    # FINDINGS
    # =====================================================

    st.divider()

    st.header("🔎 Verification Findings")

    findings = risk["findings"]

    if findings:

        for finding in findings:

            st.warning(
                f"⚠️ {finding}"
            )

    else:

        st.success(
            "✓ No significant issues detected"
        )


    # =====================================================
    # GENAI SUMMARY
    # =====================================================

    st.divider()

    st.header("🤖 LoanLens AI Summary")

    with st.container(border=True):

        st.markdown(
            ai_summary
        )


    # =====================================================
    # FINAL STATUS
    # =====================================================

    st.divider()

    if risk["human_review_required"]:

        st.warning(
            "👨‍💼 FINAL STATUS: Human review required "
            "before final processing."
        )

    else:

        st.success(
            "✅ FINAL STATUS: No human review required "
            "based on the verified results."
        )