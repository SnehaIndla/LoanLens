import os
from typing import TypedDict, List, Dict, Optional, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

class DiscrepancyRecord(TypedDict):
    field: str
    declared_value: str
    extracted_value: str
    severity: Literal["low", "medium", "high"]

class LoanCaseState(TypedDict):
    # Identity
    case_id: str
    applicant_id: str

    # Intake
    file_uris: List[str]
    missing_documents: List[str]

    # Classification + Extraction outputs
    documents: List[Dict]              # [{file_uri, doc_type, confidence}]
    extracted_fields: Dict[str, Dict]  # doc_type -> extracted JSON

    # Validation outputs
    declared_record: Dict              # Kaggle-schema fields for this applicant
    discrepancies: List[DiscrepancyRecord]

    # Risk outputs
    risk_score: int
    risk_flags: List[str]
    similar_cases: List[Dict]

    # Guardrail outcome
    guardrail_route: Literal["auto_proceed", "escalate"]

    # Summary
    summary: Optional[Dict]

    # Human decision
    officer_decision: Optional[Literal["approved", "rejected", "more_info"]]
    officer_id: Optional[str]

    # Control flow
    retry_count: int
    error: Optional[str]


# --- Node Stubs ---

def intake_node(state: LoanCaseState) -> LoanCaseState:
    if state.get("retry_count", 0) >= 3:
        state["error"] = "max_retries_exceeded"
        state["guardrail_route"] = "escalate"
    
    if "missing_documents" not in state:
        state["missing_documents"] = []
    return state

def classification_node(state: LoanCaseState) -> LoanCaseState:
    if "documents" not in state:
        state["documents"] = []
    return state

def extraction_node(state: LoanCaseState) -> LoanCaseState:
    if "extracted_fields" not in state:
        state["extracted_fields"] = {}
    return state

def validation_node(state: LoanCaseState) -> LoanCaseState:
    if "declared_record" not in state:
        state["declared_record"] = {}
    if "discrepancies" not in state:
        state["discrepancies"] = []
    return state

def risk_scoring_node(state: LoanCaseState) -> LoanCaseState:
    if "risk_flags" not in state:
        state["risk_flags"] = []
    if "similar_cases" not in state:
        state["similar_cases"] = []
    return state

def guardrail_node(state: LoanCaseState) -> LoanCaseState:
    # Deterministic rule check
    state["guardrail_route"] = route_after_guardrail(state)
    return state

def summary_node(state: LoanCaseState) -> LoanCaseState:
    if "summary" not in state:
        state["summary"] = {}
    return state

def escalate_note_node(state: LoanCaseState) -> LoanCaseState:
    # Attaches escalation reason(s) to the case
    return state

def await_human_review_node(state: LoanCaseState) -> LoanCaseState:
    # Interrupt point
    return state

def update_status_node(state: LoanCaseState) -> LoanCaseState:
    return state

def audit_log_node(state: LoanCaseState) -> LoanCaseState:
    return state


# --- Routing Logic ---

def route_after_guardrail(state: LoanCaseState) -> str:
    if state.get("error") == "max_retries_exceeded":
        return "escalate"

    discrepancies = state.get("discrepancies", [])
    high_severity = any(d.get("severity") == "high" for d in discrepancies)
    
    risk_score = state.get("risk_score", 0)
    missing_docs = state.get("missing_documents", [])
    
    if (
        risk_score >= 70
        or high_severity
        or len(missing_docs) > 0
    ):
        return "escalate"
    return "auto_proceed"

def route_after_human_decision(state: LoanCaseState) -> str:
    decision = state.get("officer_decision")
    if decision == "more_info":
        state["retry_count"] = state.get("retry_count", 0) + 1
    return decision


# --- Graph Construction ---

def build_supervisor_graph() -> StateGraph:
    graph = StateGraph(LoanCaseState)
    
    # Add nodes
    graph.add_node("intake", intake_node)
    graph.add_node("classification", classification_node)
    graph.add_node("extraction", extraction_node)
    graph.add_node("validation", validation_node)
    graph.add_node("risk_scoring", risk_scoring_node)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("summary", summary_node)
    graph.add_node("escalate_note", escalate_note_node)
    graph.add_node("await_human_review", await_human_review_node)
    graph.add_node("update_status", update_status_node)
    graph.add_node("audit_log", audit_log_node)

    # Add edges
    graph.set_entry_point("intake")
    
    graph.add_edge("intake", "classification")
    graph.add_edge("classification", "extraction")
    graph.add_edge("extraction", "validation")
    graph.add_edge("validation", "risk_scoring")
    graph.add_edge("risk_scoring", "guardrail")

    # Guardrail branching
    graph.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {"auto_proceed": "summary", "escalate": "escalate_note"},
    )

    graph.add_edge("summary", "await_human_review")
    graph.add_edge("escalate_note", "await_human_review")

    # Human review branching
    graph.add_conditional_edges(
        "await_human_review",
        route_after_human_decision,
        {
            "approved": "update_status",
            "rejected": "update_status",
            "more_info": "intake",
        },
    )

    graph.add_edge("update_status", "audit_log")
    graph.add_edge("audit_log", END)
    
    return graph


# --- Supervisor Application Singleton ---

POSTGRES_URL = os.environ.get("POSTGRES_URL", "postgresql://localhost:5432/postgres")
_app = None

def get_app():
    global _app
    if _app is not None:
        return _app
        
    graph = build_supervisor_graph()
    
    try:
        checkpointer = PostgresSaver.from_conn_string(POSTGRES_URL)
    except Exception as e:
        print(f"Warning: Could not initialize PostgresSaver ({e}). Checkpointer disabled.")
        checkpointer = None

    _app = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["await_human_review"],  # pause BEFORE human review
    )
    return _app


# --- Public API ---

def run_case(case_id: str, initial_state: dict):
    """Start or resume a case processing pipeline."""
    app = get_app()
    return app.invoke(initial_state, config={"configurable": {"thread_id": case_id}})

def resume_case(case_id: str, decision: Literal["approved", "rejected", "more_info"], officer_id: str = None):
    """Resume a case that is paused waiting for human review."""
    app = get_app()
    app.update_state(
        config={"configurable": {"thread_id": case_id}},
        values={"officer_decision": decision, "officer_id": officer_id},
    )
    return app.invoke(None, config={"configurable": {"thread_id": case_id}})
