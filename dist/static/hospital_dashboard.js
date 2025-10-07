// Hospital Dashboard JavaScript
const API_BASE = window.location.origin;

// Update dashboard stats
function updateStats() {
    // Simulate real-time updates
    const stats = {
        totalPatients: Math.floor(Math.random() * 100) + 1200,
        emergencyCases: Math.floor(Math.random() * 5) + 5,
        todayAppointments: Math.floor(Math.random() * 50) + 120,
        activeDoctors: Math.floor(Math.random() * 5) + 20,
        triageCount: Math.floor(Math.random() * 20) + 70
    };
    
    document.getElementById('totalPatients').textContent = stats.totalPatients.toLocaleString();
    document.getElementById('emergencyCases').textContent = stats.emergencyCases;
    document.getElementById('todayAppointments').textContent = stats.todayAppointments;
    document.getElementById('activeDoctors').textContent = stats.activeDoctors;
    document.getElementById('triageCount').textContent = stats.triageCount;
}

// Check system health
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
            document.getElementById('systemStatus').textContent = 'System Online';
            document.getElementById('systemStatus').className = 'bg-green-500 text-white px-3 py-1 rounded-full text-sm';
        }
    } catch (error) {
        document.getElementById('systemStatus').textContent = 'System Offline';
        document.getElementById('systemStatus').className = 'bg-red-500 text-white px-3 py-1 rounded-full text-sm';
    }
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    updateStats();
    checkSystemHealth();
    
    // Update stats every 30 seconds
    setInterval(updateStats, 30000);
    setInterval(checkSystemHealth, 60000);
});