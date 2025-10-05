from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.schemas import SymptomAssessment
import json

class TriageAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.system_prompt = """You are a cardiac triage specialist. Assess patient symptoms and determine urgency.
        
        CRITICAL SYMPTOMS requiring emergency (call 911):
        - Chest pain with crushing/pressure sensation
        - Chest pain radiating to arm, jaw, or back
        - Severe shortness of breath at rest
        - Loss of consciousness or near-syncope
        - Sudden onset severe palpitations with chest pain
        
        URGENT (same-day cardiology visit):
        - New or worsening shortness of breath
        - Palpitations lasting >30 minutes
        - Leg swelling with breathing difficulty
        
        ROUTINE (schedule within 1-2 weeks):
        - Mild intermittent palpitations
        - Medication questions
        - Follow-up appointments
        
        Return structured JSON with severity score (1-10) and recommended action."""
    
    def assess(self, patient_query: str, patient_data: dict) -> SymptomAssessment:
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