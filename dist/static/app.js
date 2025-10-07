// API Configuration
const API_BASE = window.location.origin;
let assessmentCount = 0;
let urgentCases = 0;

// Utility Functions
function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function showMessage(message, type = 'success') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message-${type} fixed top-4 right-4 z-50 max-w-md transform transition-all duration-300`;
    messageDiv.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    document.body.appendChild(messageDiv);
    
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Triage Assessment Function
async function triageAssessment() {
    const patientId = document.getElementById('patientId').value;
    const symptoms = document.getElementById('symptomsInput').value;
    const resultDiv = document.getElementById('triageResult');
    
    if (!symptoms.trim()) {
        showMessage('Please describe your symptoms', 'error');
        return;
    }
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/triage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                message: symptoms,
                conversation_context: {}
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayTriageResult(data, resultDiv);
        
        // Update statistics
        assessmentCount++;
        document.getElementById('assessmentCount').textContent = assessmentCount;
        
        // Check for urgent cases
        if (data.structured_data?.triage_assessment?.urgency_level === 'emergency') {
            urgentCases++;
            document.getElementById('urgentCases').textContent = urgentCases;
            showEmergencyAlert(data.structured_data.triage_assessment);
        }
        
        hideLoading();
        
    } catch (error) {
        console.error('Error:', error);
        hideLoading();
        showMessage(`Error: ${error.message}`, 'error');
        resultDiv.innerHTML = `<div class="text-red-600 p-4 bg-red-50 rounded-lg">Error performing assessment. Please try again.</div>`;
        resultDiv.classList.remove('hidden');
    }
}

function displayTriageResult(data, container) {
    const urgencyColors = {
        'emergency': 'urgency-emergency',
        'urgent': 'urgency-urgent', 
        'routine': 'urgency-routine',
        'informational': 'urgency-informational'
    };
    
    const assessment = data.structured_data?.triage_assessment || {};
    const urgency = assessment.urgency_level || 'routine';
    const colorClass = urgencyColors[urgency] || urgencyColors['routine'];
    
    const severityScore = assessment.severity_score || 1;
    const severityBars = '█'.repeat(Math.floor(severityScore / 2)) + '░'.repeat(5 - Math.floor(severityScore / 2));
    
    container.className = `p-4 rounded-lg ${colorClass}`;
    container.innerHTML = `
        <div class="flex items-center mb-3">
            <i class="fas fa-stethoscope mr-2"></i>
            <h3 class="font-bold">AI Assessment Result</h3>
        </div>
        <div class="space-y-3">
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <p class="text-sm font-medium">Urgency Level:</p>
                    <p class="text-lg font-bold uppercase">${urgency}</p>
                </div>
                <div>
                    <p class="text-sm font-medium">Severity Score:</p>
                    <p class="text-lg font-mono">${severityBars} ${severityScore}/10</p>
                </div>
            </div>
            ${assessment.symptoms ? `
                <div>
                    <p class="text-sm font-medium">Identified Symptoms:</p>
                    <p class="text-sm">${assessment.symptoms.join(', ')}</p>
                </div>
            ` : ''}
            <div>
                <p class="text-sm font-medium">Recommended Action:</p>
                <p class="font-medium">${assessment.recommended_action || 'Please consult your healthcare provider'}</p>
            </div>
            <div>
                <p class="text-sm font-medium">Clinical Reasoning:</p>
                <p class="text-sm">${assessment.reasoning || 'Assessment completed'}</p>
            </div>
            ${assessment.escalation_required ? `
                <div class="mt-4 p-3 bg-yellow-100 border border-yellow-400 rounded-lg">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    <strong>Follow-up Required:</strong> Please schedule an appointment for further evaluation.
                </div>
            ` : ''}
        </div>
        ${urgency === 'emergency' ? `
            <div class="mt-4 p-3 bg-red-600 text-white rounded-lg emergency-alert">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                <strong>EMERGENCY DETECTED:</strong> Immediate medical attention required!
                <button onclick="call911()" class="ml-4 bg-white text-red-600 px-3 py-1 rounded font-bold">
                    Call 911
                </button>
            </div>
        ` : ''}
    `;
    container.classList.remove('hidden');
}

function showEmergencyAlert(assessment) {
    showMessage(`🚨 EMERGENCY: ${assessment.recommended_action}`, 'error');
    
    // Optional: Auto-show emergency modal for critical cases
    if (assessment.severity_score >= 9) {
        setTimeout(() => {
            document.getElementById('emergencyModal').classList.remove('hidden');
        }, 1000);
    }
}

// Chat Functionality
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    const chatMessages = document.getElementById('chatMessages');
    
    // Add user message
    addChatMessage(message, 'user');
    input.value = '';
    
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: document.getElementById('patientId').value,
                message: message,
                conversation_context: {}
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        addChatMessage(data.response, 'assistant', data.agent_used);
        
    } catch (error) {
        console.error('Chat error:', error);
        addChatMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    }
}

function addChatMessage(message, sender, agentType = null) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'flex ' + (sender === 'user' ? 'justify-end' : 'justify-start');
    
    const messageContent = document.createElement('div');
    const baseClasses = 'p-3 rounded-lg max-w-xs relative';
    
    if (sender === 'user') {
        messageContent.className = `${baseClasses} bg-blue-500 text-white`;
    } else {
        messageContent.className = `${baseClasses} bg-gray-200 text-gray-800`;
    }
    
    let agentBadge = '';
    if (agentType && sender === 'assistant') {
        const agentColors = {
            'triage': 'bg-red-500',
            'appointment': 'bg-orange-500', 
            'virtual_assistant': 'bg-green-500',
            'clinical_docs': 'bg-purple-500',
            'supervisor': 'bg-blue-500'
        };
        const color = agentColors[agentType] || 'bg-gray-500';
        agentBadge = `<span class="${color} text-white text-xs px-2 py-1 rounded-full absolute -top-2 -left-2">${agentType.replace('_', ' ')}</span>`;
    }
    
    messageContent.innerHTML = agentBadge + message;
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Patient Data Loading
async function loadPatientData() {
    const patientId = document.getElementById('patientId').value;
    
    try {
        const response = await fetch(`${API_BASE}/patient/${patientId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        document.getElementById('patientInfo').innerHTML = `
            <div class="space-y-3">
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">Name:</span>
                    <span class="font-medium">${data.name}</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">Age:</span>
                    <span class="font-medium">${data.age}</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">ID:</span>
                    <span class="font-medium">${data.patient_id}</span>
                </div>
                <div>
                    <span class="text-gray-600">Conditions:</span>
                    <div class="mt-1">
                        ${data.conditions.map(condition => 
                            `<span class="inline-block bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full mr-1 mb-1">${condition}</span>`
                        ).join('')}
                    </div>
                </div>
                <div>
                    <span class="text-gray-600">Medications:</span>
                    <div class="mt-1">
                        ${data.medications.map(med => 
                            `<span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full mr-1 mb-1">${med}</span>`
                        ).join('')}
                    </div>
                </div>
                <div>
                    <span class="text-gray-600">Risk Factors:</span>
                    <div class="mt-1">
                        ${data.risk_factors.map(factor => 
                            `<span class="inline-block bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full mr-1 mb-1">${factor}</span>`
                        ).join('')}
                    </div>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-gray-600">Last Visit:</span>
                    <span class="font-medium">${data.last_visit || 'N/A'}</span>
                </div>
                <button onclick="loadPatientData()" class="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 px-4 rounded-lg mt-4 transition-colors">
                    <i class="fas fa-refresh mr-2"></i>Refresh Patient Data
                </button>
            </div>
        `;
        
    } catch (error) {
        console.error('Error loading patient data:', error);
        showMessage('Error loading patient data', 'error');
    }
}

// Appointment Booking
async function bookAppointment() {
    const patientId = document.getElementById('patientId').value;
    const appointmentType = document.getElementById('appointmentType').value;
    const appointmentDate = document.getElementById('appointmentDate').value;
    const notes = document.getElementById('appointmentNotes').value;
    
    if (!appointmentDate) {
        showMessage('Please select a date for the appointment', 'error');
        return;
    }
    
    try {
        showLoading();
        
        const message = `I need to schedule a ${appointmentType} appointment for ${appointmentDate}. ${notes ? 'Additional notes: ' + notes : ''}`;
        
        const response = await fetch(`${API_BASE}/appointment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                message: message,
                conversation_context: {}
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        hideLoading();
        
        showMessage('Appointment request processed successfully!', 'success');
        
        // Show appointment details in a modal or message
        showAppointmentConfirmation(data);
        
        // Clear form
        document.getElementById('appointmentNotes').value = '';
        
    } catch (error) {
        console.error('Error booking appointment:', error);
        hideLoading();
        showMessage('Error booking appointment. Please try again.', 'error');
    }
}

function showAppointmentConfirmation(data) {
    const modal = document.getElementById('reportModal');
    const content = document.getElementById('reportContent');
    
    content.innerHTML = `
        <div class="text-center mb-6">
            <i class="fas fa-calendar-check text-6xl text-green-600 mb-4"></i>
            <h3 class="text-2xl font-bold text-gray-800">Appointment Scheduled</h3>
        </div>
        <div class="bg-gray-50 p-4 rounded-lg">
            <p class="font-medium mb-2">Appointment Details:</p>
            <div class="text-sm space-y-1">
                ${data.response}
            </div>
        </div>
    `;
    
    modal.classList.remove('hidden');
}

// Quick Actions
async function generateReport() {
    const patientId = document.getElementById('patientId').value;
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                message: "Generate a comprehensive clinical summary report for this patient including medical history, current conditions, medications, and recent assessments",
                conversation_context: { agent_type: "clinical_docs" }
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        hideLoading();
        
        showReportModal(data.response, 'Clinical Report');
        
    } catch (error) {
        console.error('Error generating report:', error);
        hideLoading();
        showMessage('Error generating report. Please try again.', 'error');
    }
}

async function checkMedications() {
    const patientId = document.getElementById('patientId').value;
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                patient_id: patientId,
                message: "Review my current medications and check for any interactions, side effects, or important information I should know",
                conversation_context: {}
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        hideLoading();
        
        addChatMessage("Medication Review: " + data.response, 'assistant', data.agent_used);
        showMessage('Medication review completed - check chat for details', 'success');
        
    } catch (error) {
        console.error('Error checking medications:', error);
        hideLoading();
        showMessage('Error checking medications. Please try again.', 'error');
    }
}

async function viewHistory() {
    const patientId = document.getElementById('patientId').value;
    
    try {
        showLoading();
        
        // Get patient data for medical history
        const patientResponse = await fetch(`${API_BASE}/patient/${patientId}`);
        const patientData = await patientResponse.json();
        
        hideLoading();
        
        let historyHtml = `
            <div class="space-y-4">
                <h3 class="text-xl font-bold mb-4">Medical History for ${patientData.name}</h3>
                
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-semibold mb-2">Current Conditions:</h4>
                    <ul class="list-disc list-inside space-y-1">
                        ${patientData.conditions.map(condition => `<li>${condition}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-semibold mb-2">Current Medications:</h4>
                    <ul class="list-disc list-inside space-y-1">
                        ${patientData.medications.map(med => `<li>${med}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-semibold mb-2">Risk Factors:</h4>
                    <ul class="list-disc list-inside space-y-1">
                        ${patientData.risk_factors.map(factor => `<li>${factor}</li>`).join('')}
                    </ul>
                </div>
                
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h4 class="font-semibold mb-2">Last Visit:</h4>
                    <p>${patientData.last_visit || 'No previous visits recorded'}</p>
                </div>
            </div>
        `;
        
        showReportModal(historyHtml, 'Medical History');
        
    } catch (error) {
        console.error('Error loading medical history:', error);
        hideLoading();
        showMessage('Error loading medical history. Please try again.', 'error');
    }
}

async function viewAppointments() {
    const patientId = document.getElementById('patientId').value;
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE}/patient/${patientId}/appointments`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        hideLoading();
        
        let appointmentsHtml = `
            <div class="space-y-4">
                <h3 class="text-xl font-bold mb-4">Appointments for Patient ${patientId}</h3>
        `;
        
        if (data.appointments && data.appointments.length > 0) {
            appointmentsHtml += `
                <div class="space-y-3">
                    ${data.appointments.map(apt => `
                        <div class="bg-gray-50 p-4 rounded-lg border-l-4 border-blue-500">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h4 class="font-semibold">${apt.type || 'Appointment'}</h4>
                                    <p class="text-sm text-gray-600">${apt.date} at ${apt.time}</p>
                                    ${apt.notes ? `<p class="text-sm mt-1">${apt.notes}</p>` : ''}
                                </div>
                                <span class="px-2 py-1 text-xs font-semibold rounded-full ${apt.status === 'confirmed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                                    ${apt.status || 'Pending'}
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            appointmentsHtml += `
                <div class="text-center py-8">
                    <i class="fas fa-calendar text-4xl text-gray-400 mb-4"></i>
                    <p class="text-gray-600">No appointments scheduled</p>
                </div>
            `;
        }
        
        appointmentsHtml += '</div>';
        
        showReportModal(appointmentsHtml, 'Appointments');
        
    } catch (error) {
        console.error('Error loading appointments:', error);
        hideLoading();
        showMessage('Error loading appointments. Please try again.', 'error');
    }
}

// Modal Functions
function showReportModal(content, title = 'Report') {
    const modal = document.getElementById('reportModal');
    const reportContent = document.getElementById('reportContent');
    
    modal.querySelector('h2').textContent = title;
    reportContent.innerHTML = content;
    modal.classList.remove('hidden');
    modal.classList.add('modal-enter');
}

function closeReportModal() {
    document.getElementById('reportModal').classList.add('hidden');
}

function downloadReport() {
    const content = document.getElementById('reportContent').innerText;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cardiology-report-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Emergency Functions
function showEmergencyModal() {
    document.getElementById('emergencyModal').classList.remove('hidden');
}

function closeEmergencyModal() {
    document.getElementById('emergencyModal').classList.add('hidden');
}

function call911() {
    // In a real application, this might interface with emergency services
    showMessage('🚨 Emergency services contacted. Please wait for assistance.', 'error');
    closeEmergencyModal();
    
    // Log emergency event
    console.log('Emergency call initiated at:', new Date().toISOString());
}

// System Status Functions
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const statusElement = document.getElementById('systemStatus');
        
        if (response.ok) {
            statusElement.textContent = 'System Online';
            statusElement.className = 'bg-green-500 px-3 py-1 rounded-full text-sm';
        } else {
            throw new Error('Health check failed');
        }
    } catch (error) {
        const statusElement = document.getElementById('systemStatus');
        statusElement.textContent = 'System Offline';
        statusElement.className = 'bg-red-500 px-3 py-1 rounded-full text-sm';
    }
}

// Event Listeners and Initialization
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    document.getElementById('emergencyBtn').addEventListener('click', showEmergencyModal);
    
    // Auto-load patient data on page load
    loadPatientData();
    
    // Set default date for appointments (tomorrow)
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('appointmentDate').value = tomorrow.toISOString().split('T')[0];
    
    // Update patient info when patient selection changes
    document.getElementById('patientId').addEventListener('change', loadPatientData);
    
    // Check system health periodically
    checkSystemHealth();
    setInterval(checkSystemHealth, 30000); // Check every 30 seconds
    
    // Initialize chat with welcome message
    setTimeout(() => {
        addChatMessage('I can help you with medication questions, symptom information, and general health education. What would you like to know?', 'assistant', 'virtual_assistant');
    }, 1000);
});