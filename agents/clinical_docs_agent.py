from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from models.state import AgentState
from typing import Dict, Any, List, Literal
import time
import asyncio
from datetime import datetime, timedelta


@tool
def clinical_assessment_tool(patient_data: Dict[str, Any], 
                           session_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate clinical assessment documentation"""
    
    patient_id = patient_data.get("patient_id", "Unknown")
    urgency_level = session_data.get("urgency_level", "routine")
    symptoms = session_data.get("symptoms", [])
    risk_factors = session_data.get("risk_factors", [])
    
    # Generate clinical impression
    if urgency_level == "emergency":
        clinical_impression = "Acute cardiac emergency requiring immediate intervention"
        disposition = "Emergency department transfer via EMS"
    elif urgency_level == "urgent":
        clinical_impression = "Urgent cardiac symptoms requiring same-day evaluation"
        disposition = "Urgent cardiology referral within 2-4 hours"
    elif urgency_level == "moderate":
        clinical_impression = "Moderate cardiac symptoms requiring timely evaluation"
        disposition = "Cardiology appointment within 1-2 weeks"
    else:
        clinical_impression = "Routine cardiac assessment with stable presentation"
        disposition = "Routine follow-up as clinically indicated"
    
    return {
        "patient_id": patient_id,
        "clinical_impression": clinical_impression,
        "chief_complaint": ", ".join(symptoms) if symptoms else "Cardiac consultation",
        "assessment_urgency": urgency_level,
        "disposition": disposition,
        "risk_stratification": "High" if urgency_level in ["emergency", "urgent"] else "Moderate" if urgency_level == "moderate" else "Low",
        "documentation_confidence": 0.9
    }


@tool
def treatment_plan_tool(assessment_data: Dict[str, Any],
                       patient_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive treatment plan documentation"""
    
    urgency_level = assessment_data.get("urgency_level", "routine")
    symptoms = patient_profile.get("symptoms", [])
    risk_factors = patient_profile.get("risk_factors", [])
    
    # Generate treatment recommendations
    immediate_actions = []
    follow_up_actions = []
    medications_review = []
    lifestyle_modifications = []
    
    if urgency_level == "emergency":
        immediate_actions = [
            "Continuous cardiac monitoring",
            "IV access established",
            "Serial 12-lead ECGs",
            "Cardiac biomarkers (troponin, BNP)",
            "Emergency cardiology consultation"
        ]
    elif urgency_level == "urgent":
        immediate_actions = [
            "12-lead ECG within 30 minutes",
            "Basic metabolic panel and CBC",
            "Cardiology consultation same day",
            "Consider stress testing if stable"
        ]
    
    # Standard follow-up actions
    follow_up_actions = [
        "Follow-up appointment as scheduled",
        "Continue current cardiac medications",
        "Monitor symptoms and report changes",
        "Blood pressure monitoring"
    ]
    
    # Medication review based on risk factors
    if "hypertension" in risk_factors:
        medications_review.append("Review antihypertensive therapy")
    if "diabetes" in risk_factors:
        medications_review.append("Optimize diabetes management")
    
    # Lifestyle modifications
    lifestyle_modifications = [
        "Heart-healthy diet (Mediterranean or DASH)",
        "Regular exercise as tolerated",
        "Smoking cessation if applicable",
        "Weight management",
        "Stress reduction techniques"
    ]
    
    return {
        "immediate_actions": immediate_actions,
        "follow_up_actions": follow_up_actions,
        "medications_review": medications_review,
        "lifestyle_modifications": lifestyle_modifications,
        "monitoring_plan": ["Symptom diary", "Blood pressure log", "Weight monitoring"],
        "treatment_confidence": 0.85
    }


@tool
def discharge_summary_tool(session_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Generate discharge summary and follow-up instructions"""
    
    urgency_level = session_summary.get("urgency_level", "routine")
    patient_educated = session_summary.get("education_provided", False)
    
    # Generate discharge instructions
    if urgency_level == "emergency":
        discharge_status = "Emergency transport arranged"
        instructions = [
            "Patient transferred to emergency department",
            "Emergency contact information provided to EMS",
            "Family notified of transfer",
            "All documentation forwarded to receiving facility"
        ]
    else:
        discharge_status = "Discharged to home with instructions"
        instructions = [
            "Return to normal activities unless contraindicated",
            "Take medications as prescribed",
            "Follow-up appointments scheduled",
            "Emergency precautions reviewed"
        ]
    
    # Warning signs to report
    warning_signs = [
        "New or worsening chest pain",
        "Severe shortness of breath",
        "Loss of consciousness",
        "Rapid or irregular heartbeat",
        "Unusual swelling or weight gain"
    ]
    
    return {
        "discharge_status": discharge_status,
        "discharge_instructions": instructions,
        "warning_signs": warning_signs,
        "patient_educated": patient_educated,
        "follow_up_scheduled": urgency_level in ["urgent", "moderate"],
        "discharge_confidence": 0.9
    }


class ClinicalDocsAgent:
    """Real LangGraph Clinical Documentation Agent with StateGraph"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        self.name = "clinical_docs_agent"
        self.tools = [clinical_assessment_tool, treatment_plan_tool, discharge_summary_tool]
        
        # Build the LangGraph workflow
        self.graph = self._build_documentation_workflow()
    
    def _build_documentation_workflow(self) -> StateGraph:
        """Build the LangGraph StateGraph for clinical documentation"""
        
        # Create the StateGraph
        workflow = StateGraph(AgentState)
        
        # Add nodes for documentation workflow
        workflow.add_node("gather_session_data", self._gather_session_data_node)
        workflow.add_node("generate_assessment", self._generate_assessment_node)
        workflow.add_node("create_treatment_plan", self._create_treatment_plan_node)
        workflow.add_node("generate_discharge_summary", self._generate_discharge_summary_node)
        workflow.add_node("compile_final_report", self._compile_final_report_node)
        workflow.add_node("handle_error", self._handle_documentation_error_node)
        
        # Set entry point
        workflow.set_entry_point("gather_session_data")
        
        # Define conditional routing
        workflow.add_conditional_edges(
            "gather_session_data",
            self._route_after_data_gathering,
            {
                "generate_assessment": "generate_assessment",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "generate_assessment",
            self._route_after_assessment,
            {
                "create_treatment_plan": "create_treatment_plan",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "create_treatment_plan",
            self._route_after_treatment_plan,
            {
                "generate_discharge_summary": "generate_discharge_summary",
                "error": "handle_error"
            }
        )
        
        # Terminal routing
        workflow.add_edge("generate_discharge_summary", "compile_final_report")
        workflow.add_edge("compile_final_report", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _gather_session_data_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Gather and organize session data for documentation"""
        
        start_time = time.time()
        
        # Extract comprehensive session data
        session_data = {
            "patient_id": state.get("patient_id", "Unknown"),
            "session_timestamp": datetime.now().isoformat(),
            "urgency_level": state.get("urgency_level", "routine"),
            "triage_result": state.get("triage_result", {}),
            "clinical_notes": state.get("clinical_notes", []),
            "tools_used": state.get("tools_used", []),
            "agents_involved": self._extract_agents_involved(state),
            "processing_times": self._calculate_processing_times(state),
            "confidence_scores": state.get("confidence_scores", {})
        }
        
        # Extract symptoms and risk factors from triage result
        triage_result = session_data["triage_result"]
        if triage_result:
            session_data["symptoms"] = triage_result.get("identified_symptoms", [])
            session_data["risk_factors"] = triage_result.get("risk_factors", [])
            session_data["emergency_indicators"] = triage_result.get("emergency_indicators", [])
        else:
            session_data["symptoms"] = []
            session_data["risk_factors"] = []
            session_data["emergency_indicators"] = []
        
        processing_time = time.time() - start_time
        
        return {
            **state,
            "session_data": session_data,
            "current_agent": "clinical_docs_agent",
            "processing_time": processing_time,
            "next_action": "generate_assessment",
            "messages": state["messages"] + [AIMessage(
                content="Gathering session data for clinical documentation..."
            )]
        }
    
    def _generate_assessment_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Generate clinical assessment documentation"""
        
        session_data = state.get("session_data", {})
        patient_data = {
            "patient_id": session_data.get("patient_id"),
            "session_timestamp": session_data.get("session_timestamp")
        }
        
        try:
            # Use clinical assessment tool
            assessment_result = clinical_assessment_tool.invoke({
                "patient_data": patient_data,
                "session_data": session_data
            })
            
            # Generate LLM-enhanced assessment
            assessment_prompt = f"""
            Generate a comprehensive clinical assessment for this cardiac consultation:
            
            Patient: {patient_data.get('patient_id', 'Unknown')}
            Chief Complaint: {assessment_result['chief_complaint']}
            Urgency Level: {assessment_result['assessment_urgency']}
            Clinical Impression: {assessment_result['clinical_impression']}
            
            Session Details:
            - Symptoms: {', '.join(session_data.get('symptoms', []))}
            - Risk Factors: {', '.join(session_data.get('risk_factors', []))}
            - Emergency Indicators: {', '.join(session_data.get('emergency_indicators', []))}
            
            Provide a detailed clinical narrative in standard medical documentation format.
            """
            
            llm_assessment = self.llm.invoke([HumanMessage(content=assessment_prompt)])
            
            return {
                **state,
                "clinical_assessment": assessment_result,
                "assessment_narrative": llm_assessment.content,
                "tools_used": state.get("tools_used", []) + ["clinical_assessment_tool"],
                "next_action": "create_treatment_plan",
                "messages": state["messages"] + [AIMessage(
                    content=f"Clinical assessment generated: {assessment_result['clinical_impression']}"
                )]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Assessment generation failed: {str(e)}",
                "next_action": "error"
            }
    
    def _create_treatment_plan_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Create comprehensive treatment plan"""
        
        clinical_assessment = state.get("clinical_assessment", {})
        session_data = state.get("session_data", {})
        
        patient_profile = {
            "symptoms": session_data.get("symptoms", []),
            "risk_factors": session_data.get("risk_factors", []),
            "urgency_level": clinical_assessment.get("assessment_urgency", "routine")
        }
        
        try:
            # Use treatment plan tool
            treatment_result = treatment_plan_tool.invoke({
                "assessment_data": clinical_assessment,
                "patient_profile": patient_profile
            })
            
            # Format treatment plan
            treatment_plan_text = f"""
TREATMENT PLAN GENERATED

Immediate Actions:
{chr(10).join([f'• {action}' for action in treatment_result['immediate_actions']])}

Follow-up Actions:
{chr(10).join([f'• {action}' for action in treatment_result['follow_up_actions']])}

Monitoring Plan:
{chr(10).join([f'• {item}' for item in treatment_result['monitoring_plan']])}
            """
            
            return {
                **state,
                "treatment_plan": treatment_result,
                "treatment_plan_text": treatment_plan_text,
                "tools_used": state.get("tools_used", []) + ["treatment_plan_tool"],
                "next_action": "generate_discharge_summary",
                "messages": state["messages"] + [AIMessage(content=treatment_plan_text.strip())]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Treatment plan creation failed: {str(e)}",
                "next_action": "error"
            }
    
    def _generate_discharge_summary_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Generate discharge summary and instructions"""
        
        session_data = state.get("session_data", {})
        clinical_assessment = state.get("clinical_assessment", {})
        
        session_summary = {
            "urgency_level": session_data.get("urgency_level"),
            "education_provided": "virtual_assistant_agent" in session_data.get("agents_involved", []),
            "total_processing_time": sum(session_data.get("processing_times", {}).values())
        }
        
        try:
            # Use discharge summary tool
            discharge_result = discharge_summary_tool.invoke({
                "session_summary": session_summary
            })
            
            # Format discharge summary
            discharge_text = f"""
DISCHARGE SUMMARY

Status: {discharge_result['discharge_status']}
Patient Education: {'Provided' if discharge_result['patient_educated'] else 'Not provided'}

Instructions:
{chr(10).join([f'• {instruction}' for instruction in discharge_result['discharge_instructions']])}

WARNING SIGNS - Contact healthcare provider immediately:
{chr(10).join([f'• {sign}' for sign in discharge_result['warning_signs']])}
            """
            
            return {
                **state,
                "discharge_summary": discharge_result,
                "discharge_text": discharge_text,
                "tools_used": state.get("tools_used", []) + ["discharge_summary_tool"],
                "next_action": "compile_final_report",
                "messages": state["messages"] + [AIMessage(content=discharge_text.strip())]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Discharge summary generation failed: {str(e)}",
                "next_action": "error"
            }
    
    def _compile_final_report_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Compile comprehensive clinical documentation"""
        
        session_data = state.get("session_data", {})
        clinical_assessment = state.get("clinical_assessment", {})
        treatment_plan = state.get("treatment_plan", {})
        discharge_summary = state.get("discharge_summary", {})
        
        # Compile comprehensive clinical report
        final_report = f"""
CARDIOLOGY AI CONSULTATION REPORT

Date/Time: {session_data.get('session_timestamp', 'Not recorded')}
Patient ID: {session_data.get('patient_id', 'Unknown')}

CHIEF COMPLAINT:
{clinical_assessment.get('chief_complaint', 'Cardiac consultation')}

CLINICAL ASSESSMENT:
{state.get('assessment_narrative', 'Assessment not available')}

IMPRESSION:
{clinical_assessment.get('clinical_impression', 'Assessment pending')}

RISK STRATIFICATION:
{clinical_assessment.get('risk_stratification', 'Not assessed')}

DISPOSITION:
{clinical_assessment.get('disposition', 'Standard follow-up')}

TREATMENT PLAN:
{state.get('treatment_plan_text', 'Plan pending')}

DISCHARGE STATUS:
{discharge_summary.get('discharge_status', 'Status pending')}

SESSION METRICS:
- Total Processing Time: {sum(session_data.get('processing_times', {}).values()):.2f}s
- Agents Involved: {', '.join(session_data.get('agents_involved', []))}
- Tools Used: {', '.join(session_data.get('tools_used', []))}
- Confidence Scores: {session_data.get('confidence_scores', {})}

PROVIDER: Cardiology AI Multi-Agent System
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        return {
            **state,
            "final_clinical_report": final_report,
            "documentation_complete": True,
            "workflow_complete": True,
            "next_agent": "END",
            "clinical_notes": state.get("clinical_notes", []) + ["Clinical documentation completed"],
            "messages": state["messages"] + [AIMessage(content="Clinical documentation completed successfully.")]
        }
    
    def _handle_documentation_error_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Handle documentation errors"""
        
        error_message = state.get("error", "Unknown documentation error")
        
        error_report = f"""
CLINICAL DOCUMENTATION ERROR

Error: {error_message}

PARTIAL DOCUMENTATION AVAILABLE:
- Session Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Patient ID: {state.get('patient_id', 'Unknown')}
- Urgency Level: {state.get('urgency_level', 'Not assessed')}

Please review session manually and complete documentation as needed.
Contact system administrator regarding documentation system error.
        """
        
        return {
            **state,
            "error_handled": True,
            "documentation_complete": False,
            "workflow_complete": True,
            "next_agent": "END",
            "messages": state["messages"] + [AIMessage(content=error_report.strip())]
        }
    
    def _extract_agents_involved(self, state: AgentState) -> List[str]:
        """Extract list of agents that participated in this session"""
        agents = []
        if state.get("triage_result"):
            agents.append("triage_agent")
        if state.get("appointment_result"):
            agents.append("appointment_agent")
        if state.get("education_provided"):
            agents.append("virtual_assistant_agent")
        agents.append("clinical_docs_agent")
        return agents
    
    def _calculate_processing_times(self, state: AgentState) -> Dict[str, float]:
        """Calculate processing times for different components"""
        # This would ideally track actual processing times from each agent
        return {
            "total_session": state.get("processing_time", 0),
            "documentation": time.time()  # Current documentation time
        }
    
    def _route_after_data_gathering(self, state: AgentState) -> Literal["generate_assessment", "error"]:
        """Route after data gathering"""
        return "error" if state.get("error") else "generate_assessment"
    
    def _route_after_assessment(self, state: AgentState) -> Literal["create_treatment_plan", "error"]:
        """Route after assessment generation"""
        return "error" if state.get("error") else "create_treatment_plan"
    
    def _route_after_treatment_plan(self, state: AgentState) -> Literal["generate_discharge_summary", "error"]:
        """Route after treatment plan creation"""
        return "error" if state.get("error") else "generate_discharge_summary"
    
    async def process_documentation_workflow(self, state: AgentState) -> AgentState:
        """Execute the LangGraph clinical documentation workflow"""
        try:
            result = await self.graph.ainvoke(state)
            return result
        except Exception as e:
            return self._handle_documentation_error_node({
                **state,
                "error": f"Documentation workflow execution failed: {str(e)}"
            })
    
    def __call__(self, state: AgentState) -> AgentState:
        """Synchronous entry point for the LangGraph clinical documentation agent"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.process_documentation_workflow(state))
                return result
            finally:
                loop.close()
        except Exception as e:
            return self._handle_documentation_error_node({
                **state,
                "error": f"Clinical documentation execution failed: {str(e)}"
            })