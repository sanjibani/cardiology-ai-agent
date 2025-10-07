from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

class VirtualAssistantAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.3)
        self.system_prompt = """You are a virtual cardiology assistant providing patient education and support.
        
        You can help with:
        - Medication information and side effects
        - Pre and post-procedure care instructions
        - General cardiac health education
        - Lifestyle recommendations
        - Diet and exercise guidance for cardiac patients
        
        IMPORTANT: Never provide emergency medical advice. Always direct emergencies to call 911.
        Never diagnose conditions or change medication dosages.
        Always recommend consulting with their cardiologist for specific medical questions.
        """
        
        # Load knowledge base
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> dict:
        """Load cardiology knowledge base"""
        try:
            with open('/Users/sanjibanichoudhury/Desktop/repositories/cardiology-ai-agent/data/cardiology_knowledge_base.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "medications": {},
                "procedures": {},
                "conditions": {},
                "lifestyle": {}
            }
    
    def provide_assistance(self, query: str, patient_data: dict) -> dict:
        """Provide educational assistance and information"""
        
        # Check if query relates to specific areas in knowledge base
        relevant_info = self._find_relevant_info(query)
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Patient Query: {query}
            Patient Background: {json.dumps(patient_data)}
            Relevant Knowledge: {json.dumps(relevant_info)}
            
            Provide helpful, educational information. Include:
            1. Direct answer to their question
            2. Additional relevant education
            3. When to contact their cardiologist
            4. Any lifestyle recommendations
            
            Keep response conversational and supportive.
            """)
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "response": response.content,
            "category": self._categorize_query(query),
            "educational_resources": self._get_educational_resources(query),
            "follow_up_recommended": self._needs_follow_up(query)
        }
    
    def _find_relevant_info(self, query: str) -> dict:
        """Find relevant information from knowledge base"""
        query_lower = query.lower()
        relevant = {}
        
        # Simple keyword matching - in production, use semantic search
        for category, items in self.knowledge_base.items():
            relevant[category] = {}
            for key, value in items.items():
                if any(keyword in query_lower for keyword in key.lower().split()):
                    relevant[category][key] = value
        
        return relevant
    
    def _categorize_query(self, query: str) -> str:
        """Categorize the type of query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['medication', 'pill', 'dose', 'drug']):
            return 'medication'
        elif any(word in query_lower for word in ['procedure', 'test', 'surgery', 'catheter']):
            return 'procedure'
        elif any(word in query_lower for word in ['diet', 'exercise', 'lifestyle', 'activity']):
            return 'lifestyle'
        elif any(word in query_lower for word in ['symptom', 'pain', 'chest', 'breath']):
            return 'symptoms'
        else:
            return 'general'
    
    def _get_educational_resources(self, query: str) -> list:
        """Get relevant educational resources"""
        category = self._categorize_query(query)
        
        resources = {
            'medication': [
                'American Heart Association - Cardiovascular Medications',
                'FDA Drug Information Database'
            ],
            'procedure': [
                'American College of Cardiology - Patient Procedures',
                'Heart Procedure Education Videos'
            ],
            'lifestyle': [
                'AHA Heart-Healthy Living Guidelines',
                'Cardiac Rehabilitation Programs'
            ],
            'symptoms': [
                'When to Seek Emergency Care',
                'Understanding Heart Symptoms'
            ],
            'general': [
                'American Heart Association Patient Resources',
                'Heart.org Patient Education'
            ]
        }
        
        return resources.get(category, resources['general'])
    
    def _needs_follow_up(self, query: str) -> bool:
        """Determine if query needs medical follow-up"""
        urgent_keywords = [
            'pain', 'chest', 'breathing', 'dizzy', 'faint', 
            'medication change', 'side effect', 'emergency'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in urgent_keywords)