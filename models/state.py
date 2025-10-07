from typing import Annotated, TypedDict, Sequence, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Comprehensive shared state across all agents in the cardiology system"""
    
    # Core messaging and conversation
    messages: Annotated[Sequence[BaseMessage], add_messages]
    conversation_id: Optional[str]
    session_context: Dict[str, Any]
    
    # Patient information
    patient_id: Optional[str]
    patient_data: Optional[Dict[str, Any]]
    
    # Query processing
    query_type: Optional[str]
    original_query: Optional[str]
    current_agent: Optional[str]
    next_agent: Optional[str]
    
    # Agent-specific results
    triage_result: Optional[Dict[str, Any]]
    appointment_data: Optional[Dict[str, Any]]
    clinical_context: Optional[Dict[str, Any]]
    virtual_assistant_context: Optional[Dict[str, Any]]
    
    # Workflow control
    urgency_level: Optional[str]  # EMERGENCY, URGENT, ROUTINE
    escalation_needed: bool
    appointment_scheduled: bool
    requires_human_review: bool
    workflow_complete: bool
    
    # Tools and external integrations
    tools_used: List[str]
    external_calls: List[Dict[str, Any]]
    
    # Clinical documentation
    clinical_notes: List[str]
    diagnosis_codes: List[str]
    medications_mentioned: List[str]
    
    # Quality and monitoring
    conversation_history: List[Dict[str, Any]]
    agent_transitions: List[Dict[str, Any]]
    processing_time: Optional[float]
    confidence_scores: Dict[str, float]