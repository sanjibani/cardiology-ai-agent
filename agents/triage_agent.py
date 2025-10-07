from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from models.state import AgentState
from models.schemas import SymptomAssessment
import json
import time
from typing import Dict, Any, List


@tool
def emergency_escalation_tool(urgency_level: str, symptoms: List[str], 
                             patient_id: str = None) -> Dict[str, Any]:
    """Escalate critical symptoms to emergency services"""
    if urgency_level == "emergency":
        return {
            "escalation_triggered": True,
            "emergency_protocol": "911_notification_sent",
            "estimated_response_time": "8-12 minutes",
            "instructions": "Stay with patient, monitor vitals, prepare for transport"
        }
    elif urgency_level == "urgent":
        return {
            "escalation_triggered": True,
            "urgent_protocol": "same_day_cardiology_referral",
            "appointment_priority": "high",
            "instructions": "Contact cardiology within 2 hours"
        }
    return {"escalation_triggered": False}


@tool  
def patient_risk_assessment_tool(patient_id: str, symptoms: List[str]) -> Dict[str, Any]:
    """Assess patient risk factors based on history and current symptoms"""
    # In real implementation, this would query patient database
    return {
        "risk_factors": ["hypertension", "diabetes", "family_history"],
        "previous_cardiac_events": [],
        "current_medications": ["lisinopril", "metformin"],
        "risk_score": 6.5,
        "risk_category": "moderate"
    }


class TriageAgent:
    """Enhanced LangGraph Triage Agent with reactive assessment capabilities"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        self.name = "triage_agent"
        self.tools = [emergency_escalation_tool, patient_risk_assessment_tool]
        
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert cardiac triage specialist with access to emergency escalation and risk assessment tools.
            
            Your expertise includes:
            - Emergency cardiac symptom recognition and risk stratification
            - Evidence-based clinical decision making
            - Integration with emergency services and urgent care protocols
            - Comprehensive patient history analysis
            
            CRITICAL EMERGENCY SYMPTOMS (Immediate 911 activation):
            - Chest pain with crushing, pressure, or squeezing sensation
            - Chest pain radiating to arm, jaw, neck, or back
            - Severe shortness of breath at rest or with minimal exertion
            - Loss of consciousness, syncope, or near-syncope
            - Sudden onset severe palpitations with associated chest discomfort
            - Signs of acute heart failure (severe SOB + swelling)
            
            URGENT SYMPTOMS (Same-day cardiology evaluation):
            - New or worsening dyspnea on exertion
            - Palpitations lasting >30 minutes or recurrent episodes
            - Bilateral lower extremity edema with breathing difficulty
            - New onset fatigue with cardiac risk factors
            - Medication-related cardiac symptoms
            
            ROUTINE SYMPTOMS (Schedule within 1-2 weeks):
            - Mild intermittent palpitations without other symptoms
            - Medication adherence questions
            - Follow-up for stable conditions
            - Preventive care discussions
            
            ASSESSMENT PROTOCOL:
            1. Analyze symptoms for emergency indicators
            2. Use patient_risk_assessment_tool for relevant patient history
            3. Calculate severity score (1-10 scale)
            4. Determine urgency level and required actions
            5. Use emergency_escalation_tool if criteria met
            6. Provide structured clinical assessment with clear recommendations
            
            Always prioritize patient safety and follow evidence-based protocols."""),
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