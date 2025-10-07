from typing import Dict, Any, Optional
import asyncio
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
import time

from models.state import AgentState
from models.schemas import PatientQuery
from agents import (
    SupervisorAgent, TriageAgent, AppointmentAgent,
    VirtualAssistantAgent, ClinicalDocsAgent
)


class CardiologyWorkflow:
    """Enhanced LangGraph workflow for coordinating cardiology agents with reactive capabilities"""
    
    def __init__(self):
        # Initialize all agents
        self.supervisor = SupervisorAgent()
        self.triage_agent = TriageAgent()
        self.appointment_agent = AppointmentAgent()
        self.virtual_assistant = VirtualAssistantAgent()
        self.clinical_docs_agent = ClinicalDocsAgent()
        
        # Build the reactive workflow graph
        self.workflow = self._build_enhanced_workflow()
    
    def _build_enhanced_workflow(self) -> StateGraph:
        """Build the enhanced LangGraph workflow with proper agent routing"""
        
        # Create the graph with our comprehensive state
        workflow = StateGraph(AgentState)
        
        # Add all agent nodes
        workflow.add_node("supervisor", self._supervisor_node)
        workflow.add_node("triage_agent", self._triage_node)
        workflow.add_node("appointment_agent", self._appointment_node)
        workflow.add_node("virtual_assistant_agent", self._virtual_assistant_node)
        workflow.add_node("clinical_docs_agent", self._clinical_docs_node)
        workflow.add_node("workflow_complete", self._completion_node)
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        # Define routing logic from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self._route_from_supervisor,
            {
                "triage_agent": "triage_agent",
                "appointment_agent": "appointment_agent", 
                "virtual_assistant_agent": "virtual_assistant_agent",
                "clinical_docs_agent": "clinical_docs_agent",
                "end": END
            }
        )
        
        # Define routing from triage agent
        workflow.add_conditional_edges(
            "triage_agent",
            self._route_from_triage,
            {
                "appointment_agent": "appointment_agent",
                "virtual_assistant_agent": "virtual_assistant_agent",
                "emergency_end": END,
                "complete": "workflow_complete"
            }
        )
        
        # Define routing from appointment agent
        workflow.add_conditional_edges(
            "appointment_agent", 
            self._route_from_appointment,
            {
                "virtual_assistant_agent": "virtual_assistant_agent",
                "complete": "workflow_complete"
            }
        )
        
        # Virtual assistant and clinical docs typically end workflow
        workflow.add_edge("virtual_assistant_agent", "workflow_complete")
        workflow.add_edge("clinical_docs_agent", "workflow_complete")
        workflow.add_edge("workflow_complete", END)
        
        return workflow.compile()
    
    def _supervisor_node(self, state: AgentState) -> AgentState:
        """Execute supervisor agent"""
        return self.supervisor(state)
    
    def _triage_node(self, state: AgentState) -> AgentState:
        """Execute triage agent"""
        return self.triage_agent(state)
    
    def _appointment_node(self, state: AgentState) -> AgentState:
        """Execute appointment agent"""
        return self.appointment_agent(state)
    
    def _virtual_assistant_node(self, state: AgentState) -> AgentState:
        """Execute virtual assistant agent"""
        return self.virtual_assistant(state)
    
    def _clinical_docs_node(self, state: AgentState) -> AgentState:
        """Execute clinical documentation agent"""
        return self.clinical_docs_agent(state)
    
    def _completion_node(self, state: AgentState) -> AgentState:
        """Mark workflow as complete and provide summary"""
        
        # Generate workflow summary
        agents_used = [transition["to_agent"] for transition in state.get("agent_transitions", [])]
        tools_used = state.get("tools_used", [])
        
        summary_message = f"""
🏥 Cardiology AI Consultation Complete

WORKFLOW SUMMARY:
- Agents Consulted: {', '.join(set(agents_used))}
- Tools Used: {', '.join(set(tools_used))}
- Processing Time: {state.get('processing_time', 0):.2f}s
- Urgency Level: {state.get('urgency_level', 'Not assessed')}

RECOMMENDATIONS:
{self._generate_final_recommendations(state)}

Thank you for using our Cardiology AI system. If you have additional questions or concerns, please don't hesitate to ask.
"""
        
        return {
            **state,
            "workflow_complete": True,
            "current_agent": "workflow_complete",
            "messages": state["messages"] + [AIMessage(content=summary_message.strip())]
        }
    
    def _route_from_supervisor(self, state: AgentState) -> str:
        """Route from supervisor based on analysis"""
        next_agent = state.get("next_agent")
        
        if next_agent in ["triage_agent", "appointment_agent", "virtual_assistant_agent", "clinical_docs_agent"]:
            return next_agent
        return "end"
    
    def _route_from_triage(self, state: AgentState) -> str:
        """Route from triage based on urgency and results"""
        urgency = state.get("urgency_level")
        escalation_needed = state.get("escalation_needed", False)
        
        if urgency == "emergency":
            return "emergency_end"  # End immediately for emergencies
        elif escalation_needed or urgency == "urgent":
            return "appointment_agent"  # Schedule urgent appointment
        elif state.get("next_agent") == "virtual_assistant_agent":
            return "virtual_assistant_agent"
        else:
            return "complete"
    
    def _route_from_appointment(self, state: AgentState) -> str:
        """Route from appointment agent"""
        if state.get("appointment_scheduled"):
            return "virtual_assistant_agent"  # Provide follow-up education
        return "complete"
    
    def _generate_final_recommendations(self, state: AgentState) -> str:
        """Generate final recommendations based on workflow results"""
        
        recommendations = []
        
        # Triage recommendations
        if state.get("triage_result"):
            triage = state["triage_result"]
            recommendations.append(f"- {triage.get('recommended_action', 'Follow standard care protocols')}")
        
        # Appointment recommendations
        if state.get("appointment_data"):
            appointment = state["appointment_data"]
            if appointment.get("scheduled"):
                recommendations.append(f"- Appointment scheduled for {appointment.get('date', 'TBD')}")
        
        # General recommendations
        urgency = state.get("urgency_level")
        if urgency == "emergency":
            recommendations.append("- Seek immediate emergency medical attention")
        elif urgency == "urgent":
            recommendations.append("- Contact your cardiologist within 24 hours")
        else:
            recommendations.append("- Continue regular cardiac care routine")
        
        # Medication and lifestyle
        if state.get("clinical_notes"):
            recommendations.append("- Follow medication and lifestyle guidance provided")
        
        return "\\n".join(recommendations) if recommendations else "Continue standard care protocols"
    
    async def process_patient_query(self, patient_query: PatientQuery, 
                                  session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a patient query through the enhanced multi-agent workflow"""
        
        start_time = time.time()
        
        # Initialize comprehensive state
        initial_state: AgentState = {
            "messages": [HumanMessage(content=patient_query.query)],
            "conversation_id": patient_query.conversation_id,
            "session_context": session_context or {},
            "patient_id": patient_query.patient_id,
            "patient_data": None,
            "query_type": None,
            "original_query": patient_query.query,
            "current_agent": None,
            "next_agent": None,
            "triage_result": None,
            "appointment_data": None,
            "clinical_context": None,
            "virtual_assistant_context": None,
            "urgency_level": None,
            "escalation_needed": False,
            "appointment_scheduled": False,
            "requires_human_review": False,
            "workflow_complete": False,
            "tools_used": [],
            "external_calls": [],
            "clinical_notes": [],
            "diagnosis_codes": [],
            "medications_mentioned": [],
            "conversation_history": [],
            "agent_transitions": [],
            "processing_time": 0.0,
            "confidence_scores": {}
        }
        
        try:
            # Execute the workflow
            result = await self.workflow.ainvoke(initial_state)
            
            # Calculate total processing time
            total_time = time.time() - start_time
            result["processing_time"] = total_time
            
            # Extract final response
            final_message = result["messages"][-1].content if result["messages"] else "No response generated"
            
            # Return structured result
            return {
                "response": final_message,
                "conversation_id": result.get("conversation_id"),
                "urgency_level": result.get("urgency_level"),
                "escalation_needed": result.get("escalation_needed", False),
                "appointment_scheduled": result.get("appointment_scheduled", False),
                "requires_human_review": result.get("requires_human_review", False),
                "agents_consulted": [t["to_agent"] for t in result.get("agent_transitions", [])],
                "tools_used": result.get("tools_used", []),
                "clinical_notes": result.get("clinical_notes", []),
                "processing_time": total_time,
                "confidence_scores": result.get("confidence_scores", {}),
                "session_context": result.get("session_context", {})
            }
            
        except Exception as e:
            return {
                "response": f"System Error: {str(e)}. Please contact support.",
                "error": str(e),
                "requires_human_review": True,
                "processing_time": time.time() - start_time
            }
    
    def get_workflow_visualization(self) -> str:
        """Generate Mermaid diagram for workflow visualization"""
        return '''
graph TD
    Start([User Query]) --> Supervisor{Supervisor Agent}
    
    Supervisor -->|Emergency Symptoms| Triage[Triage Agent]
    Supervisor -->|Appointment Request| Appointment[Appointment Agent]
    Supervisor -->|General Questions| VirtualAssistant[Virtual Assistant]
    Supervisor -->|Documentation| ClinicalDocs[Clinical Docs Agent]
    
    Triage -->|Emergency| Emergency[🚨 Emergency Escalation]
    Triage -->|Urgent| Appointment
    Triage -->|Routine| VirtualAssistant
    
    Appointment -->|Scheduled| VirtualAssistant
    Appointment -->|Complete| Complete[Workflow Complete]
    
    VirtualAssistant --> Complete
    ClinicalDocs --> Complete
    Emergency --> End([End - Human Review])
    Complete --> End
    
    style Start fill:#e1f5fe
    style Supervisor fill:#fff3e0
    style Triage fill:#ffebee
    style Appointment fill:#e8f5e8
    style VirtualAssistant fill:#f3e5f5
    style ClinicalDocs fill:#e3f2fd
    style Emergency fill:#ff5252,color:#fff
    style Complete fill:#4caf50,color:#fff
    style End fill:#9e9e9e,color:#fff
'''
        
        # Define the routing logic
        workflow.add_conditional_edges(
            "supervisor",
            self._route_to_agent,
            {
                "TRIAGE_AGENT": "triage",
                "APPOINTMENT_AGENT": "appointment", 
                "VIRTUAL_ASSISTANT": "virtual_assistant",
                "CLINICAL_DOCS": "clinical_docs",
                "END": END
            }
        )
        
        # All agents can end or continue to supervisor for further routing
        for agent in ["triage", "appointment", "virtual_assistant", "clinical_docs"]:
            workflow.add_conditional_edges(
                agent,
                self._should_continue,
                {
                    "continue": "supervisor",
                    "end": END
                }
            )
        
        # Set entry point
        workflow.set_entry_point("supervisor")
        
        return workflow.compile()
    
    def _supervisor_node(self, state: AgentState) -> Dict[str, Any]:
        """Supervisor agent node"""
        
        # Get the latest message
        last_message = state["messages"][-1] if state["messages"] else None
        query = last_message.content if last_message else ""
        
        # Route to appropriate agent
        next_agent = self.supervisor.route_query(query, {
            "patient_id": state.get("patient_id"),
            "conversation_history": state.get("conversation_history", [])
        })
        
        return {
            "current_agent": next_agent,
            "messages": state["messages"]
        }
    
    def _triage_node(self, state: AgentState) -> Dict[str, Any]:
        """Triage agent node"""
        
        # Get patient data
        patient_data = self.patient_lookup.lookup_patient(state["patient_id"]) or {}
        
        # Get query from latest message
        last_message = state["messages"][-1] if state["messages"] else None
        query = last_message.content if last_message else ""
        
        # Perform triage assessment
        assessment = self.triage_agent.assess(query, patient_data)
        
        # Check for emergency escalation
        emergency_assessment = self.emergency_escalation.assess_emergency_level(query, patient_data)
        
        response_data = {
            "triage_result": assessment.dict(),
            "emergency_assessment": emergency_assessment,
            "current_agent": "triage"
        }
        
        # Handle emergency if detected
        if emergency_assessment["requires_immediate_action"]:
            emergency_response = self.emergency_escalation.trigger_emergency_response(
                emergency_assessment, patient_data
            )
            response_data["emergency_response"] = emergency_response
            self.emergency_escalation.log_escalation(emergency_response)
        
        return response_data
    
    def _appointment_node(self, state: AgentState) -> Dict[str, Any]:
        """Appointment agent node"""
        
        # Get patient data
        patient_data = self.patient_lookup.lookup_patient(state["patient_id"]) or {}
        
        # Get query from latest message
        last_message = state["messages"][-1] if state["messages"] else None
        query = last_message.content if last_message else ""
        
        # Determine urgency from triage if available
        urgency = "routine"
        if state.get("triage_result"):
            urgency = state["triage_result"]["urgency_level"]
        
        # Process appointment request
        appointment_result = self.appointment_agent.schedule_appointment(
            state["patient_id"], query, patient_data, urgency
        )
        
        return {
            "appointment_data": appointment_result,
            "current_agent": "appointment"
        }
    
    def _virtual_assistant_node(self, state: AgentState) -> Dict[str, Any]:
        """Virtual assistant agent node"""
        
        # Get patient data
        patient_data = self.patient_lookup.lookup_patient(state["patient_id"]) or {}
        
        # Get query from latest message
        last_message = state["messages"][-1] if state["messages"] else None
        query = last_message.content if last_message else ""
        
        # Provide assistance
        assistance_result = self.virtual_assistant.provide_assistance(query, patient_data)
        
        return {
            "clinical_context": assistance_result,
            "current_agent": "virtual_assistant"
        }
    
    def _clinical_docs_node(self, state: AgentState) -> Dict[str, Any]:
        """Clinical documentation agent node"""
        
        # Get patient data
        patient_data = self.patient_lookup.lookup_patient(state["patient_id"]) or {}
        
        # Get query from latest message
        last_message = state["messages"][-1] if state["messages"] else None
        query = last_message.content if last_message else ""
        
        # Generate clinical documentation
        if "summary" in query.lower():
            doc_result = self.clinical_docs_agent.generate_clinical_summary(
                patient_data, state.get("conversation_history", [])
            )
        elif "discharge" in query.lower():
            procedure_type = "general"  # Extract from query in production
            doc_result = self.clinical_docs_agent.create_discharge_instructions(
                patient_data, procedure_type
            )
        else:
            doc_result = {"message": "Clinical documentation request processed"}
        
        return {
            "clinical_context": doc_result,
            "current_agent": "clinical_docs"
        }
    
    def _route_to_agent(self, state: AgentState) -> str:
        """Determine which agent to route to"""
        return state.get("current_agent", "END")
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if workflow should continue or end"""
        
        # Check if emergency response was triggered
        if state.get("emergency_response"):
            return "end"
        
        # Check if a handoff is needed
        last_message = state["messages"][-1] if state["messages"] else None
        if last_message and "handoff" in last_message.content.lower():
            return "continue"
        
        # Default to ending after agent processing
        return "end"
    
    async def process_query(self, patient_query: PatientQuery, conversation_context: Dict) -> Dict[str, Any]:
        """Process a patient query through the workflow"""
        
        # Initialize state
        initial_state = {
            "messages": [HumanMessage(content=patient_query.query_text)],
            "patient_id": patient_query.patient_id,
            "query_type": patient_query.query_type or "general",
            "current_agent": "supervisor",
            "conversation_history": conversation_context.get("history", []),
            "requires_human_review": False
        }
        
        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state)
        
        # Format response
        response = self._format_response(final_state)
        
        return response
    
    def _format_response(self, state: AgentState) -> Dict[str, Any]:
        """Format the final response from workflow execution"""
        
        agent_used = state.get("current_agent", "unknown")
        
        # Build response based on which agent processed the query
        if agent_used == "triage":
            triage_result = state.get("triage_result", {})
            emergency_response = state.get("emergency_response")
            
            if emergency_response:
                response_text = f"EMERGENCY DETECTED: {emergency_response['immediate_action']}\n\n"
                response_text += "\n".join(emergency_response.get("instructions", []))
                
                return {
                    "response": response_text,
                    "agent_used": "triage",
                    "structured_data": {
                        "triage_assessment": triage_result,
                        "emergency_response": emergency_response
                    },
                    "emergency_alert": True,
                    "requires_follow_up": True
                }
            else:
                return {
                    "response": f"Triage Assessment Complete:\n"
                              f"Urgency Level: {triage_result.get('urgency_level', 'unknown')}\n"
                              f"Recommended Action: {triage_result.get('recommended_action', 'Please consult your healthcare provider')}\n"
                              f"Reasoning: {triage_result.get('reasoning', 'Assessment completed')}",
                    "agent_used": "triage",
                    "structured_data": {"triage_assessment": triage_result},
                    "requires_follow_up": triage_result.get("escalation_required", False)
                }
        
        elif agent_used == "appointment":
            appointment_data = state.get("appointment_data", {})
            return {
                "response": f"Appointment Request Processed:\n"
                          f"Type: {appointment_data.get('appointment_type', 'consultation')}\n"
                          f"Suggested Dates: {', '.join(appointment_data.get('suggested_dates', []))}\n"
                          f"Duration: {appointment_data.get('estimated_duration', '60 minutes')}\n"
                          f"Instructions: {appointment_data.get('pre_appointment_instructions', 'None')}",
                "agent_used": "appointment",
                "structured_data": {"appointment_data": appointment_data},
                "requires_follow_up": appointment_data.get("requires_approval", False)
            }
        
        elif agent_used == "virtual_assistant":
            clinical_context = state.get("clinical_context", {})
            return {
                "response": clinical_context.get("response", "I'm here to help with your cardiology questions."),
                "agent_used": "virtual_assistant",
                "structured_data": {"assistance_data": clinical_context},
                "requires_follow_up": clinical_context.get("follow_up_recommended", False)
            }
        
        elif agent_used == "clinical_docs":
            clinical_context = state.get("clinical_context", {})
            return {
                "response": clinical_context.get("summary", clinical_context.get("instructions", "Documentation processed.")),
                "agent_used": "clinical_docs",
                "structured_data": {"documentation": clinical_context},
                "requires_follow_up": False
            }
        
        else:
            return {
                "response": "I'm here to help with your cardiology needs. How can I assist you today?",
                "agent_used": "supervisor",
                "structured_data": {},
                "requires_follow_up": False
            }
    
    # Additional utility methods
    async def run_triage_assessment(self, patient_id: str, query: str, context: Dict) -> Dict:
        """Run triage assessment specifically"""
        patient_query = PatientQuery(patient_id=patient_id, query_text=query, query_type="triage")
        return await self.process_query(patient_query, context)
    
    async def handle_appointment_request(self, patient_id: str, query: str, context: Dict) -> Dict:
        """Handle appointment request specifically"""
        patient_query = PatientQuery(patient_id=patient_id, query_text=query, query_type="appointment")
        return await self.process_query(patient_query, context)
    
    def get_patient_appointments(self, patient_id: str) -> list:
        """Get patient appointments"""
        return self.appointment_system.get_patient_appointments(patient_id)
    
    def get_patient_info(self, patient_id: str) -> Optional[Dict]:
        """Get patient information"""
        return self.patient_lookup.lookup_patient(patient_id)