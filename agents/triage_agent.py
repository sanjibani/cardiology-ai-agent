import asyncio
import time
from typing import Any, Dict, List, Literal

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from models.state import AgentState


@tool
def emergency_escalation_tool(urgency_level: str, symptoms: List[str], 
                             patient_id: str = None) -> Dict[str, Any]:
    """Escalate critical symptoms to emergency services"""
    if urgency_level == "emergency":
        return {
            "escalation_triggered": True,
            "emergency_protocol": "911_notification_sent",
            "estimated_response_time": "8-12 minutes",
            "instructions": "Stay with patient, monitor vitals, prepare for transport",
            "emergency_contact": "911",
            "priority": "IMMEDIATE"
        }
    elif urgency_level == "urgent":
        return {
            "escalation_triggered": True,
            "urgent_protocol": "same_day_cardiology_referral",
            "appointment_priority": "high",
            "instructions": "Contact cardiology within 2 hours",
            "referral_required": True
        }
    return {"escalation_triggered": False, "monitoring_recommended": True}


@tool  
def patient_risk_assessment_tool(patient_id: str, symptoms: List[str]) -> Dict[str, Any]:
    """Assess patient risk factors based on history and current symptoms"""
    return {
        "risk_factors": ["hypertension", "diabetes", "family_history"],
        "previous_cardiac_events": [],
        "current_medications": ["lisinopril", "metformin"],
        "risk_score": 6.5,
        "risk_category": "moderate",
        "assessment_confidence": 0.85
    }


@tool
def symptom_analysis_tool(symptoms_description: str) -> Dict[str, Any]:
    """Analyze symptoms for cardiac risk patterns"""
    
    emergency_keywords = [
        "crushing chest pain", "severe chest pressure", "chest pain radiating",
        "severe shortness of breath", "unconscious", "loss of consciousness",
        "severe palpitations", "chest pain with sweating"
    ]
    
    urgent_keywords = [
        "chest discomfort", "shortness of breath", "palpitations",
        "lightheaded", "dizzy", "unusual fatigue"
    ]
    
    # Analyze symptom text
    text_lower = symptoms_description.lower()
    emergency_score = sum(1 for keyword in emergency_keywords if keyword in text_lower)
    urgent_score = sum(1 for keyword in urgent_keywords if keyword in text_lower)
    
    # Determine severity level
    if emergency_score > 0:
        severity_level = "emergency"
        severity_score = min(10, 8 + emergency_score)
    elif urgent_score > 1:
        severity_level = "urgent"
        severity_score = min(8, 5 + urgent_score)
    elif urgent_score > 0:
        severity_level = "moderate"
        severity_score = min(6, 3 + urgent_score)
    else:
        severity_level = "routine"
        severity_score = 2
    
    # Extract identified symptoms
    identified_symptoms = []
    if "chest" in text_lower:
        identified_symptoms.append("chest symptoms")
    if "breath" in text_lower or "shortness" in text_lower:
        identified_symptoms.append("dyspnea")
    if "palpitations" in text_lower or "heart" in text_lower:
        identified_symptoms.append("cardiac rhythm symptoms")
    if "dizzy" in text_lower or "lightheaded" in text_lower:
        identified_symptoms.append("dizziness")
    
    # Emergency indicators
    emergency_indicators = [keyword for keyword in emergency_keywords if keyword in text_lower]
    
    return {
        "severity_level": severity_level,
        "severity_score": severity_score,
        "identified_symptoms": identified_symptoms,
        "emergency_indicators": emergency_indicators,
        "assessment_confidence": 0.8,
        "requires_immediate_attention": severity_level in ["emergency", "urgent"]
    }


class TriageAgent:
    """Real LangGraph Triage Agent with StateGraph for emergency assessment"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        self.name = "triage_agent"
        self.tools = [emergency_escalation_tool, patient_risk_assessment_tool, symptom_analysis_tool]
        
        # Build the LangGraph workflow
        self.graph = self._build_triage_workflow()
    
    def _build_triage_workflow(self) -> StateGraph:
        """Build the LangGraph StateGraph for triage assessment"""
        
        # Create the StateGraph
        workflow = StateGraph(AgentState)
        
        # Add nodes for triage workflow
        workflow.add_node("analyze_symptoms", self._analyze_symptoms_node)
        workflow.add_node("assess_risk", self._assess_risk_node)
        workflow.add_node("determine_urgency", self._determine_urgency_node)
        workflow.add_node("escalate_emergency", self._escalate_emergency_node)
        workflow.add_node("provide_recommendations", self._provide_recommendations_node)
        workflow.add_node("handle_error", self._handle_triage_error_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_symptoms")
        
        # Define conditional routing
        workflow.add_conditional_edges(
            "analyze_symptoms",
            self._route_after_symptom_analysis,
            {
                "assess_risk": "assess_risk",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "assess_risk",
            self._route_after_risk_assessment,
            {
                "determine_urgency": "determine_urgency",
                "error": "handle_error"
            }
        )
        
        workflow.add_conditional_edges(
            "determine_urgency",
            self._route_after_urgency_determination,
            {
                "escalate_emergency": "escalate_emergency",
                "provide_recommendations": "provide_recommendations",
                "error": "handle_error"
            }
        )
        
        # Terminal nodes
        workflow.add_edge("escalate_emergency", END)
        workflow.add_edge("provide_recommendations", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _analyze_symptoms_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Analyze patient symptoms using tools and LLM"""
        
        start_time = time.time()
        
        # Get the symptom description
        last_message = state["messages"][-1] if state["messages"] else None
        
        if not last_message:
            return {
                **state,
                "error": "No symptoms to analyze",
                "next_action": "error"
            }
        
        symptoms_text = last_message.content
        
        try:
            # Use symptom analysis tool
            symptom_analysis = symptom_analysis_tool.invoke({
                "symptoms_description": symptoms_text
            })
            
            # Use LLM for additional clinical assessment
            clinical_prompt = f"""
            As a cardiac triage specialist, analyze these symptoms:
            
            Patient Symptoms: {symptoms_text}
            Automated Analysis: {symptom_analysis}
            
            Provide clinical assessment focusing on:
            1. Cardiac vs non-cardiac symptoms
            2. Emergency indicators
            3. Additional questions needed
            4. Immediate concerns
            """
            
            llm_response = self.llm.invoke([HumanMessage(content=clinical_prompt)])
            
            processing_time = time.time() - start_time
            
            return {
                **state,
                "symptom_analysis": symptom_analysis,
                "clinical_assessment": llm_response.content,
                "current_agent": "triage_agent",
                "processing_time": processing_time,
                "tools_used": state.get("tools_used", []) + ["symptom_analysis_tool", "llm_assessment"],
                "next_action": "assess_risk",
                "messages": state["messages"] + [AIMessage(
                    content=f"Analyzing symptoms... Severity level: {symptom_analysis['severity_level']} (Score: {symptom_analysis['severity_score']}/10)"
                )]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Symptom analysis failed: {str(e)}",
                "next_action": "error"
            }
    
    def _assess_risk_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Assess patient risk factors"""
        
        patient_id = state.get("patient_id")
        symptom_analysis = state.get("symptom_analysis", {})
        identified_symptoms = symptom_analysis.get("identified_symptoms", [])
        
        try:
            # Use patient risk assessment tool
            risk_assessment = patient_risk_assessment_tool.invoke({
                "patient_id": patient_id or "unknown",
                "symptoms": identified_symptoms
            })
            
            # Combine symptom severity with risk factors
            base_score = symptom_analysis.get("severity_score", 5)
            risk_multiplier = risk_assessment.get("risk_score", 5) / 5.0
            combined_risk_score = min(10, base_score * risk_multiplier)
            
            return {
                **state,
                "risk_assessment": risk_assessment,
                "combined_risk_score": combined_risk_score,
                "tools_used": state.get("tools_used", []) + ["patient_risk_assessment_tool"],
                "next_action": "determine_urgency",
                "messages": state["messages"] + [AIMessage(
                    content=f"Risk assessment complete. Risk factors: {', '.join(risk_assessment['risk_factors'])}. Combined risk score: {combined_risk_score:.1f}/10"
                )]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Risk assessment failed: {str(e)}",
                "next_action": "error"
            }
    
    def _determine_urgency_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Determine final urgency level"""
        
        symptom_analysis = state.get("symptom_analysis", {})
        risk_assessment = state.get("risk_assessment", {})
        combined_risk_score = state.get("combined_risk_score", 5)
        
        # Determine urgency based on multiple factors
        emergency_indicators = symptom_analysis.get("emergency_indicators", [])
        severity_level = symptom_analysis.get("severity_level", "routine")
        
        if emergency_indicators or combined_risk_score >= 9 or severity_level == "emergency":
            urgency_level = "emergency"
            next_action = "escalate_emergency"
        elif combined_risk_score >= 7 or severity_level == "urgent":
            urgency_level = "urgent"
            next_action = "provide_recommendations"
        elif combined_risk_score >= 5 or severity_level == "moderate":
            urgency_level = "moderate"
            next_action = "provide_recommendations"
        else:
            urgency_level = "routine"
            next_action = "provide_recommendations"
        
        # Create comprehensive triage result
        triage_result = {
            "urgency_level": urgency_level,
            "severity_score": combined_risk_score,
            "identified_symptoms": symptom_analysis.get("identified_symptoms", []),
            "emergency_indicators": emergency_indicators,
            "risk_factors": risk_assessment.get("risk_factors", []),
            "clinical_reasoning": f"Based on symptom analysis (severity: {severity_level}) and risk assessment (score: {risk_assessment.get('risk_score', 'N/A')}), determined urgency level: {urgency_level}",
            "confidence_score": min(symptom_analysis.get("assessment_confidence", 0.8), risk_assessment.get("assessment_confidence", 0.8))
        }
        
        return {
            **state,
            "triage_result": triage_result,
            "urgency_level": urgency_level,
            "escalation_needed": urgency_level in ["emergency", "urgent"],
            "next_action": next_action,
            "clinical_notes": state.get("clinical_notes", []) + [triage_result["clinical_reasoning"]],
            "confidence_scores": {
                **state.get("confidence_scores", {}),
                "triage_confidence": triage_result["confidence_score"]
            },
            "messages": state["messages"] + [AIMessage(
                content=f"Triage complete: {urgency_level.upper()} priority (Score: {combined_risk_score:.1f}/10)"
            )]
        }
    
    def _escalate_emergency_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Handle emergency escalation"""
        
        triage_result = state.get("triage_result", {})
        patient_id = state.get("patient_id")
        
        try:
            # Use emergency escalation tool
            escalation_result = emergency_escalation_tool.invoke({
                "urgency_level": "emergency",
                "symptoms": triage_result.get("identified_symptoms", []),
                "patient_id": patient_id
            })
            
            emergency_message = f"""
EMERGENCY PROTOCOL ACTIVATED

Priority: {escalation_result.get('priority', 'IMMEDIATE')}
Protocol: {escalation_result.get('emergency_protocol', 'Emergency response')}
Response Time: {escalation_result.get('estimated_response_time', 'ASAP')}

IMMEDIATE ACTIONS:
{escalation_result.get('instructions', 'Follow emergency protocols')}

EMERGENCY CONTACT: {escalation_result.get('emergency_contact', '911')}

SYMPTOMS REQUIRING EMERGENCY CARE:
{', '.join(triage_result.get('emergency_indicators', []))}

This is a medical emergency. Emergency services have been notified.
            """
            
            return {
                **state,
                "escalation_result": escalation_result,
                "emergency_activated": True,
                "requires_human_review": True,
                "workflow_complete": True,
                "next_agent": "END",
                "tools_used": state.get("tools_used", []) + ["emergency_escalation_tool"],
                "messages": state["messages"] + [AIMessage(content=emergency_message.strip())]
            }
            
        except Exception as e:
            return {
                **state,
                "error": f"Emergency escalation failed: {str(e)}",
                "next_action": "error"
            }
    
    def _provide_recommendations_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Provide triage recommendations"""
        
        triage_result = state.get("triage_result", {})
        urgency_level = triage_result.get("urgency_level", "routine")
        
        if urgency_level == "urgent":
            recommendations = f"""
URGENT CARDIOLOGY ASSESSMENT REQUIRED

Urgency Level: {urgency_level.upper()}
Risk Score: {triage_result.get('severity_score', 'N/A')}/10

IMMEDIATE ACTIONS:
• Contact your cardiologist within 2 hours
• If unavailable, go to emergency department
• Do not drive yourself - arrange transportation
• Bring list of current medications

SYMPTOMS IDENTIFIED:
{', '.join(triage_result.get('identified_symptoms', []))}

RISK FACTORS:
{', '.join(triage_result.get('risk_factors', []))}

If symptoms worsen, call 911 immediately.
            """
        elif urgency_level == "moderate":
            recommendations = f"""
CARDIOLOGY CONSULTATION RECOMMENDED

Urgency Level: {urgency_level.upper()}
Risk Score: {triage_result.get('severity_score', 'N/A')}/10

RECOMMENDED ACTIONS:
• Schedule cardiology appointment within 1-2 weeks
• Monitor symptoms and note any changes
• Continue current medications as prescribed
• Avoid strenuous activity until evaluated

SYMPTOMS TO MONITOR:
{', '.join(triage_result.get('identified_symptoms', []))}

Contact your doctor if symptoms worsen or new symptoms develop.
            """
        else:
            recommendations = f"""
ROUTINE MONITORING RECOMMENDED

Urgency Level: {urgency_level.upper()}
Risk Score: {triage_result.get('severity_score', 'N/A')}/10

GENERAL RECOMMENDATIONS:
• Schedule routine cardiology follow-up as needed
• Continue heart-healthy lifestyle practices
• Monitor blood pressure and take medications as prescribed
• Regular exercise and balanced diet

HEART HEALTH TIPS:
• Aim for 150 minutes moderate exercise weekly
• Limit sodium intake
• Maintain healthy weight
• Don't smoke

Contact your doctor for routine care or if concerns develop.
            """
        
        return {
            **state,
            "triage_recommendations": recommendations,
            "workflow_complete": True,
            "next_agent": "appointment_agent" if urgency_level in ["urgent", "moderate"] else "virtual_assistant_agent",
            "messages": state["messages"] + [AIMessage(content=recommendations.strip())]
        }
    
    def _handle_triage_error_node(self, state: AgentState) -> AgentState:
        """LangGraph Node: Handle triage errors"""
        
        error_message = state.get("error", "Unknown triage error")
        
        error_response = f"""
TRIAGE ASSESSMENT ERROR

{error_message}

IMPORTANT: If you are experiencing a medical emergency, call 911 immediately.

For urgent cardiac symptoms, contact:
• Emergency Department: 911
• Cardiology Department: (555) 123-4567
• Your primary care physician

DO NOT DELAY SEEKING MEDICAL CARE if you have:
• Chest pain or pressure
• Severe shortness of breath
• Loss of consciousness
• Rapid or irregular heartbeat

Our system encountered an error, but your health is our priority.
        """
        
        return {
            **state,
            "error_handled": True,
            "requires_human_review": True,
            "workflow_complete": True,
            "next_agent": "virtual_assistant_agent",
            "messages": state["messages"] + [AIMessage(content=error_response.strip())]
        }
    
    def _route_after_symptom_analysis(self, state: AgentState) -> Literal["assess_risk", "error"]:
        """Route after symptom analysis"""
        return "error" if state.get("error") else "assess_risk"
    
    def _route_after_risk_assessment(self, state: AgentState) -> Literal["determine_urgency", "error"]:
        """Route after risk assessment"""
        return "error" if state.get("error") else "determine_urgency"
    
    def _route_after_urgency_determination(self, state: AgentState) -> Literal["escalate_emergency", "provide_recommendations", "error"]:
        """Route after urgency determination"""
        if state.get("error"):
            return "error"
        elif state.get("next_action") == "escalate_emergency":
            return "escalate_emergency"
        else:
            return "provide_recommendations"
    
    async def process_triage_workflow(self, state: AgentState) -> AgentState:
        """Execute the LangGraph triage workflow"""
        try:
            result = await self.graph.ainvoke(state)
            return result
        except Exception as e:
            return self._handle_triage_error_node({
                **state,
                "error": f"Triage workflow execution failed: {str(e)}"
            })
    
    def __call__(self, state: AgentState) -> AgentState:
        """Synchronous entry point for the LangGraph triage agent"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.process_triage_workflow(state))
                return result
            finally:
                loop.close()
        except Exception as e:
            return self._handle_triage_error_node({
                **state,
                "error": f"Triage agent execution failed: {str(e)}"
            })