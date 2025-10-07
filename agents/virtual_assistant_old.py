from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from models.state import AgentState
import time
from typing import Dict, Any


class VirtualAssistantAgent:
    """LangGraph Virtual Assistant Agent for patient education and support"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        self.name = "virtual_assistant_agent"
    
    def __call__(self, state: AgentState) -> AgentState:
        """Provide patient education and general assistance"""
        start_time = time.time()
        
        try:
            # Generate educational response based on context
            response_message = self._generate_educational_response(state)
            
            # Update state
            processing_time = time.time() - start_time
            
            return {
                **state,
                "current_agent": "virtual_assistant_agent",
                "virtual_assistant_context": {
                    "education_provided": True,
                    "topics_covered": ["general_cardiology", "lifestyle"]
                },
                "tools_used": state.get("tools_used", []) + ["knowledge_base"],
                "processing_time": processing_time,
                "workflow_complete": True,
                "messages": state["messages"] + [AIMessage(content=response_message)]
            }
            
        except Exception as e:
            return self._create_error_response(state, f"Assistant error: {str(e)}")
    
    def _generate_educational_response(self, state: AgentState) -> str:
        """Generate educational content based on session context"""
        
        urgency = state.get("urgency_level", "routine")
        triage_result = state.get("triage_result", {})
        
        if urgency == "routine":
            return """
💡 CARDIOLOGY HEALTH EDUCATION

Thank you for using our Cardiology AI system. Here are some general heart health tips:

🫀 HEART HEALTH BASICS:
• Maintain a balanced diet low in saturated fats
• Exercise regularly (aim for 150 min/week moderate activity)  
• Monitor blood pressure and cholesterol levels
• Avoid smoking and limit alcohol consumption
• Manage stress through relaxation techniques

📋 MEDICATION ADHERENCE:
• Take medications as prescribed
• Don't stop cardiac medications without consulting your doctor
• Keep a medication list updated
• Set reminders for consistent timing

⚠️ WHEN TO SEEK HELP:
• New or worsening chest pain
• Severe shortness of breath
• Dizziness or fainting
• Rapid or irregular heartbeat

Remember: This AI system provides educational information only. 
Always consult your healthcare provider for medical decisions.
"""
        else:
            return """
Thank you for using our Cardiology AI system. Please follow the medical 
recommendations provided and contact your healthcare provider as advised.

If you have any additional questions about your heart health, 
feel free to ask our virtual assistant anytime.
"""
    
    def _create_error_response(self, state: AgentState, error_message: str) -> AgentState:
        """Create error response state"""
        return {
            **state,
            "current_agent": "virtual_assistant_agent",
            "workflow_complete": True,
            "requires_human_review": True,
            "messages": state.get("messages", []) + [AIMessage(
                content=f"Assistant Error: {error_message}. Please contact support."
            )]
        }