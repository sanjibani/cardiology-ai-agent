// Emergency Triage JavaScript
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

// Emergency triage assessment
async function performEmergencyTriage() {
    const patientId = document.getElementById('emergencyPatientId').value || 'Walk-in';
    const chiefComplaint = document.getElementById('chiefComplaint').value;
    const symptoms = document.getElementById('emergencySymptoms').value.trim();
    
    if (!symptoms) {
        showMessage('Please describe the symptoms', 'error');
        return;
    }
    
    try {
        showLoading();
        
        let message = `Chief complaint: ${chiefComplaint || 'Not specified'}. Symptoms: ${symptoms}`;
        
        // Add vital signs if provided
        const vitals = getVitalSigns();
        if (vitals) {
            message += `. Vital signs: ${vitals}`;
        }
        
        const response = await fetch(`${API_BASE}/triage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                message: message,
                conversation_context: { emergency: true }
            })
        });
        
        const data = await response.json();
        displayTriageResults(data);
        hideLoading();
        
        // Update emergency counts
        updateEmergencyCounts(data);
        
    } catch (error) {
        hideLoading();
        showMessage('Error performing triage assessment', 'error');
    }
}

function getVitalSigns() {
    const inputs = document.querySelectorAll('#emergencySymptoms').closest('.grid').nextElementSibling.querySelectorAll('input');
    const vitals = [];
    
    inputs.forEach((input, index) => {
        if (input.value) {
            const labels = ['BP', 'HR', 'O2 Sat', 'Temp'];
            vitals.push(`${labels[index]}: ${input.value}`);
        }
    });
    
    return vitals.length > 0 ? vitals.join(', ') : null;
}

function displayTriageResults(data) {
    const resultsDiv = document.getElementById('triageResults');
    const contentDiv = document.getElementById('triageContent');
    
    const assessment = data.structured_data?.triage_assessment || {};
    const urgency = assessment.urgency_level || 'routine';
    
    const urgencyColors = {
        'emergency': 'bg-red-50 border-red-500 text-red-800',
        'urgent': 'bg-orange-50 border-orange-500 text-orange-800',
        'routine': 'bg-yellow-50 border-yellow-500 text-yellow-800',
        'informational': 'bg-green-50 border-green-500 text-green-800'
    };
    
    const colorClass = urgencyColors[urgency] || urgencyColors['routine'];
    
    contentDiv.innerHTML = `
        <div class="p-4 ${colorClass} border-l-4 rounded-lg">
            <div class="flex justify-between items-start mb-4">
                <div>
                    <h4 class="text-xl font-bold uppercase">${urgency} PRIORITY</h4>
                    <p class="text-sm">Severity Score: ${assessment.severity_score || 'N/A'}/10</p>
                </div>
                <div class="text-right">
                    <span class="px-3 py-1 rounded-full text-xs font-bold bg-white bg-opacity-50">
                        ${urgency === 'emergency' ? 'IMMEDIATE' : urgency === 'urgent' ? '30 MIN' : '2 HRS'}
                    </span>
                </div>
            </div>
            
            <div class="space-y-3">
                <div>
                    <p class="font-semibold">Recommended Action:</p>
                    <p>${assessment.recommended_action || 'Standard care protocol'}</p>
                </div>
                
                ${assessment.symptoms ? `
                    <div>
                        <p class="font-semibold">Identified Symptoms:</p>
                        <p>${assessment.symptoms.join(', ')}</p>
                    </div>
                ` : ''}
                
                <div>
                    <p class="font-semibold">Clinical Reasoning:</p>
                    <p class="text-sm">${assessment.reasoning || 'Assessment completed'}</p>
                </div>
                
                ${urgency === 'emergency' ? `
                    <div class="mt-4 p-3 bg-red-600 text-white rounded-lg">
                        <div class="flex items-center justify-between">
                            <span class="font-bold">🚨 EMERGENCY ALERT ACTIVATED</span>
                            <button onclick="triggerEmergencyResponse()" class="bg-white text-red-600 px-3 py-1 rounded font-bold">
                                ACTIVATE RESPONSE
                            </button>
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    resultsDiv.classList.remove('hidden');
}

function updateEmergencyCounts(data) {
    const assessment = data.structured_data?.triage_assessment || {};
    const urgency = assessment.urgency_level || 'routine';
    
    // Update counts based on urgency
    if (urgency === 'emergency') {
        const emergencyCount = document.getElementById('emergencyCount');
        emergencyCount.textContent = parseInt(emergencyCount.textContent) + 1;
    } else if (urgency === 'urgent') {
        const urgentCount = document.getElementById('urgentCount');
        urgentCount.textContent = parseInt(urgentCount.textContent) + 1;
    } else {
        const routineCount = document.getElementById('routineCount');
        routineCount.textContent = parseInt(routineCount.textContent) + 1;
    }
}

function triggerEmergencyResponse() {
    showMessage('🚨 Emergency response team alerted!', 'error');
    
    // In a real system, this would:
    // - Alert emergency team
    // - Reserve trauma room
    // - Notify specialists
    // - Prepare emergency protocols
    
    console.log('Emergency response triggered at:', new Date().toISOString());
}

// Simulate real-time updates
function updateEmergencyDashboard() {
    // In a real system, this would fetch live data
    const counts = {
        emergency: Math.max(0, parseInt(document.getElementById('emergencyCount').textContent) + Math.floor(Math.random() * 2) - 1),
        urgent: Math.max(0, parseInt(document.getElementById('urgentCount').textContent) + Math.floor(Math.random() * 3) - 1),
        routine: Math.max(0, parseInt(document.getElementById('routineCount').textContent) + Math.floor(Math.random() * 4) - 2)
    };
    
    document.getElementById('emergencyCount').textContent = counts.emergency;
    document.getElementById('urgentCount').textContent = counts.urgent;
    document.getElementById('routineCount').textContent = counts.routine;
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Update dashboard every 30 seconds
    setInterval(updateEmergencyDashboard, 30000);
});