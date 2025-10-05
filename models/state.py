from typing import Annotated, TypedDict, Sequence, Optional, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """Shared state across all agents"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    patient_id: str
    query_type: str
    current_agent: str
    triage_result: Optional[dict]
    appointment_data: Optional[dict]
    clinical_context: Optional[dict]
    conversation_history: List[dict]
    requires_human_review: bool