from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Literal

class SupervisorAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.system_prompt = """You are a routing supervisor for a cardiology AI system.
        Analyze patient queries and route to the appropriate specialist agent:
        
        - TRIAGE_AGENT: Symptoms, pain, discomfort, emergency situations
        - APPOINTMENT_AGENT: Scheduling, rescheduling, appointment questions
        - VIRTUAL_ASSISTANT: Medication questions, general education, post-procedure care
        - CLINICAL_DOCS: Documentation requests, test results, medical records
        
        Return ONLY the agent name, nothing else.
        """
    
    def route_query(self, query: str, conversation_context: dict) -> Literal[
        "TRIAGE_AGENT", "APPOINTMENT_AGENT", "VIRTUAL_ASSISTANT", "CLINICAL_DOCS", "END"
    ]:
        """Determine which agent should handle the query"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Patient Query: {query}
            Context: {conversation_context}
            
            Which agent should handle this? Return one of:
            TRIAGE_AGENT, APPOINTMENT_AGENT, VIRTUAL_ASSISTANT, CLINICAL_DOCS, or END
            """)
        ]
        
        response = self.llm.invoke(messages)
        agent_name = response.content.strip()
        
        return agent_name if agent_name in [
            "TRIAGE_AGENT", "APPOINTMENT_AGENT", "VIRTUAL_ASSISTANT", "CLINICAL_DOCS"
        ] else "END"