from typing import Dict, Optional
import json

class PatientLookupTool:
    """Tool for looking up patient information"""
    
    def __init__(self):
        self.name = "patient_lookup"
        self.description = "Look up patient information by ID or demographic data"
        
    def lookup_patient(self, patient_id: str) -> Optional[Dict]:
        """Look up patient by ID"""
        # Mock patient lookup - in production, this would query a real database
        try:
            with open('/Users/sanjibanichoudhury/Desktop/repositories/cardiology-ai-agent/data/sample_patient_data.json', 'r') as f:
                patients = json.load(f)
                return patients.get(patient_id)
        except FileNotFoundError:
            return None
    
    def search_patients(self, criteria: Dict) -> list:
        """Search patients by criteria"""
        # Mock search - in production, this would query a database with proper indexing
        try:
            with open('/Users/sanjibanichoudhury/Desktop/repositories/cardiology-ai-agent/data/sample_patient_data.json', 'r') as f:
                patients = json.load(f)
                results = []
                
                for patient_id, patient_data in patients.items():
                    match = True
                    for key, value in criteria.items():
                        if key in patient_data and patient_data[key] != value:
                            match = False
                            break
                    if match:
                        results.append({**patient_data, 'patient_id': patient_id})
                
                return results
        except FileNotFoundError:
            return []
    
    def get_patient_history(self, patient_id: str) -> Dict:
        """Get patient medical history"""
        patient = self.lookup_patient(patient_id)
        if patient:
            return {
                'conditions': patient.get('conditions', []),
                'medications': patient.get('medications', []),
                'last_visit': patient.get('last_visit'),
                'risk_factors': patient.get('risk_factors', []),
                'allergies': patient.get('allergies', [])
            }
        return {}