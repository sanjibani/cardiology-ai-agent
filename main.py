from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

from workflow import CardiologyWorkflow
from models.schemas import PatientQuery, AgentResponse

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Cardiology AI Multi-Agent System",
    description="LangGraph-based multi-agent system for cardiology patient triage, appointments, and virtual assistance",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the workflow
workflow = CardiologyWorkflow()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main landing page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/hospital", response_class=HTMLResponse)
async def hospital_dashboard(request: Request):
    """Serve the hospital dashboard interface"""
    return templates.TemplateResponse("hospital_dashboard.html", {"request": request})


@app.get("/patient", response_class=HTMLResponse)
async def patient_portal(request: Request):
    """Serve the patient portal interface"""
    return templates.TemplateResponse("patient_portal.html", {"request": request})


@app.get("/doctor", response_class=HTMLResponse)
async def doctor_interface(request: Request):
    """Serve the doctor interface"""
    return templates.TemplateResponse("doctor_interface.html", {"request": request})


@app.get("/emergency", response_class=HTMLResponse)
async def emergency_triage(request: Request):
    """Serve the emergency triage interface"""
    return templates.TemplateResponse("emergency_triage.html", {"request": request})


class ChatRequest(BaseModel):
    patient_id: str
    message: str
    conversation_context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    agent_used: str
    structured_data: Optional[Dict[str, Any]] = None
    requires_follow_up: bool = False
    emergency_alert: bool = False

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint for patient interactions"""
    
    try:
        # Create patient query
        patient_query = PatientQuery(
            patient_id=request.patient_id,
            query_text=request.message
        )
        
        # Process through workflow
        result = await workflow.process_query(
            patient_query, 
            request.conversation_context or {}
        )
        
        return ChatResponse(
            response=result["response"],
            agent_used=result["agent_used"],
            structured_data=result.get("structured_data"),
            requires_follow_up=result.get("requires_follow_up", False),
            emergency_alert=result.get("emergency_alert", False)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/triage")
async def triage_endpoint(request: ChatRequest):
    """Dedicated triage endpoint for symptom assessment"""
    
    try:
        result = await workflow.run_triage_assessment(
            request.patient_id,
            request.message,
            request.conversation_context or {}
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in triage assessment: {str(e)}")

@app.post("/appointment")
async def appointment_endpoint(request: ChatRequest):
    """Dedicated appointment booking endpoint"""
    
    try:
        result = await workflow.handle_appointment_request(
            request.patient_id,
            request.message,
            request.conversation_context or {}
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling appointment: {str(e)}")

@app.get("/patient/{patient_id}/appointments")
async def get_patient_appointments(patient_id: str):
    """Get appointments for a patient (mock data for demo)"""
    try:
        # Mock appointment data for demonstration
        appointments = [
            {
                "id": f"apt_{patient_id}_001",
                "type": "Cardiology Consultation",
                "date": "2024-01-15",
                "time": "10:00 AM",
                "status": "confirmed",
                "notes": "Follow-up for hypertension management"
            },
            {
                "id": f"apt_{patient_id}_002", 
                "type": "ECG Screening",
                "date": "2024-01-22",
                "time": "2:30 PM",
                "status": "pending",
                "notes": "Routine cardiovascular screening"
            }
        ]
        
        return {
            "patient_id": patient_id,
            "appointments": appointments,
            "total_count": len(appointments)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving appointments: {str(e)}")

@app.get("/patient/{patient_id}")
async def get_patient_info(patient_id: str):
    """Get patient information"""
    
    try:
        patient_info = workflow.get_patient_info(patient_id)
        if not patient_info:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return patient_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving patient info: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cardiology-ai-agent"}


@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "service": "Cardiology AI Multi-Agent System",
        "version": "1.0.0", 
        "description": "LangGraph-based multi-agent system",
        "endpoints": {
            "chat": "/chat",
            "triage": "/triage",
            "appointment": "/appointment",
            "patient_info": "/patient/{patient_id}",
            "patient_appointments": "/patient/{patient_id}/appointments",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )