from typing import Dict, List
from datetime import datetime, timedelta

class AppointmentSystemTool:
    """Tool for managing appointments"""
    
    def __init__(self):
        self.name = "appointment_system"
        self.description = "Manage appointment scheduling, availability, and booking"
        
        # Mock appointment storage - in production, this would be a database
        self.appointments = {}
        self.availability = self._generate_mock_availability()
    
    def _generate_mock_availability(self) -> Dict:
        """Generate mock availability data"""
        availability = {}
        
        # Generate availability for next 30 days
        for i in range(30):
            date = (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            # Skip weekends
            if datetime.strptime(date, '%Y-%m-%d').weekday() < 5:
                availability[date] = {
                    'slots': [
                        '09:00', '09:30', '10:00', '10:30',
                        '11:00', '11:30', '14:00', '14:30',
                        '15:00', '15:30', '16:00', '16:30'
                    ],
                    'emergency_slots': ['08:00', '17:00']
                }
        
        return availability
    
    def check_availability(self, date: str, appointment_type: str = 'routine') -> Dict:
        """Check appointment availability for a date"""
        if date not in self.availability:
            return {'available': False, 'slots': []}
        
        day_availability = self.availability[date]
        available_slots = day_availability['slots'].copy()
        
        # Add emergency slots if it's an urgent appointment
        if appointment_type in ['emergency', 'urgent']:
            available_slots.extend(day_availability['emergency_slots'])
        
        # Remove already booked slots
        booked_slots = [apt['time'] for apt in self.appointments.get(date, [])]
        available_slots = [slot for slot in available_slots if slot not in booked_slots]
        
        return {
            'available': len(available_slots) > 0,
            'slots': available_slots,
            'date': date
        }
    
    def book_appointment(self, patient_id: str, date: str, time: str, 
                        appointment_type: str, notes: str = "") -> Dict:
        """Book an appointment"""
        
        # Check if slot is available
        availability = self.check_availability(date, appointment_type)
        if not availability['available'] or time not in availability['slots']:
            return {
                'success': False,
                'message': 'Requested time slot is not available',
                'alternative_slots': availability['slots'][:3]
            }
        
        # Create appointment
        appointment_id = f"CARD-{date.replace('-', '')}-{time.replace(':', '')}-{patient_id}"
        appointment = {
            'appointment_id': appointment_id,
            'patient_id': patient_id,
            'date': date,
            'time': time,
            'type': appointment_type,
            'notes': notes,
            'status': 'confirmed',
            'created_at': datetime.now().isoformat()
        }
        
        # Store appointment
        if date not in self.appointments:
            self.appointments[date] = []
        self.appointments[date].append(appointment)
        
        return {
            'success': True,
            'appointment_id': appointment_id,
            'appointment': appointment,
            'message': f'Appointment confirmed for {date} at {time}'
        }
    
    def get_patient_appointments(self, patient_id: str) -> List[Dict]:
        """Get all appointments for a patient"""
        patient_appointments = []
        
        for date, appointments in self.appointments.items():
            for appointment in appointments:
                if appointment['patient_id'] == patient_id:
                    patient_appointments.append(appointment)
        
        return sorted(patient_appointments, key=lambda x: f"{x['date']} {x['time']}")
    
    def cancel_appointment(self, appointment_id: str) -> Dict:
        """Cancel an appointment"""
        for date, appointments in self.appointments.items():
            for i, appointment in enumerate(appointments):
                if appointment['appointment_id'] == appointment_id:
                    cancelled_appointment = appointments.pop(i)
                    return {
                        'success': True,
                        'message': 'Appointment cancelled successfully',
                        'cancelled_appointment': cancelled_appointment
                    }
        
        return {
            'success': False,
            'message': 'Appointment not found'
        }
    
    def reschedule_appointment(self, appointment_id: str, new_date: str, new_time: str) -> Dict:
        """Reschedule an existing appointment"""
        
        # Find existing appointment
        existing_appointment = None
        for date, appointments in self.appointments.items():
            for appointment in appointments:
                if appointment['appointment_id'] == appointment_id:
                    existing_appointment = appointment
                    break
        
        if not existing_appointment:
            return {'success': False, 'message': 'Appointment not found'}
        
        # Cancel existing appointment
        cancel_result = self.cancel_appointment(appointment_id)
        if not cancel_result['success']:
            return cancel_result
        
        # Book new appointment
        return self.book_appointment(
            existing_appointment['patient_id'],
            new_date,
            new_time,
            existing_appointment['type'],
            existing_appointment['notes']
        )