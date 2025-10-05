// Doctor Interface JavaScript
const API_BASE = window.location.origin;

// Show loading state
function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

// Show message
function showMessage(message, type = 'success') {
    const messageDiv = document.createElement('div');
    const bgColor = type === 'success' ? 'bg-green-500' : 'bg-red-500';
    messageDiv.className = `${bgColor} text-white px-4 py-2 rounded-lg fixed top-4 right-4 z-50`;
    messageDiv.textContent = message;
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}

// Load patient data for doctor
async function loadPatientForDoctor() {
    const patientSelect = document.getElementById('doctorPatientSelect');
    const patientId = patientSelect.value;
    
    try {
        const response = await fetch(`${API_BASE}/patient/${patientId}`);
        const data = await response.json();
        
        document.getElementById('doctorPatientInfo').innerHTML = `
            <div class="p-4 bg-blue-50 rounded-lg">
                <h4 class="font-bold text-blue-800 mb-2">Patient Information</h4>
                <p><strong>Name:</strong> ${data.name}</p>
                <p><strong>Age:</strong> ${data.age}</p>
                <p><strong>ID:</strong> ${data.patient_id}</p>
                <p><strong>Last Visit:</strong> ${data.last_visit || 'N/A'}</p>
            </div>
            <div class="p-4 bg-red-50 rounded-lg">
                <h4 class="font-bold text-red-800 mb-2">Current Conditions</h4>
                <div class="space-y-1">
                    ${data.conditions.map(condition => 
                        `<span class="inline-block bg-red-200 text-red-800 text-xs px-2 py-1 rounded">${condition}</span>`
                    ).join(' ')}
                </div>
            </div>
        `;
        
    } catch (error) {
        showMessage('Error loading patient data', 'error');
    }
}

// AI Clinical Assistant Functions
async function generateClinicalSummary() {
    const patientId = document.getElementById('doctorPatientSelect').value;
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                message: "Generate a comprehensive clinical summary for this patient including medical history, current conditions, and treatment recommendations",
                conversation_context: { agent_type: "clinical_docs" }
            })
        });
        
        const data = await response.json();
        showAnalysisResult(data.response, 'Clinical Summary');
        hideLoading();
        
    } catch (error) {
        hideLoading();
        showMessage('Error generating clinical summary', 'error');
    }
}

async function analyzeMedications() {
    const patientId = document.getElementById('doctorPatientSelect').value;
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                message: "Analyze current medications for interactions, side effects, and optimization opportunities",
                conversation_context: {}
            })
        });
        
        const data = await response.json();
        showAnalysisResult(data.response, 'Medication Analysis');
        hideLoading();
        
    } catch (error) {
        hideLoading();
        showMessage('Error analyzing medications', 'error');
    }
}

async function riskAssessment() {
    const patientId = document.getElementById('doctorPatientSelect').value;
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/triage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                message: "Perform comprehensive cardiovascular risk assessment based on patient history and current status",
                conversation_context: {}
            })
        });
        
        const data = await response.json();
        showAnalysisResult(data.response, 'Risk Assessment');
        hideLoading();
        
    } catch (error) {
        hideLoading();
        showMessage('Error performing risk assessment', 'error');
    }
}

function showAnalysisResult(content, title) {
    const resultsDiv = document.getElementById('aiAnalysisResults');
    const contentDiv = document.getElementById('analysisContent');
    
    contentDiv.innerHTML = `
        <h4 class="font-bold text-lg mb-3">${title}</h4>
        <div class="prose max-w-none">
            <p>${content}</p>
        </div>
    `;
    
    resultsDiv.classList.remove('hidden');
}

// Clinical Notes Functions
function saveClinicalNotes() {
    const notes = document.getElementById('clinicalNotes').value;
    
    if (!notes.trim()) {
        showMessage('Please enter clinical notes before saving', 'error');
        return;
    }
    
    // In a real application, this would save to the database
    showMessage('Clinical notes saved successfully');
}

async function generateReport() {
    const patientId = document.getElementById('doctorPatientSelect').value;
    const notes = document.getElementById('clinicalNotes').value;
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                message: `Generate a clinical report based on these notes: ${notes}`,
                conversation_context: { agent_type: "clinical_docs" }
            })
        });
        
        const data = await response.json();
        showAnalysisResult(data.response, 'Generated Clinical Report');
        hideLoading();
        
    } catch (error) {
        hideLoading();
        showMessage('Error generating report', 'error');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadPatientForDoctor();
});