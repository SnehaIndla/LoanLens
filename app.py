import sys
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------
# PROJECT PATH
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
CORE_DIR = BASE_DIR / "core"

if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

# Import LangGraph agent
from loan_agent import loan_graph


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="LoanLens",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.markdown(
    """
    <style>

    /* -----------------------------
       GLOBAL
    ----------------------------- */

    .stApp {
        background:
            radial-gradient(
                circle at 15% 10%,
                rgba(125, 60, 255, 0.12),
                transparent 30%
            ),
            radial-gradient(
                circle at 85% 15%,
                rgba(0, 180, 255, 0.08),
                transparent 28%
            ),
            #070b14;
        color: #f5f7ff;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    /* -----------------------------
       HEADER
    ----------------------------- */

    .brand {
        font-size: 42px;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(
            90deg,
            #c084fc,
            #8b5cf6,
            #60a5fa
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .subtitle {
        font-size: 18px;
        font-weight: 600;
        color: #e5e7eb;
        margin-top: -8px;
    }

    .description {
        color: #9ca3af;
        max-width: 720px;
        line-height: 1.6;
    }

    .agent-badge {
        background: rgba(91, 33, 182, 0.18);
        border: 1px solid rgba(139, 92, 246, 0.35);
        border-radius: 12px;
        padding: 10px 16px;
        color: #c4b5fd;
        font-weight: 600;
        text-align: center;
    }

    /* -----------------------------
       CARDS
    ----------------------------- */

    .metric-card {
        background:
            linear-gradient(
                145deg,
                rgba(20, 27, 43, 0.98),
                rgba(10, 15, 27, 0.98)
            );
        border: 1px solid #263247;
        border-radius: 16px;
        padding: 20px;
        min-height: 145px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.20);
    }

    .metric-title {
        color: #a1a1aa;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 10px;
    }

    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #ffffff;
    }

    .metric-small {
        color: #9ca3af;
        font-size: 13px;
        margin-top: 8px;
    }

    .risk-low {
        color: #4ade80;
    }

    .risk-medium {
        color: #fbbf24;
    }

    .risk-high {
        color: #fb7185;
    }

    /* -----------------------------
       FINDINGS
    ----------------------------- */

    .finding-warning {
        background: rgba(120, 70, 10, 0.25);
        border: 1px solid rgba(245, 158, 11, 0.35);
        border-radius: 12px;
        padding: 16px;
        color: #fbbf24;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .finding-success {
        background: rgba(16, 100, 70, 0.22);
        border: 1px solid rgba(34, 197, 94, 0.30);
        border-radius: 12px;
        padding: 16px;
        color: #86efac;
        font-weight: 600;
    }

    /* -----------------------------
       INFO CARDS
    ----------------------------- */

    .info-card {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid #263247;
        border-radius: 14px;
        padding: 18px;
        min-height: 150px;
    }

    .info-title {
        color: #c084fc;
        font-size: 15px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .info-text {
        color: #d1d5db;
        line-height: 1.55;
        font-size: 14px;
    }

    .status-good {
        display: inline-block;
        background: rgba(34,197,94,0.15);
        border: 1px solid rgba(34,197,94,0.3);
        color: #86efac;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        margin-top: 10px;
    }

    .status-bad {
        display: inline-block;
        background: rgba(245,158,11,0.15);
        border: 1px solid rgba(245,158,11,0.3);
        color: #fbbf24;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        margin-top: 10px;
    }

    /* -----------------------------
       PIPELINE
    ----------------------------- */

    .pipeline {
        background:
            linear-gradient(
                145deg,
                rgba(15,23,42,0.95),
                rgba(8,13,24,0.95)
            );
        border: 1px solid #263247;
        border-radius: 16px;
        padding: 22px;
    }

    .pipeline-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 20px;
        color: #ffffff;
    }

    .pipeline-step {
        padding: 12px 0;
        border-left: 2px solid #6d28d9;
        padding-left: 16px;
        margin-left: 8px;
    }

    .pipeline-step strong {
        color: #e5e7eb;
    }

    .pipeline-step span {
        display: block;
        color: #8f98aa;
        font-size: 12px;
        margin-top: 3px;
    }

    /* -----------------------------
       BUTTON
    ----------------------------- */

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        border: none;
        background:
            linear-gradient(
                90deg,
                #6d28d9,
                #7c3aed,
                #2563eb
            );
        color: white;
        font-weight: 700;
        min-height: 44px;
    }

    .stButton > button:hover {
        border: none;
        color: white;
        transform: translateY(-1px);
    }

    /* -----------------------------
       FOOTER
    ----------------------------- */

    .footer {
        text-align: center;
        color: #71717a;
        padding: 30px 0 10px 0;
        font-size: 13px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

header_left, header_right = st.columns([5, 1])

with header_left:
    st.markdown(
        '<div class="brand">🏦 LoanLens</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">Intelligent Loan Document Verification System</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="description">
        LoanLens analyzes loan documents, extracts verified claims,
        checks financial and identity consistency, assesses risk,
        and uses an agentic workflow to review the evidence and
        generate an explainable AI-assisted result.
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_right:
    st.markdown(
        '<div class="agent-badge">🤖 Powered by Agentic AI</div>',
        unsafe_allow_html=True,
    )


st.divider()


# ---------------------------------------------------------
# SIDEBAR / LOAN SELECTION
# ---------------------------------------------------------

with st.sidebar:

    st.markdown("## 📄 Loan Application")

    loan_id = st.selectbox(
        "Select Loan ID",
        list(range(1, 11)),
    )

    analyze = st.button(
        "🔍 Analyze Loan",
        use_container_width=True,
    )

    st.markdown("---")

    st.markdown("### 🔄 Processing Pipeline")

    st.markdown(
        """
        <div class="pipeline">

        <div class="pipeline-step">
            <strong>✓ Document Verification</strong>
            <span>Extract & verify claims</span>
        </div>

        <div class="pipeline-step">
            <strong>✓ Risk Assessment</strong>
            <span>Calculate risk score</span>
        </div>

        <div class="pipeline-step">
            <strong>✓ Agent Decision</strong>
            <span>Review & decide</span>
        </div>

        <div class="pipeline-step">
            <strong>↻ Re-check Evidence</strong>
            <span>Verify findings again</span>
        </div>

        <div class="pipeline-step">
            <strong>👤 Human Review / Proceed</strong>
            <span>Route application</span>
        </div>

        <div class="pipeline-step">
            <strong>🧠 AI Explanation</strong>
            <span>Generate summary</span>
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# RUN ANALYSIS
# ---------------------------------------------------------

if analyze:

    with st.spinner("Running LoanLens Agent..."):

        try:

            result = loan_graph.invoke(
                {
                    "loan_id": loan_id
                }
            )

            st.session_state["loan_result"] = result

        except Exception as e:

            st.error(
                f"Unable to analyze loan: {e}"
            )

            st.stop()


# ---------------------------------------------------------
# DEFAULT / RESULT
# ---------------------------------------------------------

if "loan_result" not in st.session_state:

    st.info(
        "Select a Loan ID from the sidebar and click "
        "**Analyze Loan** to begin."
    )

    st.markdown(
        """
        <div class="footer">
            🛡️ LoanLens AI &nbsp;•&nbsp;
            Intelligent &nbsp;•&nbsp;
            Transparent &nbsp;•&nbsp;
            Explainable
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


result = st.session_state["loan_result"]

verification = result.get(
    "verification_result",
    {},
)

risk_score = result.get(
    "risk_score",
    0,
)

risk_level = result.get(
    "risk_level",
    "UNKNOWN",
)

human_review = result.get(
    "human_review_required",
    False,
)

findings = result.get(
    "findings",
    [],
)

ai_summary = verification.get(
    "ai_summary",
    "",
)

summary = verification.get(
    "summary",
    "",
)


# ---------------------------------------------------------
# SUCCESS MESSAGE
# ---------------------------------------------------------

st.success(
    f"Loan {loan_id} analysis completed successfully."
)


# ---------------------------------------------------------
# TOP METRICS
# ---------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.markdown(
        f"""
        <div class="metric-card">

        <div class="metric-title">
        🛡️ Risk Score
        </div>

        <div class="metric-value">
        {risk_score}
        <span style="font-size:16px;color:#71717a;">
        /100
        </span>
        </div>

        <div class="metric-small">
        Risk assessment score
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with col2:

    if risk_level.upper() == "LOW":
        risk_class = "risk-low"
    elif risk_level.upper() == "MEDIUM":
        risk_class = "risk-medium"
    else:
        risk_class = "risk-high"

    st.markdown(
        f"""
        <div class="metric-card">

        <div class="metric-title">
        📊 Risk Level
        </div>

        <div class="metric-value {risk_class}">
        {risk_level}
        </div>

        <div class="metric-small">
        Deterministic risk assessment
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with col3:

    review_text = (
        "YES"
        if human_review
        else "NO"
    )

    review_class = (
        "risk-medium"
        if human_review
        else "risk-low"
    )

    st.markdown(
        f"""
        <div class="metric-card">

        <div class="metric-title">
        👤 Human Review
        </div>

        <div class="metric-value {review_class}">
        {review_text}
        </div>

        <div class="metric-small">
        Agent routing decision
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


with col4:

    st.markdown(
        f"""
        <div class="metric-card">

        <div class="metric-title">
        📁 Loan ID
        </div>

        <div class="metric-value">
        {loan_id}
        </div>

        <div class="metric-small">
        Application identifier
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown("")


# ---------------------------------------------------------
# FINDINGS
# ---------------------------------------------------------

st.subheader("🔎 Verification Findings")

if findings:

    for finding in findings:

        st.markdown(
            f"""
            <div class="finding-warning">
            ⚠️ {finding}
            </div>
            """,
            unsafe_allow_html=True,
        )

else:

    st.markdown(
        """
        <div class="finding-success">
        ✓ No significant issues detected.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# AGENT DECISION
# ---------------------------------------------------------

st.subheader("🤖 Agent Decision")

if human_review:

    st.warning(
        "Human review required before final processing."
    )

else:

    st.success(
        "Application can proceed based on the verified results."
    )


# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------

tabs = st.tabs(
    [
        "🧠 Executive Summary",
        "📄 Document Checks",
        "💰 Financial Consistency",
        "👤 Identity & Profile",
        "🤖 Agent Workflow",
        "🔍 Raw Evidence",
    ]
)


# =========================================================
# TAB 1 — AI SUMMARY
# =========================================================

with tabs[0]:

    left, right = st.columns(
        [2.2, 1]
    )

    with left:

        st.markdown(
            """
            <div class="info-card">

            <div class="info-title">
            🧠 AI Explanation
            </div>

            <div class="info-text">
            """,
            unsafe_allow_html=True,
        )

        if ai_summary:

            st.markdown(
                ai_summary
            )

        else:

            st.markdown(
                summary
                if summary
                else "Not available in the verified evidence."
            )

        st.markdown(
            """
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    with right:

        st.markdown(
            """
            <div class="info-card">

            <div class="info-title">
            🛡️ Recommended Action
            </div>

            <div class="info-text">
            """,
            unsafe_allow_html=True,
        )

        if human_review:

            st.markdown(
                """
                Route the application to a
                human reviewer before final processing.
                """
            )

            st.markdown(
                '<span class="status-bad">⚠ REVIEW REQUIRED</span>',
                unsafe_allow_html=True,
            )

        else:

            st.markdown(
                """
                Application can proceed to
                the next processing stage.
                """
            )

            st.markdown(
                '<span class="status-good">✓ CAN PROCEED</span>',
                unsafe_allow_html=True,
            )

        st.markdown(
            """
            </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# TAB 2 — DOCUMENT CHECKS
# =========================================================

with tabs[1]:

    st.subheader(
        "Detailed Verification Summary"
    )

    missing_documents = verification.get(
        "missing_documents",
        [],
    )

    payslip = verification.get(
        "payslip_result"
    )

    tax = verification.get(
        "tax_result"
    )

    bank = verification.get(
        "bank_result"
    )


    d1, d2, d3 = st.columns(3)


    with d1:

        st.markdown(
            """
            <div class="info-card">

            <div class="info-title">
            📄 Document Completeness
            </div>
            """,
            unsafe_allow_html=True,
        )

        if missing_documents:

            st.write(
                "Missing documents:"
            )

            for doc in missing_documents:

                st.warning(doc)

            st.markdown(
                '<span class="status-bad">⚠ INCOMPLETE</span>',
                unsafe_allow_html=True,
            )

        else:

            st.write(
                "All required documents submitted."
            )

            st.markdown(
                '<span class="status-good">✓ COMPLETE</span>',
                unsafe_allow_html=True,
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    with d2:

        st.markdown(
            """
            <div class="info-card">

            <div class="info-title">
            💼 Payslip Income Check
            </div>
            """,
            unsafe_allow_html=True,
        )

        if payslip:

            difference = payslip.get(
                "difference_percent"
            )

            st.write(
                f"Difference: {difference}%"
            )

            if difference == 0:

                st.markdown(
                    '<span class="status-good">✓ CONSISTENT</span>',
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    '<span class="status-bad">⚠ MISMATCH</span>',
                    unsafe_allow_html=True,
                )

        else:

            st.write(
                "Not available in the verified evidence."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    with d3:

        st.markdown(
            """
            <div class="info-card">

            <div class="info-title">
            🧾 Tax Return Check
            </div>
            """,
            unsafe_allow_html=True,
        )

        if tax:

            difference = tax.get(
                "difference_percent"
            )

            st.write(
                f"Difference: {difference}%"
            )

            if difference == 0:

                st.markdown(
                    '<span class="status-good">✓ CONSISTENT</span>',
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    '<span class="status-bad">⚠ MISMATCH</span>',
                    unsafe_allow_html=True,
                )

        else:

            st.write(
                "Not available in the verified evidence."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# =========================================================
# TAB 3 — FINANCIAL CONSISTENCY
# =========================================================

with tabs[2]:

    st.subheader(
        "Financial Verification"
    )

    f1, f2 = st.columns(2)


    with f1:

        st.markdown(
            """
            <div class="info-card">

            <div class="info-title">
            🏦 Bank Asset Check
            </div>
            """,
            unsafe_allow_html=True,
        )

        if bank:

            st.write(
                f"Dataset value: "
                f"{bank.get('dataset_bank_assets')}"
            )

            st.write(
                f"Document value: "
                f"{bank.get('document_bank_assets')}"
            )

            st.write(
                f"Difference: "
                f"{bank.get('difference_percent')}%"
            )

            if bank.get(
                "difference_percent"
            ) == 0:

                st.markdown(
                    '<span class="status-good">✓ CONSISTENT</span>',
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    '<span class="status-bad">⚠ MISMATCH</span>',
                    unsafe_allow_html=True,
                )

        else:

            st.write(
                "Not available in the verified evidence."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    with f2:

        st.markdown(
            """
            <div class="info-card">

            <div class="info-title">
            📈 Income Verification
            </div>
            """,
            unsafe_allow_html=True,
        )

        if payslip:

            st.write(
                f"Payslip difference: "
                f"{payslip.get('difference_percent')}%"
            )

        else:

            st.write(
                "Payslip verification unavailable."
            )


        if tax:

            st.write(
                f"Tax return difference: "
                f"{tax.get('difference_percent')}%"
            )

        else:

            st.write(
                "Tax return verification unavailable."
            )


        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# =========================================================
# TAB 4 — IDENTITY & PROFILE
# =========================================================

with tabs[3]:

    st.subheader(
        "Identity and Profile Consistency"
    )

    identity = verification.get(
        "identity_result",
        {},
    )

    profiles = verification.get(
        "profile_results",
        [],
    )


    p1, p2 = st.columns(2)


    with p1:

        st.markdown(
            """
            <div class="info-card">

            <div class="info-title">
            👤 Identity Consistency
            </div>
            """,
            unsafe_allow_html=True,
        )

        identity_status = identity.get(
            "status"
        )

        if identity_status == "match":

            st.write(
                "Identity information is consistent across submitted documents."
            )

            st.markdown(
                '<span class="status-good">✓ MATCHED</span>',
                unsafe_allow_html=True,
            )

        elif identity_status == "mismatch":

            st.write(
                "Identity information is inconsistent."
            )

            st.markdown(
                '<span class="status-bad">⚠ MISMATCH</span>',
                unsafe_allow_html=True,
            )

        else:

            st.write(
                "Not available in the verified evidence."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    with p2:

        st.markdown(
            """
            <div class="info-card">

            <div class="info-title">
            🎓 Profile Consistency
            </div>
            """,
            unsafe_allow_html=True,
        )

        if profiles:

            all_matched = True

            for profile in profiles:

                check = profile.get(
                    "check",
                    "Unknown",
                )

                match = profile.get(
                    "match",
                    False,
                )

                if match:

                    st.write(
                        f"✓ {check}: MATCH"
                    )

                else:

                    all_matched = False

                    st.write(
                        f"⚠ {check}: MISMATCH"
                    )

            if all_matched:

                st.markdown(
                    '<span class="status-good">✓ ALL MATCHED</span>',
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    '<span class="status-bad">⚠ REVIEW REQUIRED</span>',
                    unsafe_allow_html=True,
                )

        else:

            st.write(
                "Not available in the verified evidence."
            )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


# =========================================================
# TAB 5 — AGENT WORKFLOW
# =========================================================

with tabs[4]:

    st.subheader(
        "LoanLens Agent Workflow"
    )

    st.markdown(
        """
        <div class="pipeline">

        <div class="pipeline-step">
            <strong>1. Document Verification</strong>
            <span>
            Extract claims and verify submitted evidence.
            </span>
        </div>

        <div class="pipeline-step">
            <strong>2. Risk Assessment</strong>
            <span>
            Deterministic risk engine evaluates verification findings.
            </span>
        </div>

        <div class="pipeline-step">
            <strong>3. Agent Decision</strong>
            <span>
            LangGraph agent reviews the verification state.
            </span>
        </div>

        <div class="pipeline-step">
            <strong>4. Conditional Routing</strong>
            <span>
            Application is routed to re-check or proceed.
            </span>
        </div>

        <div class="pipeline-step">
            <strong>5. Evidence Re-check</strong>
            <span>
            Agent re-evaluates detected findings against verified evidence.
            </span>
        </div>

        <div class="pipeline-step">
            <strong>6. Human Review / Proceed</strong>
            <span>
            Application is routed according to the agent decision.
            </span>
        </div>

        <div class="pipeline-step">
            <strong>7. AI Explanation</strong>
            <span>
            Ollama generates an explainable summary using verified evidence.
            </span>
        </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# TAB 6 — RAW EVIDENCE
# =========================================================

with tabs[5]:

    st.subheader(
        "Verified Evidence"
    )

    st.caption(
        "This is the structured evidence produced by the deterministic verification system and agent workflow."
    )

    st.json(
        verification
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.markdown(
    """
    <div class="footer">
        🛡️ LoanLens AI
        &nbsp; • &nbsp;
        Intelligent
        &nbsp; • &nbsp;
        Transparent
        &nbsp; • &nbsp;
        Explainable
        &nbsp; • &nbsp;
        Human-in-the-Loop
    </div>
    """,
    unsafe_allow_html=True,
)