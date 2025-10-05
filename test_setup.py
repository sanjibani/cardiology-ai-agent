#!/usr/bin/env python3
"""
Simple test script to verify the Cardiology AI system setup
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all modules can be imported successfully"""
    print("Testing imports...")
    
    try:
        from models.schemas import SymptomAssessment, PatientQuery, AppointmentRequest
        print("✅ Models imported successfully")
    except ImportError as e:
        print(f"❌ Models import failed: {e}")
        return False
    
    try:
        from models.state import AgentState
        print("✅ State models imported successfully")
    except ImportError as e:
        print(f"❌ State models import failed: {e}")
        return False
    
    try:
        from tools.patient_lookup import PatientLookupTool
        from tools.appointment_system import AppointmentSystemTool
        from tools.knowledge_base import KnowledgeBaseTool
        from tools.emergency_escalation import EmergencyEscalationTool
        print("✅ Tools imported successfully")
    except ImportError as e:
        print(f"❌ Tools import failed: {e}")
        return False
    
    # Test data files exist
    try:
        knowledge_base_path = project_root / "data" / "cardiology_knowledge_base.json"
        patient_data_path = project_root / "data" / "sample_patient_data.json"
        
        if knowledge_base_path.exists():
            print("✅ Knowledge base file found")
        else:
            print("❌ Knowledge base file missing")
            return False
            
        if patient_data_path.exists():
            print("✅ Patient data file found")
        else:
            print("❌ Patient data file missing")
            return False
            
    except Exception as e:
        print(f"❌ Data files check failed: {e}")
        return False
    
    return True

def test_tools():
    """Test that tools work correctly"""
    print("\nTesting tools functionality...")
    
    try:
        from tools.patient_lookup import PatientLookupTool
        patient_tool = PatientLookupTool()
        
        # Test patient lookup
        patient = patient_tool.lookup_patient("P001")
        if patient:
            print("✅ Patient lookup working")
        else:
            print("❌ Patient lookup failed")
            return False
            
    except Exception as e:
        print(f"❌ Patient lookup test failed: {e}")
        return False
    
    try:
        from tools.knowledge_base import KnowledgeBaseTool
        kb_tool = KnowledgeBaseTool()
        
        # Test knowledge base search
        results = kb_tool.search_knowledge("medication")
        if results:
            print("✅ Knowledge base search working")
        else:
            print("❌ Knowledge base search failed")
            return False
            
    except Exception as e:
        print(f"❌ Knowledge base test failed: {e}")
        return False
    
    try:
        from tools.appointment_system import AppointmentSystemTool
        apt_tool = AppointmentSystemTool()
        
        # Test appointment system
        availability = apt_tool.check_availability("2025-10-10", "routine")
        if availability:
            print("✅ Appointment system working")
        else:
            print("❌ Appointment system failed")
            return False
            
    except Exception as e:
        print(f"❌ Appointment system test failed: {e}")
        return False
    
    return True

def test_fastapi_setup():
    """Test FastAPI application setup"""
    print("\nTesting FastAPI setup...")
    
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        # Create a minimal test app
        app = FastAPI()
        
        @app.get("/health")
        def health_check():
            return {"status": "healthy"}
        
        client = TestClient(app)
        response = client.get("/health")
        
        if response.status_code == 200:
            print("✅ FastAPI setup working")
            return True
        else:
            print("❌ FastAPI setup failed")
            return False
            
    except Exception as e:
        print(f"❌ FastAPI test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🏥 Cardiology AI Multi-Agent System - Setup Test")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Run tests
    all_tests_passed &= test_imports()
    all_tests_passed &= test_tools()
    all_tests_passed &= test_fastapi_setup()
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All tests passed! The system setup is working correctly.")
        print("\nNext steps:")
        print("1. Set your OpenAI API key in the .env file")
        print("2. Run: python main.py")
        print("3. Visit: http://localhost:8000/docs for API documentation")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()