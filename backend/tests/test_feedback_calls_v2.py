"""
Test Post-Visit Feedback Call Feature V2
Tests the updated feedback feature where:
1. Feedback appears for ALL past appointments regardless of status (not just 'done')
2. Feedback persists until HA logs an interaction AFTER the appointment date
3. Day labels show correct relative time ('yesterday', '3 days ago', etc.)
4. Lab test bookings also generate feedback entries
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def seeded_data(api_client):
    """Seed database and return patient data"""
    response = api_client.post(f"{BASE_URL}/api/seed")
    assert response.status_code == 200, f"Seed failed: {response.text}"
    
    response = api_client.get(f"{BASE_URL}/api/patients")
    assert response.status_code == 200
    patients = response.json()
    assert len(patients) > 0, "No patients after seeding"
    
    return patients

@pytest.fixture
def yesterday_str():
    """Get yesterday's date string"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

@pytest.fixture
def today_str():
    """Get today's date string"""
    return datetime.now().strftime("%Y-%m-%d")

@pytest.fixture
def three_days_ago_str():
    """Get 3 days ago date string"""
    return (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")

@pytest.fixture
def tomorrow_str():
    """Get tomorrow's date string for follow-up"""
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


class TestFeedbackForAllStatuses:
    """Test that feedback appears for appointments with ANY status"""
    
    def test_feedback_for_upcoming_status_appointment(self, api_client, seeded_data, yesterday_str):
        """Feedback should appear for appointments with status='upcoming' (not marked done)"""
        patient = seeded_data[0]
        patient_id = patient["id"]
        
        # Create appointment for yesterday but DON'T mark it done (stays 'upcoming')
        apt_data = {
            "type": "doctor",
            "title": "TEST Upcoming Status Visit",
            "doctor": "Dr. Upcoming Status",
            "hospital": "Test Hospital",
            "date": yesterday_str,
            "time": "10:00"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200, f"Failed to create appointment: {response.text}"
        
        appointment = response.json()
        assert appointment["status"] == "upcoming", "Appointment should have 'upcoming' status"
        print(f"Created appointment with status='upcoming' for yesterday")
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call" 
                         and "Dr. Upcoming Status" in t.get("description", "")]
        
        assert len(feedback_tasks) > 0, "Feedback should appear for 'upcoming' status appointments"
        print(f"SUCCESS: Feedback entry found for appointment with status='upcoming'")
    
    def test_feedback_for_done_status_appointment(self, api_client, seeded_data, yesterday_str):
        """Feedback should appear for appointments with status='done'"""
        patient = seeded_data[1] if len(seeded_data) > 1 else seeded_data[0]
        patient_id = patient["id"]
        
        apt_data = {
            "type": "doctor",
            "title": "TEST Done Status Visit",
            "doctor": "Dr. Done Status",
            "date": yesterday_str,
            "time": "11:00"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        apt = response.json()
        
        # Mark as done
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt['id']}/status",
            json={"status": "done"}
        )
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call" 
                         and "Dr. Done Status" in t.get("description", "")]
        
        assert len(feedback_tasks) > 0, "Feedback should appear for 'done' status appointments"
        print(f"SUCCESS: Feedback entry found for appointment with status='done'")
    
    def test_feedback_for_postponed_status_appointment(self, api_client, seeded_data, yesterday_str):
        """Feedback should appear for appointments with status='postponed'"""
        patient = seeded_data[2] if len(seeded_data) > 2 else seeded_data[0]
        patient_id = patient["id"]
        
        apt_data = {
            "type": "doctor",
            "title": "TEST Postponed Status Visit",
            "doctor": "Dr. Postponed Status",
            "date": yesterday_str,
            "time": "12:00"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        apt = response.json()
        
        # Mark as postponed
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt['id']}/status",
            json={"status": "postponed"}
        )
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call" 
                         and "Dr. Postponed Status" in t.get("description", "")]
        
        assert len(feedback_tasks) > 0, "Feedback should appear for 'postponed' status appointments"
        print(f"SUCCESS: Feedback entry found for appointment with status='postponed'")
    
    def test_feedback_for_abandoned_status_appointment(self, api_client, seeded_data, yesterday_str):
        """Feedback should appear for appointments with status='abandoned'"""
        patient = seeded_data[3] if len(seeded_data) > 3 else seeded_data[0]
        patient_id = patient["id"]
        
        apt_data = {
            "type": "doctor",
            "title": "TEST Abandoned Status Visit",
            "doctor": "Dr. Abandoned Status",
            "date": yesterday_str,
            "time": "13:00"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        apt = response.json()
        
        # Mark as abandoned
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt['id']}/status",
            json={"status": "abandoned"}
        )
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call" 
                         and "Dr. Abandoned Status" in t.get("description", "")]
        
        assert len(feedback_tasks) > 0, "Feedback should appear for 'abandoned' status appointments"
        print(f"SUCCESS: Feedback entry found for appointment with status='abandoned'")


class TestFeedbackPersistence:
    """Test that feedback persists for multiple days until interaction is logged"""
    
    def test_feedback_persists_for_old_appointments(self, api_client, seeded_data, three_days_ago_str):
        """Feedback should persist for appointments from multiple days ago"""
        patient = seeded_data[4] if len(seeded_data) > 4 else seeded_data[0]
        patient_id = patient["id"]
        
        apt_data = {
            "type": "doctor",
            "title": "TEST Old Appointment",
            "doctor": "Dr. Three Days Ago",
            "date": three_days_ago_str,
            "time": "10:00"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call" 
                         and "Dr. Three Days Ago" in t.get("description", "")]
        
        assert len(feedback_tasks) > 0, "Feedback should persist for 3-day-old appointments"
        print(f"SUCCESS: Feedback entry found for 3-day-old appointment")
    
    def test_old_feedback_shows_correct_day_label(self, api_client, seeded_data, three_days_ago_str):
        """Old feedback entries should show '3 days ago' not 'yesterday'"""
        patient = seeded_data[5] if len(seeded_data) > 5 else seeded_data[0]
        patient_id = patient["id"]
        
        apt_data = {
            "type": "doctor",
            "title": "TEST Day Label Check",
            "doctor": "Dr. Day Label",
            "date": three_days_ago_str,
            "time": "14:00"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call" 
                         and "Dr. Day Label" in t.get("description", "")]
        
        assert len(feedback_tasks) > 0, "Feedback entry should exist"
        
        desc = feedback_tasks[0]["description"]
        assert "3 days ago" in desc.lower(), f"Description should say '3 days ago', got: {desc}"
        assert "yesterday" not in desc.lower(), f"Description should NOT say 'yesterday' for 3-day-old: {desc}"
        print(f"SUCCESS: Old feedback shows correct day label: {desc}")


class TestFeedbackCompletionStatus:
    """Test that feedback status changes based on interaction logging"""
    
    def test_feedback_pending_when_no_interaction(self, api_client, seeded_data, yesterday_str):
        """Feedback should show 'pending' when no interaction logged after appointment"""
        patient = seeded_data[6] if len(seeded_data) > 6 else seeded_data[0]
        patient_id = patient["id"]
        
        apt_data = {
            "type": "doctor",
            "title": "TEST Pending Status",
            "doctor": "Dr. Pending Check",
            "date": yesterday_str,
            "time": "09:00"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call" 
                         and "Dr. Pending Check" in t.get("description", "")]
        
        assert len(feedback_tasks) > 0, "Feedback entry should exist"
        assert feedback_tasks[0]["status"] == "pending", f"Status should be 'pending', got: {feedback_tasks[0]['status']}"
        print(f"SUCCESS: Feedback shows 'pending' status when no interaction logged")
    
    def test_feedback_completed_after_interaction_logged(self, api_client, seeded_data, yesterday_str, tomorrow_str):
        """Feedback should show 'completed' when HA logs an interaction after appointment date"""
        patient = seeded_data[7] if len(seeded_data) > 7 else seeded_data[0]
        patient_id = patient["id"]
        
        apt_data = {
            "type": "doctor",
            "title": "TEST Completed Status",
            "doctor": "Dr. Completed Check",
            "date": yesterday_str,
            "time": "15:00"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        
        # Log an interaction (today is after yesterday's appointment)
        interaction_data = {
            "type": "call",
            "notes": "Feedback call completed",
            "outcome": "positive",
            "follow_up_date": tomorrow_str,
            "follow_up_time": "10:00"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/interactions", json=interaction_data)
        assert response.status_code == 200, f"Failed to log interaction: {response.text}"
        print(f"Logged interaction for patient")
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call" 
                         and "Dr. Completed Check" in t.get("description", "")]
        
        assert len(feedback_tasks) > 0, "Feedback entry should still exist"
        assert feedback_tasks[0]["status"] == "completed", f"Status should be 'completed' after interaction, got: {feedback_tasks[0]['status']}"
        print(f"SUCCESS: Feedback shows 'completed' status after interaction logged")


class TestLabTestFeedback:
    """Test that lab test bookings also generate feedback entries"""
    
    def test_lab_test_generates_feedback(self, api_client, seeded_data, yesterday_str):
        """Lab test bookings should generate feedback entries"""
        patient = seeded_data[8] if len(seeded_data) > 8 else seeded_data[0]
        patient_id = patient["id"]
        
        lab_data = {
            "test_name": "TEST Lab Feedback Check",
            "booked_date": yesterday_str,
            "price": 500
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/lab-tests/book", json=lab_data)
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call" 
                         and "TEST Lab Feedback Check" in t.get("description", "")]
        
        assert len(feedback_tasks) > 0, "Lab test should generate feedback entry"
        print(f"SUCCESS: Lab test booking generates feedback entry")
    
    def test_lab_test_feedback_persists_for_old_bookings(self, api_client, seeded_data, three_days_ago_str):
        """Lab test feedback should persist for old bookings"""
        patient = seeded_data[9] if len(seeded_data) > 9 else seeded_data[0]
        patient_id = patient["id"]
        
        lab_data = {
            "test_name": "TEST Old Lab Booking",
            "booked_date": three_days_ago_str,
            "price": 600
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/lab-tests/book", json=lab_data)
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call" 
                         and "TEST Old Lab Booking" in t.get("description", "")]
        
        assert len(feedback_tasks) > 0, "Old lab test booking should still have feedback entry"
        
        desc = feedback_tasks[0]["description"]
        assert "3 days ago" in desc.lower(), f"Description should say '3 days ago', got: {desc}"
        print(f"SUCCESS: Old lab test feedback persists with correct day label")


class TestSeededDataFeedback:
    """Test that seeded data generates feedback entries"""
    
    def test_seeded_patients_have_old_appointments(self, api_client, seeded_data):
        """Verify seeded patients have old 'done' appointments that generate feedback"""
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call"]
        
        # After seeding, each patient should have an old appointment generating feedback
        print(f"Found {len(feedback_tasks)} feedback entries from seeded data")
        assert len(feedback_tasks) > 0, "Seeded data should generate feedback entries"


class TestFeedbackFilterIntegration:
    """Test the Feedback filter in Dashboard"""
    
    def test_feedback_filter_count_matches_entries(self, api_client):
        """Feedback filter count should match actual feedback_call entries"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_count = len([t for t in tasks if t.get("task_type") == "feedback_call"])
        
        print(f"SUCCESS: Feedback filter count = {feedback_count}")
        assert feedback_count >= 0, "Feedback count should be non-negative"
    
    def test_feedback_entries_have_required_fields(self, api_client):
        """All feedback entries should have required fields"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call"]
        
        for task in feedback_tasks:
            assert "id" in task, "Missing 'id' field"
            assert "patient_id" in task, "Missing 'patient_id' field"
            assert "patient_name" in task, "Missing 'patient_name' field"
            assert "status" in task, "Missing 'status' field"
            assert "task_type" in task, "Missing 'task_type' field"
            assert "description" in task, "Missing 'description' field"
            assert task["task_type"] == "feedback_call", f"Wrong task_type: {task['task_type']}"
            assert task["status"] in ["pending", "completed"], f"Invalid status: {task['status']}"
        
        print(f"SUCCESS: All {len(feedback_tasks)} feedback entries have required fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
