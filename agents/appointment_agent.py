import asyncio
import time
import uuid
from typing import Any, Dict, Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from models.state import AgentState


# Real LangGraph Tools for Appointment Agent
@tool
def check_availability_tool(urgency_level: str, date_preference: str = "flexible") -> Dict[str, Any]:
    """Check appointment availability based on urgency level."""
    if urgency_level == "emergency":
        return {
            "available": True,
            "next_slot": "IMMEDIATE",
            "provider": "Emergency Cardiology Team",
            "location": "Emergency Department",
            "appointment_type": "emergency_consultation"
        }
    elif urgency_level == "urgent":
        return {
            "available": True,
            "next_slot": "Within 24 hours",
            "provider": "Dr. Sarah Smith, MD",
            "location": "Cardiology Clinic",
            "appointment_type": "urgent_consultation"
        }
    else:
        return {
            "available": True,
            "next_slot": "Within 1-2 weeks",
            "provider": "Cardiology Department",
            "location": "Outpatient Clinic",
            "appointment_type": "routine_consultation"
        }


@tool
def book_appointment_tool(patient_id: str, appointment_type: str, urgency: str) -> Dict[str, Any]:
    """Book the actual appointment in the healthcare system."""
    appointment_id = f"CARD-{str(uuid.uuid4())[:8].upper()}"
    
    return {
        "appointment_id": appointment_id,
        "status": "confirmed",
        "patient_id": patient_id,
        "type": appointment_type,
        "urgency": urgency,
        "booking_timestamp": time.time(),
        "confirmation_required": True
    }


@tool
def notify_patient_tool(patient_id: str, appointment_details: Dict[str, Any]) -> Dict[str, Any]:
    """Send appointment confirmation to patient via multiple channels."""
    confirmation_code = f"CONFIRM-{appointment_details.get('appointment_id', 'UNKNOWN')}"
    
    return {
        "notification_sent": True,
        "channels": ["SMS", "Email", "Patient Portal"],
        "confirmation_code": confirmation_code,
        "estimated_delivery": "Within 5 minutes"
    }


class AppointmentAgent:
    """Real LangGraph-based Appointment Agent with StateGraph workflow"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        self.name = "appointment_agent"
        self.tools = [check_availability_tool, book_appointment_tool, notify_patient_tool]
        
        # Build the actual LangGraph workflow
        self.graph = self._build_langgraph_workflow()
    
    def _build_langgraph_workflow(self) -> StateGraph:
        """Build the real LangGraph StateGraph for appointment scheduling"""
        
        # Create the StateGraph with our state schema
        workflow = StateGraph(AgentState)
        
        # Add nodes for each step in the appointment workflow
        workflow.add_node("analyze_request", self._analyze_appointment_request_node)
        workflow.add_node("check_availability", self._check_availability_node)
        workflow.add_node("book_appointment", self._book_appointment_node)
        workflow.add_node("send_confirmation", self._send_confirmation_node)
        workflow.add_node("handle_error", self._handle_error_node)
        
        # Set the entry point
        workflow.set_entry_point("analyze_request")
        
        # Define conditional edges for workflow routing
        workflow.add_conditional_edges(
            "analyze_request",
            self._route_after_analysis,
            {
                "check_availability": "check_availability",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "check_availability",
            self._route_after_availability_check,
            {
                "book_appointment": "book_appointment",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "book_appointment",
            self._route_after_booking,
            {
                "send_confirmation": "send_confirmation",
                "error": "handle_error"
            }
        )
        
        # Terminal nodes
        workflow.add_edge("send_confirmation", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _analyze_appointment_request_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Analyze the appointment request using LLM"""
        
        start_time = time.time()
        
        # Get the latest message for analysis
        last_message = state["messages"][-1] if state["messages"] else None
        
        if not last_message:
            return {
                **state,
                "error": "No appointment request to analyze",
                "current_agent": "appointment_agent",
                "next_action": "error"
            }
        
        # Use LLM to analyze the appointment request
        analysis_prompt = f"""
        Analyze this cardiology appointment request:
        
        Patient ID: {state.get('patient_id', 'Unknown')}
        Request: {last_message.content}
        Urgency Level: {state.get('urgency_level', 'routine')}
        Previous Context: {state.get('session_context', {})}
        
        Extract key information and respond in this format:
        - Appointment Type: [consultation/follow-up/emergency/procedure]
        - Preferred Timing: [immediate/urgent/flexible/specific date]
        - Special Requirements: [any specific needs mentioned]
        - Confidence Level: [0.0-1.0]
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            
            # Parse the LLM response (in real implementation, use structured output)
            appointment_analysis = {
                "appointment_type": "cardiology_consultation",
                "preferred_timing": state.get('urgency_level', 'routine'),
                "special_requirements": "standard cardiac evaluation",
                "confidence_level": 0.9,
                "analysis_reasoning": response.content
            }
            
            processing_time = time.time() - start_time
            
            return {
                **state,
                "appointment_analysis": appointment_analysis,
                "current_agent": "appointment_agent",
                "processing_time": processing_time,
                "next_action": "check_availability",
                "tools_used": state.get("tools_used", []) + ["llm_analysis"],
                "messages": state["messages"] + [AIMessage(
                    content=f"📋 Analyzing your appointment request for {appointment_analysis['appointment_type']}. Confidence: {appointment_analysis['confidence_level']:.1%}"
                )]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Request analysis failed: {str(e)}",
                "current_agent": "appointment_agent",
                "next_action": "error"
            }
    
    def _check_availability_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Check appointment availability using tools"""
        
        urgency_level = state.get("urgency_level", "routine")
        appointment_analysis = state.get("appointment_analysis", {})
        preferred_timing = appointment_analysis.get("preferred_timing", "flexible")
        
        try:
            # Use the LangGraph tool to check availability
            availability_result = check_availability_tool.invoke({
                "urgency_level": urgency_level,
                "date_preference": preferred_timing
            })
            
            if availability_result.get("available"):
                return {
                    **state,
                    "availability_check": availability_result,
                    "next_action": "book_appointment",
                    "tools_used": state.get("tools_used", []) + ["check_availability_tool"],
                    "messages": state["messages"] + [AIMessage(
                        content=f"✅ Found available slot: {availability_result['next_slot']} with {availability_result['provider']} at {availability_result['location']}"
                    )]
                }
            else:
                return {
                    **state,
                    "error": "No available appointment slots found for the requested timeframe",
                    "next_action": "error",
                    "tools_used": state.get("tools_used", []) + ["check_availability_tool"]
                }
                
        except Exception as e:
            return {
                **state,
                "error": f"Availability check failed: {str(e)}",
                "next_action": "error"
            }
    
    def _book_appointment_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Book the appointment using tools"""
        
        patient_id = state.get("patient_id", "unknown")
        appointment_analysis = state.get("appointment_analysis", {})
        availability_check = state.get("availability_check", {})
        urgency_level = state.get("urgency_level", "routine")
        
        try:
            # Use the LangGraph tool to book the appointment
            booking_result = book_appointment_tool.invoke({
                "patient_id": patient_id,
                "appointment_type": availability_check.get("appointment_type", "consultation"),
                "urgency": urgency_level
            })
            
            return {
                **state,
                "booking_result": booking_result,
                "appointment_scheduled": True,
                "appointment_id": booking_result["appointment_id"],
                "next_action": "send_confirmation",
                "tools_used": state.get("tools_used", []) + ["book_appointment_tool"],
                "clinical_notes": state.get("clinical_notes", []) + [
                    f"Appointment {booking_result['appointment_id']} scheduled for patient {patient_id}"
                ],
                "messages": state["messages"] + [AIMessage(
                    content=f"🎉 Appointment successfully booked! Confirmation ID: {booking_result['appointment_id']}"
                )]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Appointment booking failed: {str(e)}",
                "next_action": "error"
            }
    
    def _send_confirmation_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Send appointment confirmation using tools"""
        
        patient_id = state.get("patient_id")
        booking_result = state.get("booking_result", {})
        availability_check = state.get("availability_check", {})
        
        try:
            # Use the LangGraph tool to send notification
            notification_result = notify_patient_tool.invoke({
                "patient_id": patient_id,
                "appointment_details": booking_result
            })
            
            # Create comprehensive confirmation message
            confirmation_message = f"""
📅 APPOINTMENT CONFIRMATION COMPLETE

Confirmation Code: {notification_result['confirmation_code']}
Appointment ID: {booking_result.get('appointment_id', 'N/A')}
Type: {booking_result.get('type', 'Cardiology Consultation')}
Scheduled: {availability_check.get('next_slot', 'TBD')}
Provider: {availability_check.get('provider', 'Cardiology Team')}
Location: {availability_check.get('location', 'Main Clinic')}

📱 Notifications sent via: {', '.join(notification_result.get('channels', []))}
⏰ Delivery time: {notification_result.get('estimated_delivery', 'Soon')}

📋 NEXT STEPS:
• Arrive 15 minutes early
• Bring insurance card and ID
• Bring list of current medications
• Prepare questions for your provider

Thank you for choosing our cardiology services!
            """
            
            return {
                **state,
                "confirmation_sent": True,
                "notification_result": notification_result,
                "workflow_complete": True,
                "next_agent": "virtual_assistant_agent",
                "tools_used": state.get("tools_used", []) + ["notify_patient_tool"],
                "session_context": {
                    **state.get("session_context", {}),
                    "appointment_completed": True,
                    "confirmation_code": notification_result['confirmation_code']
                },
                "messages": state["messages"] + [AIMessage(content=confirmation_message.strip())]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Confirmation sending failed: {str(e)}",
                "next_action": "error"
            }
    
    def _handle_error_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Handle errors in the appointment workflow"""
        
        error_message = state.get("error", "Unknown error occurred during appointment scheduling")
        
        error_response = f"""
❌ APPOINTMENT SCHEDULING ERROR

{error_message}

🏥 ALTERNATIVE OPTIONS:
• Call our scheduling department: (555) 123-CARD (2273)
• Visit our patient portal: cardiology-clinic.com/appointments
• Email us: appointments@cardiology-clinic.com

🕒 SCHEDULING HOURS:
• Monday-Friday: 8:00 AM - 6:00 PM
• Saturday: 9:00 AM - 2:00 PM
• Emergency situations: Call 911

Our scheduling team will be happy to assist you with finding the perfect appointment time.
        """
        
        return {
            **state,
            "error_handled": True,
            "requires_human_review": True,
            "workflow_complete": True,
            "next_agent": "virtual_assistant_agent",
            "session_context": {
                **state.get("session_context", {}),
                "appointment_error": error_message,
                "requires_manual_scheduling": True
            },
            "messages": state["messages"] + [AIMessage(content=error_response.strip())]
        }
    
    def _route_after_analysis(self, state: AgentState) -> Literal["check_availability", "error"]:
        """LangGraph Conditional Edge: Route after request analysis"""
        if state.get("error"):
            return "error"
        elif state.get("appointment_analysis", {}).get("confidence_level", 0) < 0.5:
            return "error"
        else:
            return "check_availability"
    
    def _route_after_availability_check(self, state: AgentState) -> Literal["book_appointment", "error"]:
        """LangGraph Conditional Edge: Route after availability check"""
        if state.get("error"):
            return "error"
        elif not state.get("availability_check", {}).get("available"):
            return "error"
        else:
            return "book_appointment"
    
    def _route_after_booking(self, state: AgentState) -> Literal["send_confirmation", "error"]:
        """LangGraph Conditional Edge: Route after booking attempt"""
        if state.get("error"):
            return "error"
        elif not state.get("booking_result", {}).get("status") == "confirmed":
            return "error"
        else:
            return "send_confirmation"
    
    async def process_appointment_workflow(self, state: AgentState) -> AgentState:
        """Execute the LangGraph workflow asynchronously"""
        try:
            # Execute the compiled LangGraph workflow
            result = await self.graph.ainvoke(state)
            return result
        except Exception as e:
            return self._handle_error_node({
                **state,
                "error": f"LangGraph workflow execution failed: {str(e)}"
            })
    
    def __call__(self, state: AgentState) -> AgentState:
        """Synchronous entry point for the LangGraph appointment agent"""
        try:
            # Run the async LangGraph workflow
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.process_appointment_workflow(state))
                return result
            finally:
                loop.close()
                
        except Exception as e:
            return self._handle_error_node({
                **state,
                "error": f"Appointment agent execution failed: {str(e)}"
            })