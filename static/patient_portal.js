// Patient Portal JavaScript
const API_BASE = window.location.origin;
const PATIENT_ID = 'patient-001'; // In real app, this would be from auth session

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

// Symptom assessment
async function checkSymptoms() {
    const symptoms = document.getElementById('symptomsInput').value.trim();
    
    if (!symptoms) {
        showMessage('Please describe your symptoms', 'error');
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/triage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: PATIENT_ID,
                message: symptoms,
                conversation_context: {}
            })
        });
        
        const data = await response.json();
        displaySymptomResult(data);
        hideLoading();
        
    } catch (error) {
        hideLoading();
        showMessage('Error assessing symptoms. Please try again.', 'error');
    }
}

function displaySymptomResult(data) {
    const resultDiv = document.getElementById('symptomResult');
    const assessment = data.structured_data?.triage_assessment || {};
    
    resultDiv.innerHTML = `
        <div class="p-4 bg-blue-50 rounded-lg border-l-4 border-blue-500">
            <h4 class="font-bold text-blue-800 mb-2">Assessment Result</h4>
            <p><strong>Urgency:</strong> ${assessment.urgency_level || 'Routine'}</p>
            <p><strong>Recommendation:</strong> ${assessment.recommended_action || 'Consult your healthcare provider'}</p>
            <div class="mt-3">
                <p class="text-sm">${assessment.reasoning || 'Assessment completed'}</p>
            </div>
        </div>
    `;
    resultDiv.classList.remove('hidden');
}

// Chat functionality
async function sendPatientMessage() {
    const input = document.getElementById('patientChatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    addChatMessage(message, 'user');
    input.value = '';
    
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: PATIENT_ID,
                message: message,
                conversation_context: {}
            })
        });
        
        const data = await response.json();
        addChatMessage(data.response, 'assistant');
        
    } catch (error) {
        addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    }
}

function addChatMessage(message, sender) {
    const chatContainer = document.getElementById('patientChatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} mb-3`;
    
    const messageBubble = document.createElement('div');
    messageBubble.className = `p-3 rounded-lg max-w-xs ${
        sender === 'user' 
            ? 'bg-green-500 text-white' 
            : 'bg-gray-200 text-gray-800'
    }`;
    messageBubble.textContent = message;
    
    messageDiv.appendChild(messageBubble);
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Appointment booking
async function bookPatientAppointment() {
    const type = document.getElementById('patientAppointmentType').value;
    const date = document.getElementById('patientAppointmentDate').value;
    const notes = document.getElementById('patientAppointmentNotes').value;
    
    if (!date) {
        showMessage('Please select a date', 'error');
        return;
    }
    
    try {
        showLoading();
        
        const message = `I need to schedule a ${type} appointment for ${date}. ${notes ? 'Notes: ' + notes : ''}`;
        
        const response = await fetch(`${API_BASE}/appointment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: PATIENT_ID,
                message: message,
                conversation_context: {}
            })
        });
        
        const data = await response.json();
        hideLoading();
        showMessage('Appointment request submitted successfully!');
        
        // Clear form
        document.getElementById('patientAppointmentNotes').value = '';
        
    } catch (error) {
        hideLoading();
        showMessage('Error booking appointment. Please try again.', 'error');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Set default date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('patientAppointmentDate').value = tomorrow.toISOString().split('T')[0];
    
    // Initialize chat with welcome message
    setTimeout(() => {
        addChatMessage('Hello! I\'m your AI health assistant. How can I help you today?', 'assistant');
    }, 1000);
});