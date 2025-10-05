from typing import Dict, List
import json

class KnowledgeBaseTool:
    """Tool for accessing cardiology knowledge base"""
    
    def __init__(self):
        self.name = "knowledge_base"
        self.description = "Access cardiology knowledge base for medical information"
        self.knowledge_base = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> Dict:
        """Load the cardiology knowledge base"""
        try:
            with open('/Users/sanjibanichoudhury/Desktop/repositories/cardiology-ai-agent/data/cardiology_knowledge_base.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._create_default_knowledge_base()
    
    def _create_default_knowledge_base(self) -> Dict:
        """Create default knowledge base structure"""
        return {
            "medications": {
                "ACE_inhibitors": {
                    "common_names": ["lisinopril", "enalapril", "captopril"],
                    "purpose": "Lower blood pressure and reduce heart workload",
                    "side_effects": ["dry cough", "elevated potassium", "dizziness"],
                    "monitoring": "Blood pressure, kidney function, potassium levels"
                },
                "beta_blockers": {
                    "common_names": ["metoprolol", "atenolol", "propranolol"],
                    "purpose": "Slow heart rate and reduce blood pressure",
                    "side_effects": ["fatigue", "cold hands/feet", "depression"],
                    "monitoring": "Heart rate, blood pressure, blood sugar"
                }
            },
            "procedures": {
                "echocardiogram": {
                    "description": "Ultrasound imaging of the heart",
                    "preparation": "No special preparation needed",
                    "duration": "30-60 minutes",
                    "what_to_expect": "Gel applied to chest, ultrasound probe moved around"
                },
                "stress_test": {
                    "description": "Test heart function during physical stress",
                    "preparation": "Avoid caffeine 24 hours before, wear comfortable shoes",
                    "duration": "60-90 minutes",
                    "what_to_expect": "Exercise on treadmill while monitoring heart"
                }
            },
            "conditions": {
                "hypertension": {
                    "description": "High blood pressure",
                    "risk_factors": ["age", "family history", "obesity", "smoking"],
                    "lifestyle_changes": ["low sodium diet", "regular exercise", "weight management"],
                    "monitoring": "Regular blood pressure checks"
                },
                "coronary_artery_disease": {
                    "description": "Narrowing of coronary arteries",
                    "symptoms": ["chest pain", "shortness of breath", "fatigue"],
                    "risk_factors": ["smoking", "diabetes", "high cholesterol"],
                    "treatment_options": ["medications", "lifestyle changes", "procedures"]
                }
            },
            "lifestyle": {
                "diet": {
                    "heart_healthy_foods": ["fish", "vegetables", "whole grains", "nuts"],
                    "foods_to_limit": ["saturated fats", "sodium", "added sugars"],
                    "portion_control": "Use smaller plates, eat slowly, stop when satisfied"
                },
                "exercise": {
                    "aerobic_recommendations": "150 minutes moderate activity per week",
                    "strength_training": "2 days per week",
                    "getting_started": "Start slowly, gradually increase intensity"
                }
            }
        }
    
    def search_knowledge(self, query: str, category: str = None) -> Dict:
        """Search knowledge base for relevant information"""
        query_lower = query.lower()
        results = {}
        
        categories_to_search = [category] if category else self.knowledge_base.keys()
        
        for cat in categories_to_search:
            if cat in self.knowledge_base:
                results[cat] = {}
                for item_key, item_value in self.knowledge_base[cat].items():
                    # Simple keyword matching
                    if self._matches_query(query_lower, item_key, item_value):
                        results[cat][item_key] = item_value
        
        return results
    
    def _matches_query(self, query: str, key: str, value: Dict) -> bool:
        """Check if an item matches the search query"""
        # Check key
        if query in key.lower():
            return True
        
        # Check values recursively
        if isinstance(value, dict):
            for v in value.values():
                if isinstance(v, str) and query in v.lower():
                    return True
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and query in item.lower():
                            return True
        
        return False
    
    def get_medication_info(self, medication_name: str) -> Dict:
        """Get information about a specific medication"""
        medication_name_lower = medication_name.lower()
        
        for med_class, info in self.knowledge_base.get("medications", {}).items():
            common_names = [name.lower() for name in info.get("common_names", [])]
            if medication_name_lower in common_names or medication_name_lower in med_class.lower():
                return {
                    "medication_class": med_class,
                    **info
                }
        
        return {"message": f"No information found for medication: {medication_name}"}
    
    def get_procedure_info(self, procedure_name: str) -> Dict:
        """Get information about a specific procedure"""
        procedure_name_lower = procedure_name.lower()
        
        for proc_name, info in self.knowledge_base.get("procedures", {}).items():
            if procedure_name_lower in proc_name.lower():
                return {
                    "procedure": proc_name,
                    **info
                }
        
        return {"message": f"No information found for procedure: {procedure_name}"}
    
    def get_lifestyle_recommendations(self, topic: str) -> Dict:
        """Get lifestyle recommendations for a specific topic"""
        topic_lower = topic.lower()
        
        lifestyle_info = self.knowledge_base.get("lifestyle", {})
        
        for category, info in lifestyle_info.items():
            if topic_lower in category.lower():
                return {
                    "category": category,
                    **info
                }
        
        # Return all lifestyle info if no specific match
        return lifestyle_info