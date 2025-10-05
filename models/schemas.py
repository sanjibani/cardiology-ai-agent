from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from datetime import datetime

class SymptomAssessment(BaseModel):
    """Structured output for triage decisions"""
    symptoms: List[str]
    severity_score: int = Field(ge=1, le=10, description="1=minor, 10=critical")
    urgency_level: Literal["emergency", "urgent", "routine", "informational"]
    recommended_action: str
    escalation_required: bool
    reasoning: str

class PatientQuery(BaseModel):
    patient_id: str
    query_text: str
    query_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class AppointmentRequest(BaseModel):
    patient_id: str
    preferred_date: str
    appointment_type: Literal["consultation", "follow-up", "procedure", "emergency"]
    notes: Optional[str] = None

class AgentResponse(BaseModel):
    agent_name: str
    response_text: str
    structured_data: Optional[dict] = None
    requires_handoff: bool = False
    next_agent: Optional[str] = None

class Patient(BaseModel):
    patient_id: str
    name: str
    age: int
    conditions: List[str] = []
    medications: List[str] = []
    last_visit: Optional[str] = None
    risk_factors: List[str] = []