from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from models.state import AgentState
import time
from typing import Dict, Any


class AppointmentAgent:
    """Enhanced LangGraph Appointment Agent with smart scheduling capabilities"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        self.name = "appointment_agent"
    
    def __call__(self, state: AgentState) -> AgentState:
        """Handle appointment scheduling with urgency-based prioritization"""
        start_time = time.time()
        
        try:
            # Get urgency level and patient info
            urgency = state.get("urgency_level", "routine")
            patient_id = state.get("patient_id")
            
            # Simulate appointment scheduling
            appointment_result = self._schedule_appointment(urgency, patient_id)
            
            # Create response message
            response_message = self._format_appointment_response(appointment_result)
            
            # Update state
            processing_time = time.time() - start_time
            
            return {
                **state,
                "current_agent": "appointment_agent",
                "appointment_data": appointment_result,
                "appointment_scheduled": appointment_result["scheduled"],
                "tools_used": state.get("tools_used", []) + ["appointment_system"],
                "processing_time": processing_time,
                "next_agent": "virtual_assistant_agent",
                "messages": state["messages"] + [AIMessage(content=response_message)]
            }
            
        except Exception as e:
            return self._create_error_response(state, f"Appointment error: {str(e)}")
    
    def _schedule_appointment(self, urgency: str, patient_id: str) -> Dict[str, Any]:
        """Schedule appointment based on urgency"""
        
        if urgency == "emergency":
            return {
                "scheduled": True,
                "type": "emergency_consultation",
                "date": "TODAY - Emergency Department",
                "time": "Immediate",
                "provider": "Emergency Cardiology Team"
            }
        elif urgency == "urgent":
            return {
                "scheduled": True,
                "type": "urgent_cardiology_consultation", 
                "date": "Within 24 hours",
                "time": "Next available",
                "provider": "Dr. Smith (Cardiologist)"
            }
        else:
            return {
                "scheduled": True,
                "type": "routine_cardiology_consultation",
                "date": "Within 1-2 weeks", 
                "time": "Available slots",
                "provider": "Cardiology Department"
            }
    
    def _format_appointment_response(self, appointment_result: Dict[str, Any]) -> str:
        """Format appointment response"""
        
        if appointment_result["scheduled"]:
            return f"""
📅 APPOINTMENT SCHEDULED

Type: {appointment_result['type']}
Date: {appointment_result['date']}
Time: {appointment_result['time']}
Provider: {appointment_result['provider']}

Your appointment has been successfully scheduled. You will receive a confirmation shortly.
"""
        else:
            return "Unable to schedule appointment at this time. Please contact our scheduling department."
    
    def _create_error_response(self, state: AgentState, error_message: str) -> AgentState:
        """Create error response state"""
        return {
            **state,
            "current_agent": "appointment_agent",
            "next_agent": "virtual_assistant_agent",
            "requires_human_review": True,
            "messages": state.get("messages", []) + [AIMessage(
                content=f"Appointment Error: {error_message}. Please contact scheduling."
            )]
        }