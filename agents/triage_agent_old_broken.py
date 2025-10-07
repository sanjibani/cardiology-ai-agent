from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from models.state import AgentState
from typing import Dict, Any, List, Literal
import time
import asyncio


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
    # In real implementation, this would use medical NLP and symptom databases
    cardiac_keywords = ["chest pain", "shortness of breath", "palpitations", "dizziness"]
    emergency_keywords = ["crushing", "radiating", "severe", "sudden onset"]
    
    symptoms_lower = symptoms_description.lower()
    
    cardiac_indicators = [kw for kw in cardiac_keywords if kw in symptoms_lower]
    emergency_indicators = [kw for kw in emergency_keywords if kw in symptoms_lower]
    
    if emergency_indicators:
        severity = "emergency"
        score = 9
    elif len(cardiac_indicators) >= 2:
        severity = "urgent" 
        score = 7
    elif cardiac_indicators:
        severity = "moderate"
        score = 5
    else:
        severity = "routine"
        score = 3
    
    return {
        "identified_symptoms": cardiac_indicators,
        "emergency_indicators": emergency_indicators,
        "severity_level": severity,
        "severity_score": score,
        "clinical_patterns": "cardiac_assessment_required" if cardiac_indicators else "general_consultation"
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
                    content=f"🔍 Analyzing symptoms... Severity level: {symptom_analysis['severity_level']} (Score: {symptom_analysis['severity_score']}/10)"
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
                    content=f"📊 Risk assessment complete. Risk factors: {', '.join(risk_assessment['risk_factors'])}. Combined risk score: {combined_risk_score:.1f}/10"
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
                content=f"⚕️ Triage complete: {urgency_level.upper()} priority (Score: {combined_risk_score:.1f}/10)"
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
🚨 EMERGENCY PROTOCOL ACTIVATED

Priority: {escalation_result.get('priority', 'IMMEDIATE')}
Protocol: {escalation_result.get('emergency_protocol', 'Emergency response')}
Response Time: {escalation_result.get('estimated_response_time', 'ASAP')}

⚠️ IMMEDIATE ACTIONS:
{escalation_result.get('instructions', 'Follow emergency protocols')}

📞 EMERGENCY CONTACT: {escalation_result.get('emergency_contact', '911')}

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
🏥 URGENT CARDIOLOGY ASSESSMENT REQUIRED

Urgency Level: {urgency_level.upper()}
Risk Score: {triage_result.get('severity_score', 'N/A')}/10

⚠️ IMMEDIATE ACTIONS:
• Contact your cardiologist within 2 hours
• If unavailable, go to emergency department
• Do not drive yourself - arrange transportation
• Bring list of current medications

SYMPTOMS IDENTIFIED:
{', '.join(triage_result.get('identified_symptoms', []))}

RISK FACTORS:
{', '.join(triage_result.get('risk_factors', []))}

📞 If symptoms worsen, call 911 immediately.
            """
        elif urgency_level == "moderate":
            recommendations = f"""
📋 CARDIOLOGY CONSULTATION RECOMMENDED

Urgency Level: {urgency_level.upper()}
Risk Score: {triage_result.get('severity_score', 'N/A')}/10

📅 RECOMMENDED ACTIONS:
• Schedule cardiology appointment within 1-2 weeks
• Monitor symptoms and note any changes
• Continue current medications as prescribed
• Avoid strenuous activity until evaluated

SYMPTOMS TO MONITOR:
{', '.join(triage_result.get('identified_symptoms', []))}

📞 Contact your doctor if symptoms worsen or new symptoms develop.
            """
        else:
            recommendations = f"""
✅ ROUTINE MONITORING RECOMMENDED

Urgency Level: {urgency_level.upper()}
Risk Score: {triage_result.get('severity_score', 'N/A')}/10

📋 GENERAL RECOMMENDATIONS:
• Schedule routine cardiology follow-up as needed
• Continue heart-healthy lifestyle practices
• Monitor blood pressure and take medications as prescribed
• Regular exercise and balanced diet

💡 HEART HEALTH TIPS:
• Aim for 150 minutes moderate exercise weekly
• Limit sodium intake
• Maintain healthy weight
• Don't smoke

📞 Contact your doctor for routine care or if concerns develop.
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
❌ TRIAGE ASSESSMENT ERROR

{error_message}

🚨 IMPORTANT: If you are experiencing a medical emergency, call 911 immediately.

🏥 For urgent cardiac symptoms, contact:
• Emergency Department: 911
• Cardiology Department: (555) 123-4567
• Your primary care physician

⚠️ DO NOT DELAY SEEKING MEDICAL CARE if you have:
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
            """),
            MessagesPlaceholder(variable_name="messages"),
            HumanMessage(content="Perform comprehensive triage assessment with tool integration.")
        ])
    
    def __call__(self, state: AgentState) -> AgentState:
        """Perform comprehensive triage assessment with tool integration"""
        start_time = time.time()
        
        # Get the current query and context
        if not state.get("messages"):
            return self._create_error_response(state, "No symptoms to assess")
        
        # Extract symptoms and context
        last_message = state["messages"][-1]
        symptoms_query = last_message.content if hasattr(last_message, 'content') else str(last_message)
        patient_id = state.get("patient_id")
        
        try:
            # Step 1: Analyze symptoms with LLM
            symptom_analysis = self._analyze_symptoms(symptoms_query, state)
            
            # Step 2: Assess patient risk factors if patient ID available
            risk_assessment = {}
            if patient_id:
                risk_assessment = patient_risk_assessment_tool.invoke({
                    "patient_id": patient_id,
                    "symptoms": symptom_analysis["symptoms"]
                })
            
            # Step 3: Determine urgency and severity
            urgency_assessment = self._determine_urgency(symptom_analysis, risk_assessment)
            
            # Step 4: Escalate if needed
            escalation_result = {}
            if urgency_assessment["urgency_level"] in ["emergency", "urgent"]:
                escalation_result = emergency_escalation_tool.invoke({
                    "urgency_level": urgency_assessment["urgency_level"],
                    "symptoms": symptom_analysis["symptoms"],
                    "patient_id": patient_id
                })
            
            # Step 5: Generate comprehensive assessment
            triage_result = {
                "symptoms": symptom_analysis["symptoms"],
                "severity_score": urgency_assessment["severity_score"],
                "urgency_level": urgency_assessment["urgency_level"],
                "recommended_action": urgency_assessment["recommended_action"],
                "escalation_required": escalation_result.get("escalation_triggered", False),
                "reasoning": urgency_assessment["clinical_reasoning"],
                "risk_factors": risk_assessment.get("risk_factors", []),
                "emergency_protocol": escalation_result.get("emergency_protocol"),
                "tools_used": ["symptom_analysis", "risk_assessment"] + 
                             (["emergency_escalation"] if escalation_result else [])
            }
            
            # Create response message
            response_message = self._format_triage_response(triage_result)
            
            # Update state
            processing_time = time.time() - start_time
            
            updated_state = {
                **state,
                "current_agent": "triage_agent",
                "triage_result": triage_result,
                "urgency_level": triage_result["urgency_level"],
                "escalation_needed": triage_result["escalation_required"],
                "clinical_notes": state.get("clinical_notes", []) + [triage_result["reasoning"]],
                "tools_used": state.get("tools_used", []) + triage_result["tools_used"],
                "processing_time": processing_time,
                "confidence_scores": {
                    **state.get("confidence_scores", {}),
                    "triage_confidence": urgency_assessment.get("confidence", 0.9)
                },
                "messages": state["messages"] + [AIMessage(content=response_message)],
                "requires_human_review": triage_result["urgency_level"] == "emergency",
                "next_agent": self._determine_next_agent(triage_result)
            }
            
            return updated_state
            
        except Exception as e:
            return self._create_error_response(state, f"Triage assessment error: {str(e)}")
    
    def _analyze_symptoms(self, symptoms_query: str, state: AgentState) -> Dict[str, Any]:
        """Use LLM to analyze and extract symptoms"""
        
        analysis_prompt = f"""
        Analyze the following patient query and extract key information:
        
        Patient Query: {symptoms_query}
        
        Extract and structure the following:
        1. List of specific symptoms mentioned
        2. Symptom characteristics (severity, duration, triggers)
        3. Associated symptoms
        4. Temporal patterns
        5. Any red flag indicators
        
        Provide response in JSON format:
        {{
            "symptoms": ["list of symptoms"],
            "characteristics": {{"severity": "", "duration": "", "triggers": ""}},
            "red_flags": ["emergency indicators"],
            "temporal_pattern": "acute/chronic/intermittent"
        }}
        """
        
        try:
            response = self.llm.invoke([HumanMessage(content=analysis_prompt)])
            # Parse JSON response (simplified for demo)
            return {
                "symptoms": ["chest pain", "shortness of breath"],  # Would extract from LLM
                "characteristics": {"severity": "moderate", "duration": "30 minutes"},
                "red_flags": [],
                "temporal_pattern": "acute"
            }
        except Exception:
            return {"symptoms": [symptoms_query], "characteristics": {}, "red_flags": []}
    
    def _determine_urgency(self, symptom_analysis: Dict[str, Any], 
                          risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Determine urgency level based on symptoms and risk factors"""
        
        symptoms = symptom_analysis.get("symptoms", [])
        red_flags = symptom_analysis.get("red_flags", [])
        risk_score = risk_assessment.get("risk_score", 0)
        
        # Emergency criteria
        emergency_indicators = [
            "crushing chest pain", "radiating pain", "severe shortness of breath",
            "loss of consciousness", "syncope"
        ]
        
        if any(indicator in " ".join(symptoms).lower() for indicator in emergency_indicators) or red_flags:
            return {
                "urgency_level": "emergency",
                "severity_score": 9,
                "recommended_action": "Call 911 immediately - potential acute cardiac event",
                "clinical_reasoning": "Emergency cardiac symptoms detected requiring immediate evaluation",
                "confidence": 0.95
            }
        
        # Urgent criteria
        urgent_indicators = ["palpitations", "new dyspnea", "leg swelling"]
        if any(indicator in " ".join(symptoms).lower() for indicator in urgent_indicators) or risk_score > 7:
            return {
                "urgency_level": "urgent",
                "severity_score": 6,
                "recommended_action": "Same-day cardiology evaluation recommended",
                "clinical_reasoning": "Urgent cardiac symptoms requiring prompt medical attention",
                "confidence": 0.85
            }
        
        # Routine
        return {
            "urgency_level": "routine",
            "severity_score": 3,
            "recommended_action": "Schedule cardiology appointment within 1-2 weeks",
            "clinical_reasoning": "Routine cardiac concerns, stable for outpatient management",
            "confidence": 0.8
        }
    
    def _format_triage_response(self, triage_result: Dict[str, Any]) -> str:
        """Format comprehensive triage response"""
        
        urgency = triage_result["urgency_level"].upper()
        severity = triage_result["severity_score"]
        
        response = f"""
🏥 CARDIOLOGY TRIAGE ASSESSMENT

URGENCY LEVEL: {urgency} (Severity: {severity}/10)

SYMPTOMS ASSESSED: {', '.join(triage_result['symptoms'])}

RECOMMENDED ACTION: {triage_result['recommended_action']}

CLINICAL REASONING: {triage_result['reasoning']}
"""
        
        if triage_result.get("escalation_required"):
            response += f"\n⚠️ ESCALATION ACTIVATED: {triage_result.get('emergency_protocol', 'Emergency protocols initiated')}"
        
        if triage_result.get("risk_factors"):
            response += f"\nRISK FACTORS: {', '.join(triage_result['risk_factors'])}"
        
        return response.strip()
    
    def _determine_next_agent(self, triage_result: Dict[str, Any]) -> str:
        """Determine next agent based on triage results"""
        
        if triage_result["urgency_level"] == "emergency":
            return "END"  # Emergency cases end workflow, human intervention required
        elif triage_result["urgency_level"] == "urgent":
            return "appointment_agent"  # Schedule urgent appointment
        else:
            return "virtual_assistant_agent"  # Provide education and guidance
    
    def _create_error_response(self, state: AgentState, error_message: str) -> AgentState:
        """Create error response state"""
        return {
            **state,
            "current_agent": "triage_agent",
            "next_agent": "virtual_assistant_agent",  # Fallback to general assistance
            "requires_human_review": True,
            "messages": state.get("messages", []) + [AIMessage(
                content=f"Triage Assessment Error: {error_message}. Redirecting to general assistance."
            )],
            "session_context": {
                **state.get("session_context", {}),
                "triage_error": error_message
            }
        }
        """Evaluate symptoms and return structured assessment"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Patient Query: {patient_query}
            Patient History: {json.dumps(patient_data)}
            
            Provide triage assessment in this exact JSON format:
            {{
                "symptoms": ["list", "of", "symptoms"],
                "severity_score": 1-10,
                "urgency_level": "emergency|urgent|routine|informational",
                "recommended_action": "specific action to take",
                "escalation_required": true/false,
                "reasoning": "clinical reasoning"
            }}
            """)
        ]
        
        response = self.llm.invoke(messages)
        # Parse response and validate with Pydantic
        try:
            assessment_data = json.loads(response.content)
            return SymptomAssessment(**assessment_data)
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback assessment if parsing fails
            return SymptomAssessment(
                symptoms=["unknown"],
                severity_score=5,
                urgency_level="routine",
                recommended_action="Please contact your healthcare provider",
                escalation_required=True,
                reasoning=f"Unable to parse assessment: {str(e)}"
            )