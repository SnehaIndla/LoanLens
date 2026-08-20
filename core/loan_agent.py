from typing import TypedDict, Any

from langgraph.graph import StateGraph, START, END


# --------------------------------------------------
# LoanLens Agent State
# --------------------------------------------------

class LoanState(TypedDict, total=False):
    loan_id: int
    verification_result: Any
    risk_score: int
    risk_level: str
    human_review_required: bool
    findings: list
    final_summary: str


# --------------------------------------------------
# Step 1: Start
# --------------------------------------------------

def start_process(state: LoanState):

    print(f"Starting LoanLens analysis for Loan ID: {state['loan_id']}")

    return state


# --------------------------------------------------
# Step 2: Verification
# --------------------------------------------------

def verify_loan(state: LoanState):

    print("Running document verification...")

    from verification import get_loan_record, CrossValidationAgent
    from test_verification import read_loan_documents, analyze_loan

    loan_id = state["loan_id"]
    record = get_loan_record(loan_id)
    if record is None:
        print(f"Loan record not found for Loan ID: {loan_id}")
        state["verification_result"] = None
        return state

    claims, document_claims = read_loan_documents(loan_id)

    try:
        result = analyze_loan(loan_id)
    except Exception as e:
        print(f"analyze_loan failed or Ollama not running: {e}. Falling back to default summaries.")
        from risk_engine import calculate_risk
        from document_requirements import check_missing_documents
        from verification import (
            compare_bank_assets,
            compare_profile,
            compare_document_identity,
            check_payslip_income,
            check_tax_income
        )
        from summary_generator import generate_summary
        
        missing_documents = check_missing_documents(document_claims)
        payslip_res = check_payslip_income(record, claims)
        tax_res = check_tax_income(record, claims)
        bank_res = compare_bank_assets(record, claims)
        profile_res = compare_profile(record, claims)
        identity_res = compare_document_identity(document_claims)
        
        risk_res = calculate_risk(
            missing_documents,
            payslip_res,
            tax_res,
            bank_res,
            profile_res,
            identity_res
        )
        
        summary = generate_summary(
            loan_id,
            risk_res,
            missing_documents,
            payslip_res,
            tax_res,
            bank_res,
            profile_res,
            identity_res
        )
        
        result = {
            "loan_id": loan_id,
            "record": record,
            "claims": claims,
            "missing_documents": missing_documents,
            "payslip_result": payslip_res,
            "tax_result": tax_res,
            "bank_result": bank_res,
            "profile_results": profile_res,
            "identity_result": identity_res,
            "risk_result": risk_res,
            "summary": summary,
            "ai_summary": summary
        }

    agent = CrossValidationAgent()
    validation_result = agent.cross_check_fields(record, claims)

    # Merge validation_result fields into the result dictionary
    validation_result_dict = validation_result.model_dump()
    result.update(validation_result_dict)

    # Save dictionary representation of the merged result to state
    state["verification_result"] = result

    return state


# --------------------------------------------------
# Step 3: Risk Assessment
# --------------------------------------------------

def assess_risk(state: LoanState):

    print("Running risk assessment...")

    validation_result = state.get("verification_result")

    if not validation_result:
        print("No verification result available.")
        return state

    from risk_engine import calculate_risk

    risk = calculate_risk(validation_result=validation_result)

    state["risk_score"] = risk.get("risk_score", 0)
    state["risk_level"] = risk.get("risk_level", "UNKNOWN")
    state["human_review_required"] = risk.get(
        "human_review_required",
        False
    )
    state["findings"] = risk.get(
        "findings",
        []
    )

    print(
        f"Risk Score: {state['risk_score']}"
    )

    print(
        f"Risk Level: {state['risk_level']}"
    )

    print(
        f"Human Review Required: "
        f"{state['human_review_required']}"
    )

    return state


# --------------------------------------------------
# Step 4: Agent Decision
# --------------------------------------------------
def agent_decision(state: LoanState):

    print("\nAgent reviewing verification results...")

    findings = state.get("findings", [])
    human_review = state.get(
        "human_review_required",
        False
    )

    if human_review:

        print("Decision: HUMAN REVIEW REQUIRED")

        if findings:

            print("Agent findings:")

            for finding in findings:
                print(f" - {finding}")

    else:

        print("Decision: APPLICATION CAN PROCEED")

    return state
# --------------------------------------------------
# Agent Re-check / Re-planning
# --------------------------------------------------

def recheck_evidence(state: LoanState):

    print("\nAgent detected an issue.")
    print("Re-checking verification evidence...")

    findings = state.get("findings", [])
    if not findings:
        verification = state.get("verification_result", {}) or {}
        risk = verification.get("risk_result", {}) if isinstance(verification, dict) else {}
        findings = risk.get("findings", [])

    # Re-evaluate the evidence already produced
    if findings:

        print("Re-check findings:")

        for finding in findings:
            print(f" - {finding}")

        print(
            "Agent conclusion: "
            "The issue is supported by the verification evidence."
        )

        state["human_review_required"] = True

    else:

        print(
            "Agent conclusion: "
            "No issue confirmed after re-check."
        )

        state["human_review_required"] = False

    return state
# --------------------------------------------------
# Conditional Agent Routing
# --------------------------------------------------

def route_after_decision(state: LoanState):

    if state.get("human_review_required", False):
        return "recheck"

    return "proceed"
# --------------------------------------------------
# Human Review
# --------------------------------------------------

def human_review(state: LoanState):

    print("\nHuman review required.")

    findings = state.get("findings", [])

    if findings:

        print("Issues requiring review:")

        for finding in findings:
            print(f" - {finding}")

    else:

        print("No specific findings available.")

    return state
# --------------------------------------------------
# Proceed
# --------------------------------------------------

def proceed_application(state: LoanState):

    print("\nApplication can proceed.")

    return state



# --------------------------------------------------
# Step 5: Generate Explanation
# --------------------------------------------------

def generate_explanation(state: LoanState):

    print("Generating explainable loan summary...")

    return state


# --------------------------------------------------
# Build LangGraph
# --------------------------------------------------

builder = StateGraph(LoanState)

builder.add_node("start_process", start_process)
builder.add_node("verify_loan", verify_loan)
builder.add_node("assess_risk", assess_risk)
builder.add_node("agent_decision", agent_decision)
builder.add_node("recheck_evidence", recheck_evidence)
builder.add_node("human_review", human_review)
builder.add_node("proceed", proceed_application)
builder.add_node("generate_explanation", generate_explanation)


builder.add_edge(START, "start_process")

builder.add_edge(
    "start_process",
    "verify_loan"
)

builder.add_edge(
    "verify_loan",
    "assess_risk"
)

builder.add_edge(
    "assess_risk",
    "agent_decision"
)


# Conditional routing
builder.add_conditional_edges(
    "agent_decision",
    route_after_decision,
    {
        "recheck": "recheck_evidence",
        "proceed": "proceed"
    }
)


builder.add_edge(
    "human_review",
    "generate_explanation"
)

builder.add_edge(
    "proceed",
    "generate_explanation"
)

builder.add_edge(
    "generate_explanation",
    END
)

loan_graph = builder.compile()


# --------------------------------------------------
# Test the Graph
# --------------------------------------------------

if __name__ == "__main__":

    result = loan_graph.invoke({
        "loan_id": 4
    })

    print("\nLoanLens Agent completed.")
    print(result)