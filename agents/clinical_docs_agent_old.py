from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
from datetime import datetime

class ClinicalDocsAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.system_prompt = """You are a clinical documentation specialist for cardiology.
        
        You can help with:
        - Generating clinical summaries
        - Organizing test results
        - Creating discharge instructions  
        - Summarizing patient interactions
        - Preparing referral documentation
        
        Maintain HIPAA compliance and medical accuracy in all documentation.
        Use proper medical terminology and follow clinical documentation standards.
        """
    
    def generate_clinical_summary(self, patient_data: dict, interaction_history: list) -> dict:
        """Generate clinical summary from patient interaction"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Patient Data: {json.dumps(patient_data)}
            Interaction History: {json.dumps(interaction_history)}
            
            Generate a clinical summary including:
            1. Chief complaint/reason for interaction
            2. Relevant medical history
            3. Assessment findings
            4. Recommendations made
            5. Follow-up actions needed
            
            Format as structured medical documentation.
            """)
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "summary": response.content,
            "generated_date": datetime.now().isoformat(),
            "summary_type": "clinical_interaction",
            "patient_id": patient_data.get('patient_id', 'unknown')
        }
    
    def create_discharge_instructions(self, patient_data: dict, procedure_type: str) -> dict:
        """Create post-procedure discharge instructions"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Patient: {json.dumps(patient_data)}
            Procedure: {procedure_type}
            
            Create comprehensive discharge instructions including:
            1. Activity restrictions
            2. Medication instructions
            3. Warning signs to watch for
            4. Follow-up appointment scheduling
            5. Emergency contact information
            
            Make instructions clear and patient-friendly.
            """)
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "instructions": response.content,
            "procedure_type": procedure_type,
            "created_date": datetime.now().isoformat(),
            "patient_id": patient_data.get('patient_id', 'unknown')
        }
    
    def format_test_results(self, test_data: dict, patient_context: dict) -> dict:
        """Format and interpret test results for patient communication"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Test Results: {json.dumps(test_data)}
            Patient Context: {json.dumps(patient_context)}
            
            Create patient-friendly interpretation of test results including:
            1. Summary of what tests were performed
            2. Key findings in understandable language
            3. What results mean for patient's health
            4. Any recommended actions
            5. Questions patient should ask their doctor
            
            Balance accuracy with readability.
            """)
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "interpretation": response.content,
            "test_type": test_data.get('test_type', 'unknown'),
            "results_date": datetime.now().isoformat(),
            "patient_id": patient_context.get('patient_id', 'unknown')
        }
    
    def generate_referral_note(self, patient_data: dict, referral_reason: str, specialist_type: str) -> dict:
        """Generate referral documentation"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Patient: {json.dumps(patient_data)}
            Referral Reason: {referral_reason}
            Specialist Type: {specialist_type}
            
            Generate professional referral note including:
            1. Patient demographics and relevant history
            2. Reason for referral
            3. Specific questions for specialist
            4. Relevant test results or findings
            5. Urgency level
            
            Use formal medical referral format.
            """)
        ]
        
        response = self.llm.invoke(messages)
        
        return {
            "referral_note": response.content,
            "specialist_type": specialist_type,
            "referral_reason": referral_reason,
            "created_date": datetime.now().isoformat(),
            "patient_id": patient_data.get('patient_id', 'unknown')
        }