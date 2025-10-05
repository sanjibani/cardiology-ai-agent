from typing import Dict
from datetime import datetime
import json

class EmergencyEscalationTool:
    """Tool for handling emergency escalations"""
    
    def __init__(self):
        self.name = "emergency_escalation"
        self.description = "Handle emergency situations and escalation procedures"
        
        # Emergency keywords that trigger immediate escalation
        self.emergency_keywords = [
            "chest pain", "can't breathe", "heart attack", "crushing pain",
            "pain radiating", "loss of consciousness", "severe shortness of breath",
            "cardiac arrest", "emergency", "911", "ambulance"
        ]
        
        # Emergency contact information
        self.emergency_contacts = {
            "emergency_services": "911",
            "cardiology_emergency": "555-CARD-911",
            "hospital_emergency": "555-HOSP-ER",
            "poison_control": "1-800-222-1222"
        }
    
    def assess_emergency_level(self, patient_query: str, patient_data: Dict) -> Dict:
        """Assess if query indicates an emergency situation"""
        
        query_lower = patient_query.lower()
        emergency_indicators = []
        
        # Check for emergency keywords
        for keyword in self.emergency_keywords:
            if keyword in query_lower:
                emergency_indicators.append(keyword)
        
        # Assess patient risk factors
        high_risk_conditions = ["previous heart attack", "coronary artery disease", "heart failure"]
        risk_factors = []
        
        patient_conditions = patient_data.get('conditions', [])
        for condition in patient_conditions:
            if any(risk_cond in condition.lower() for risk_cond in high_risk_conditions):
                risk_factors.append(condition)
        
        # Determine emergency level
        if emergency_indicators:
            if len(emergency_indicators) >= 2 or any(critical in query_lower for critical in 
                ["chest pain", "can't breathe", "heart attack", "cardiac arrest"]):
                emergency_level = "CRITICAL"
            else:
                emergency_level = "HIGH"
        elif risk_factors and any(urgent in query_lower for urgent in 
            ["pain", "shortness of breath", "dizzy", "faint"]):
            emergency_level = "MODERATE"
        else:
            emergency_level = "LOW"
        
        return {
            "emergency_level": emergency_level,
            "emergency_indicators": emergency_indicators,
            "risk_factors": risk_factors,
            "requires_immediate_action": emergency_level in ["CRITICAL", "HIGH"],
            "assessment_time": datetime.now().isoformat()
        }
    
    def trigger_emergency_response(self, emergency_assessment: Dict, patient_data: Dict) -> Dict:
        """Trigger appropriate emergency response based on assessment"""
        
        emergency_level = emergency_assessment["emergency_level"]
        
        if emergency_level == "CRITICAL":
            return self._critical_emergency_response(patient_data, emergency_assessment)
        elif emergency_level == "HIGH":
            return self._high_priority_response(patient_data, emergency_assessment)
        elif emergency_level == "MODERATE":
            return self._moderate_priority_response(patient_data, emergency_assessment)
        else:
            return self._low_priority_response(patient_data, emergency_assessment)
    
    def _critical_emergency_response(self, patient_data: Dict, assessment: Dict) -> Dict:
        """Handle critical emergency situations"""
        
        return {
            "response_type": "CRITICAL_EMERGENCY",
            "immediate_action": "CALL 911 IMMEDIATELY",
            "instructions": [
                "Call 911 right now",
                "Do not drive yourself to the hospital",
                "If experiencing chest pain, chew aspirin if not allergic",
                "Stay calm and follow dispatcher instructions",
                "Have someone stay with you if possible"
            ],
            "emergency_contacts": self.emergency_contacts,
            "patient_info_for_ems": {
                "patient_id": patient_data.get('patient_id'),
                "age": patient_data.get('age'),
                "conditions": patient_data.get('conditions', []),
                "medications": patient_data.get('medications', []),
                "allergies": patient_data.get('allergies', [])
            },
            "escalation_logged": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _high_priority_response(self, patient_data: Dict, assessment: Dict) -> Dict:
        """Handle high priority situations"""
        
        return {
            "response_type": "HIGH_PRIORITY",
            "immediate_action": "Contact cardiology emergency line",
            "instructions": [
                f"Call cardiology emergency: {self.emergency_contacts['cardiology_emergency']}",
                "If unable to reach cardiology, call 911",
                "Do not wait for symptoms to worsen",
                "Prepare to go to emergency room",
                "Bring current medications and insurance cards"
            ],
            "follow_up_required": True,
            "escalation_logged": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _moderate_priority_response(self, patient_data: Dict, assessment: Dict) -> Dict:
        """Handle moderate priority situations"""
        
        return {
            "response_type": "MODERATE_PRIORITY",
            "immediate_action": "Schedule urgent appointment",
            "instructions": [
                "Contact your cardiologist's office today",
                "Request same-day or next-day appointment",
                "Monitor symptoms closely",
                "Call emergency if symptoms worsen",
                "Do not ignore persistent symptoms"
            ],
            "monitoring_required": True,
            "follow_up_timeframe": "within 24 hours",
            "timestamp": datetime.now().isoformat()
        }
    
    def _low_priority_response(self, patient_data: Dict, assessment: Dict) -> Dict:
        """Handle low priority situations"""
        
        return {
            "response_type": "ROUTINE",
            "immediate_action": "Schedule routine follow-up",
            "instructions": [
                "Contact your cardiologist for routine appointment",
                "Continue current medications as prescribed",
                "Monitor symptoms and report changes",
                "Follow up if concerns persist"
            ],
            "follow_up_timeframe": "within 1-2 weeks",
            "timestamp": datetime.now().isoformat()
        }
    
    def log_escalation(self, escalation_data: Dict) -> bool:
        """Log emergency escalation for audit trail"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "escalation_type": escalation_data.get("response_type"),
            "patient_id": escalation_data.get("patient_info_for_ems", {}).get("patient_id"),
            "emergency_level": escalation_data.get("emergency_level"),
            "actions_taken": escalation_data.get("instructions", []),
            "follow_up_required": escalation_data.get("follow_up_required", False)
        }
        
        # In production, this would write to a secure audit log
        try:
            with open('/tmp/emergency_escalations.log', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            return True
        except Exception:
            return False