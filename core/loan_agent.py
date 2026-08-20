import sys
from pathlib import Path
from typing import TypedDict, Any

from langgraph.graph import StateGraph, START, END

CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from extractor import extract_text
from classifier import classify_document
from claims import extract_claims
from verification import verify_cross_documents
from risk_engine import calculate_risk
from genai_agent import generate_ai_summary
from summary_generator import generate_summary

# --------------------------------------------------
# LoanLens Agent State
# --------------------------------------------------

class LoanState(TypedDict, total=False):
    loan_id: Any
    client_name: str
    uploaded_files: dict  # mapping doc_type to pdf_path or temp bytes
    form_inputs: dict
    claims_by_doc: dict
    verification_result: Any
    risk_result: Any
    risk_score: int
    risk_level: str
    human_review_required: bool
    findings: list
    summary: str
    ai_summary: str


# --------------------------------------------------
# Step 1: Start Process
# --------------------------------------------------

def start_process(state: LoanState):
    loan_id = state.get("loan_id", "LN-2026-0001")
    client_name = state.get("client_name", "Applicant")
    print(f"Starting LoanLens Live Analysis for Loan ID: {loan_id} ({client_name})")
    return state


# --------------------------------------------------
# Step 2: Live Document Verification
# --------------------------------------------------

def verify_loan(state: LoanState):
    print("Extracting text and running cross-document verification...")
    uploaded_files = state.get("uploaded_files", {})
    form_inputs = state.get("form_inputs", {})
    
    claims_by_doc = {}

    for doc_type, file_path in uploaded_files.items():
        if file_path and Path(file_path).exists():
            try:
                pages = extract_text(file_path)
                full_text = "\n".join([page.get("text", "") for page in pages])
                classified_type = classify_document(full_text)
                target_type = classified_type if classified_type != "unknown" else doc_type
                claims = extract_claims(full_text, target_type)
                claims_by_doc[doc_type] = claims
            except Exception as e:
                print(f"Extraction error for {doc_type}: {e}")
                claims_by_doc[doc_type] = {}

    # Perform cross-document verification & assemble features
    ver_res = verify_cross_documents(claims_by_doc, form_inputs)
    state["claims_by_doc"] = claims_by_doc
    state["verification_result"] = ver_res
    return state


# --------------------------------------------------
# Step 3: Risk Assessment
# --------------------------------------------------

def assess_risk(state: LoanState):
    print("Running risk assessment & ML credit default engine...")
    ver_res = state.get("verification_result", {})
    applicant_features = ver_res.get("applicant_features", {})

    risk = calculate_risk(ver_res, applicant_features)
    
    state["risk_result"] = risk
    state["risk_score"] = risk.get("risk_score", 0)
    state["risk_level"] = risk.get("risk_level", "UNKNOWN")
    state["human_review_required"] = risk.get("human_review_required", True)
    state["findings"] = risk.get("findings", [])

    print(f"Risk Score: {state['risk_score']} / 100")
    print(f"Risk Level: {state['risk_level']}")
    print(f"Human Review Required: {state['human_review_required']}")
    return state


# --------------------------------------------------
# Step 4: Agent Decision & Recheck
# --------------------------------------------------

def agent_decision(state: LoanState):
    print("\nAgent reviewing verification findings...")
    findings = state.get("findings", [])
    if state.get("human_review_required", False):
        print("Decision: HUMAN REVIEW REQUIRED")
        for finding in findings:
            print(f" - {finding}")
    else:
        print("Decision: APPLICATION CAN PROCEED FOR AUTO APPROVAL")
    return state


def recheck_evidence(state: LoanState):
    print("\nRe-checking evidence consistency...")
    findings = state.get("findings", [])
    if findings:
        state["human_review_required"] = True
    else:
        state["human_review_required"] = False
    return state


def route_after_decision(state: LoanState):
    if state.get("human_review_required", False):
        return "recheck"
    return "proceed"


def route_after_recheck(state: LoanState):
    if state.get("human_review_required", False):
        return "human_review"
    return "proceed"


def human_review(state: LoanState):
    print("\nRouting to Human Review Officer...")
    return state


def proceed_application(state: LoanState):
    print("\nApplication cleared for Auto-Approval.")
    return state


# --------------------------------------------------
# Step 5: Generate Summary & AI Explanation
# --------------------------------------------------

def generate_explanation(state: LoanState):
    print("Generating explainable loan summary...")
    loan_id = state.get("loan_id", "LN-2026-0001")
    risk_res = state.get("risk_result", {})
    ver_res = state.get("verification_result", {})
    
    missing_docs = ver_res.get("missing_documents", [])
    income_res = ver_res.get("income_result")
    identity_res = ver_res.get("identity_result", {})
    profile_res = ver_res.get("profile_results", [])
    
    # Template summary
    summary_text = generate_summary(
        loan_id,
        risk_res,
        missing_docs,
        income_res,
        income_res,
        None,
        profile_res,
        identity_res
    )
    
    # Grounded AI Summary via Ollama / Fallback
    ai_summary = generate_ai_summary(
        loan_id,
        risk_res,
        missing_docs,
        income_res,
        income_res,
        None,
        profile_res,
        identity_res
    )
    
    state["summary"] = summary_text
    state["ai_summary"] = ai_summary
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
builder.add_edge("start_process", "verify_loan")
builder.add_edge("verify_loan", "assess_risk")
builder.add_edge("assess_risk", "agent_decision")

builder.add_conditional_edges(
    "agent_decision",
    route_after_decision,
    {
        "recheck": "recheck_evidence",
        "proceed": "proceed"
    }
)

builder.add_conditional_edges(
    "recheck_evidence",
    route_after_recheck,
    {
        "human_review": "human_review",
        "proceed": "proceed"
    }
)

builder.add_edge("human_review", "generate_explanation")
builder.add_edge("proceed", "generate_explanation")
builder.add_edge("generate_explanation", END)

loan_graph = builder.compile()


if __name__ == "__main__":
    # Test workflow with pre-generated files for Loan 4
    base_path = Path(__file__).resolve().parent.parent / "data" / "documents" / "loan_4"
    uploaded_files = {
        "payslip": base_path / "payslip.pdf",
        "bank_statement": base_path / "bank_statement.pdf",
        "tax_return": base_path / "tax_return.pdf",
        "kyc": base_path / "kyc.pdf"
    }
    form_inputs = {
        "cibil_score": 467,
        "loan_amount": 30700000,
        "loan_term": 8,
        "no_of_dependents": 3,
        "education": "Graduate",
        "self_employed": "No",
        "residential_assets_value": 18200000,
        "commercial_assets_value": 3300000,
        "luxury_assets_value": 23300000
    }
    
    result = loan_graph.invoke({
        "loan_id": "LN-2026-1004",
        "client_name": "Applicant 4",
        "uploaded_files": uploaded_files,
        "form_inputs": form_inputs
    })

    print("\nLoanLens Agent Live Intake Execution Completed.")
    print("Final Risk Level:", result.get("risk_level"))
    print("Human Review Required:", result.get("human_review_required"))