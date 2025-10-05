from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.schemas import AppointmentRequest
from datetime import datetime, timedelta
import json

class AppointmentAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.system_prompt = """You are an appointment scheduling specialist for a cardiology practice.
        
        Available appointment types:
        - consultation: New patient or specialty consultations (60 min)
        - follow-up: Routine follow-up visits (30 min)
        - procedure: Diagnostic procedures like stress tests, echocardiograms (varies)
        - emergency: Same-day urgent appointments (30 min)
        
        Available time slots:
        - Monday-Friday: 8:00 AM - 5:00 PM
        - Emergency slots: Monday-Friday: 8:00 AM - 6:00 PM
        
        Consider patient urgency level and current availability when scheduling.
        """
    
    def schedule_appointment(self, patient_id: str, request: str, patient_data: dict, urgency: str = "routine") -> dict:
        """Process appointment scheduling request"""
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
            Patient ID: {patient_id}
            Request: {request}
            Patient History: {json.dumps(patient_data)}
            Urgency Level: {urgency}
            Current Date: {datetime.now().strftime('%Y-%m-%d')}
            
            Process this appointment request and return JSON with:
            {{
                "appointment_type": "consultation|follow-up|procedure|emergency",
                "suggested_dates": ["date1", "date2", "date3"],
                "estimated_duration": "duration in minutes",
                "pre_appointment_instructions": "any prep needed",
                "scheduling_notes": "additional information",
                "requires_approval": true/false
            }}
            """)
        ]
        
        response = self.llm.invoke(messages)
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "appointment_type": "consultation",
                "suggested_dates": [
                    (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
                    (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d')
                ],
                "estimated_duration": "60 minutes",
                "pre_appointment_instructions": "Please bring insurance cards and current medications list",
                "scheduling_notes": "Standard appointment scheduling",
                "requires_approval": False
            }
    
    def check_availability(self, date: str, appointment_type: str) -> dict:
        """Check appointment availability for a given date"""
        # Mock availability check - in production, this would query a real scheduling system
        available_slots = [
            "9:00 AM", "10:30 AM", "2:00 PM", "3:30 PM"
        ]
        
        return {
            "date": date,
            "available_slots": available_slots,
            "appointment_type": appointment_type
        }
    
    def confirm_appointment(self, appointment_details: dict) -> dict:
        """Confirm appointment booking"""
        return {
            "status": "confirmed",
            "appointment_id": f"CARD-{datetime.now().strftime('%Y%m%d')}-{appointment_details.get('patient_id', 'XXX')}",
            "details": appointment_details,
            "confirmation_sent": True
        }