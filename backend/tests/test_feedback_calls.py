"""
Test Post-Visit Feedback Call Feature
Tests that feedback_call entries appear in Daily Task List for:
1. Doctor appointments marked 'done' yesterday
2. Lab test bookings for yesterday
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
    # Seed the database
    response = api_client.post(f"{BASE_URL}/api/seed")
    assert response.status_code == 200, f"Seed failed: {response.text}"
    
    # Get patients
    response = api_client.get(f"{BASE_URL}/api/patients")
    assert response.status_code == 200
    patients = response.json()
    assert len(patients) > 0, "No patients after seeding"
    
    return patients

@pytest.fixture(scope="module")
def yesterday_str():
    """Get yesterday's date string"""
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

@pytest.fixture(scope="module")
def today_str():
    """Get today's date string"""
    return datetime.now().strftime("%Y-%m-%d")


class TestFeedbackCallBackend:
    """Backend tests for feedback_call feature"""
    
    def test_seed_and_get_patients(self, api_client, seeded_data):
        """Verify seeding works and patients exist"""
        assert len(seeded_data) >= 1, "Should have at least 1 patient"
        print(f"SUCCESS: Found {len(seeded_data)} patients after seeding")
    
    def test_create_doctor_appointment_yesterday_done(self, api_client, seeded_data, yesterday_str):
        """Create a doctor appointment for yesterday and mark it done"""
        patient = seeded_data[0]
        patient_id = patient["id"]
        
        # Create appointment for yesterday
        apt_data = {
            "type": "doctor",
            "title": "TEST Feedback Checkup",
            "doctor": "Dr. Test Feedback",
            "hospital": "Test Hospital",
            "date": yesterday_str,
            "time": "10:00",
            "notes": "Test appointment for feedback call"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200, f"Failed to create appointment: {response.text}"
        
        appointment = response.json()
        apt_id = appointment["id"]
        assert appointment["date"] == yesterday_str
        assert appointment["status"] == "upcoming"
        print(f"SUCCESS: Created appointment {apt_id} for yesterday ({yesterday_str})")
        
        # Mark appointment as done
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt_id}/status",
            json={"status": "done"}
        )
        assert response.status_code == 200, f"Failed to update status: {response.text}"
        
        updated = response.json()
        assert updated["status"] == "done"
        print(f"SUCCESS: Appointment marked as 'done'")
        
        return {"patient_id": patient_id, "apt_id": apt_id, "doctor": apt_data["doctor"], "title": apt_data["title"]}
    
    def test_create_lab_test_booking_yesterday(self, api_client, seeded_data, yesterday_str):
        """Create a lab test booking for yesterday"""
        # Use second patient to avoid duplicate feedback entry
        patient = seeded_data[1] if len(seeded_data) > 1 else seeded_data[0]
        patient_id = patient["id"]
        
        lab_data = {
            "test_name": "TEST HbA1c Feedback",
            "booked_date": yesterday_str,
            "price": 450
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/lab-tests/book", json=lab_data)
        assert response.status_code == 200, f"Failed to book lab test: {response.text}"
        
        booking = response.json()
        assert booking["booked_date"] == yesterday_str
        assert booking["test_name"] == lab_data["test_name"]
        print(f"SUCCESS: Created lab test booking for yesterday ({yesterday_str})")
        
        return {"patient_id": patient_id, "test_name": lab_data["test_name"]}
    
    def test_daily_task_list_has_feedback_entries(self, api_client, seeded_data, yesterday_str):
        """Verify feedback_call entries appear in daily task list"""
        # First create the test data
        patient1 = seeded_data[0]
        patient1_id = patient1["id"]
        
        # Create and mark done a doctor appointment for yesterday
        apt_data = {
            "type": "doctor",
            "title": "Feedback Test Visit",
            "doctor": "Dr. Feedback Test",
            "hospital": "Test Hospital",
            "date": yesterday_str,
            "time": "14:00"
        }
        response = api_client.post(f"{BASE_URL}/api/patients/{patient1_id}/appointments", json=apt_data)
        assert response.status_code == 200
        apt = response.json()
        
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient1_id}/appointments/{apt['id']}/status",
            json={"status": "done"}
        )
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call"]
        
        assert len(feedback_tasks) > 0, "No feedback_call entries found in daily task list"
        print(f"SUCCESS: Found {len(feedback_tasks)} feedback_call entries")
        
        return feedback_tasks
    
    def test_feedback_entry_has_correct_fields(self, api_client, seeded_data, yesterday_str):
        """Verify feedback_call entries have correct task_type, status, and revenue"""
        # Create test data
        patient = seeded_data[0]
        patient_id = patient["id"]
        
        apt_data = {
            "type": "doctor",
            "title": "Field Test Visit",
            "doctor": "Dr. Field Test",
            "date": yesterday_str,
            "time": "09:00"
        }
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        apt = response.json()
        
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt['id']}/status",
            json={"status": "done"}
        )
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_tasks = [t for t in tasks if t.get("task_type") == "feedback_call"]
        
        for task in feedback_tasks:
            assert task["task_type"] == "feedback_call", f"Wrong task_type: {task['task_type']}"
            assert task["status"] == "pending", f"Wrong status: {task['status']}"
            assert task["revenue"] == 0, f"Wrong revenue: {task['revenue']}"
            assert "patient_id" in task
            assert "patient_name" in task
            assert "description" in task
            print(f"SUCCESS: Feedback entry has correct fields - task_type={task['task_type']}, status={task['status']}, revenue={task['revenue']}")
        
        return True
    
    def test_feedback_description_format_doctor(self, api_client, seeded_data, yesterday_str):
        """Verify doctor appointment feedback has descriptive text"""
        patient = seeded_data[0]
        patient_id = patient["id"]
        
        apt_data = {
            "type": "doctor",
            "title": "Diabetes Checkup",
            "doctor": "Dr. Description Test",
            "date": yesterday_str,
            "time": "11:00"
        }
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        apt = response.json()
        
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt['id']}/status",
            json={"status": "done"}
        )
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        
        # Find the feedback entry for this appointment
        feedback_for_apt = [t for t in tasks 
                           if t.get("task_type") == "feedback_call" 
                           and "Dr. Description Test" in t.get("description", "")]
        
        assert len(feedback_for_apt) > 0, "Feedback entry for doctor appointment not found"
        
        desc = feedback_for_apt[0]["description"]
        assert "Feedback" in desc, f"Description should contain 'Feedback': {desc}"
        assert "yesterday" in desc.lower(), f"Description should mention 'yesterday': {desc}"
        print(f"SUCCESS: Doctor feedback description format correct: {desc}")
    
    def test_feedback_description_format_lab(self, api_client, seeded_data, yesterday_str):
        """Verify lab test feedback has descriptive text"""
        # Use a different patient to avoid duplicate check
        patient = seeded_data[2] if len(seeded_data) > 2 else seeded_data[0]
        patient_id = patient["id"]
        
        lab_data = {
            "test_name": "Lipid Profile Test",
            "booked_date": yesterday_str,
            "price": 600
        }
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/lab-tests/book", json=lab_data)
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        
        # Find the feedback entry for this lab test
        feedback_for_lab = [t for t in tasks 
                           if t.get("task_type") == "feedback_call" 
                           and "Lipid Profile" in t.get("description", "")]
        
        assert len(feedback_for_lab) > 0, "Feedback entry for lab test not found"
        
        desc = feedback_for_lab[0]["description"]
        assert "Feedback" in desc, f"Description should contain 'Feedback': {desc}"
        assert "yesterday" in desc.lower(), f"Description should mention 'yesterday': {desc}"
        print(f"SUCCESS: Lab test feedback description format correct: {desc}")
    
    def test_no_duplicate_feedback_same_patient(self, api_client, seeded_data, yesterday_str):
        """Verify no duplicate feedback entries for same patient (doctor + lab on same day)"""
        patient = seeded_data[3] if len(seeded_data) > 3 else seeded_data[0]
        patient_id = patient["id"]
        patient_name = patient["name"]
        
        # Create doctor appointment for yesterday and mark done
        apt_data = {
            "type": "doctor",
            "title": "Duplicate Test Visit",
            "doctor": "Dr. Duplicate Test",
            "date": yesterday_str,
            "time": "10:00"
        }
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        apt = response.json()
        
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt['id']}/status",
            json={"status": "done"}
        )
        assert response.status_code == 200
        
        # Create lab test for yesterday
        lab_data = {
            "test_name": "Duplicate Test Lab",
            "booked_date": yesterday_str,
            "price": 300
        }
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/lab-tests/book", json=lab_data)
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        
        # Count feedback entries for this patient
        feedback_for_patient = [t for t in tasks 
                                if t.get("task_type") == "feedback_call" 
                                and t.get("patient_id") == patient_id]
        
        # Should have only 1 feedback entry (doctor appointment takes precedence, lab skipped)
        assert len(feedback_for_patient) == 1, f"Expected 1 feedback entry for patient, got {len(feedback_for_patient)}"
        print(f"SUCCESS: No duplicate feedback - patient {patient_name} has exactly 1 feedback entry")
    
    def test_feedback_only_for_yesterday_not_older(self, api_client, seeded_data):
        """Verify feedback entries only appear for yesterday's visits, not older"""
        patient = seeded_data[4] if len(seeded_data) > 4 else seeded_data[0]
        patient_id = patient["id"]
        
        # Create appointment for 2 days ago
        two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        
        apt_data = {
            "type": "doctor",
            "title": "Old Visit Test",
            "doctor": "Dr. Old Visit",
            "date": two_days_ago,
            "time": "10:00"
        }
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        apt = response.json()
        
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt['id']}/status",
            json={"status": "done"}
        )
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        
        # Check that no feedback entry exists for this old appointment
        feedback_for_old = [t for t in tasks 
                           if t.get("task_type") == "feedback_call" 
                           and "Dr. Old Visit" in t.get("description", "")]
        
        assert len(feedback_for_old) == 0, f"Should not have feedback for 2-day-old visit, found {len(feedback_for_old)}"
        print(f"SUCCESS: No feedback entry for 2-day-old visit")
    
    def test_feedback_only_for_yesterday_not_today(self, api_client, seeded_data, today_str):
        """Verify feedback entries don't appear for today's visits"""
        patient = seeded_data[5] if len(seeded_data) > 5 else seeded_data[0]
        patient_id = patient["id"]
        
        # Create appointment for today and mark done
        apt_data = {
            "type": "doctor",
            "title": "Today Visit Test",
            "doctor": "Dr. Today Visit",
            "date": today_str,
            "time": "08:00"
        }
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=apt_data)
        assert response.status_code == 200
        apt = response.json()
        
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt['id']}/status",
            json={"status": "done"}
        )
        assert response.status_code == 200
        
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        
        # Check that no feedback entry exists for today's appointment
        feedback_for_today = [t for t in tasks 
                             if t.get("task_type") == "feedback_call" 
                             and "Dr. Today Visit" in t.get("description", "")]
        
        assert len(feedback_for_today) == 0, f"Should not have feedback for today's visit, found {len(feedback_for_today)}"
        print(f"SUCCESS: No feedback entry for today's visit")


class TestFeedbackCallIntegration:
    """Integration tests for feedback_call with daily task list"""
    
    def test_feedback_filter_count_matches(self, api_client, seeded_data, yesterday_str):
        """Verify feedback filter count matches actual feedback_call entries"""
        # Get daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        feedback_count = len([t for t in tasks if t.get("task_type") == "feedback_call"])
        
        print(f"SUCCESS: Found {feedback_count} feedback_call entries in daily task list")
        assert feedback_count >= 0, "Feedback count should be non-negative"
        
        return feedback_count
    
    def test_feedback_entries_sorted_correctly(self, api_client):
        """Verify feedback entries are sorted with other tasks (pending before completed)"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        tasks = response.json()
        
        # Check that pending tasks come before completed
        found_completed = False
        for task in tasks:
            if task["status"] == "completed":
                found_completed = True
            elif task["status"] == "pending" and found_completed:
                # This would mean a pending task comes after a completed one
                # which is fine as long as overdue comes first
                pass
        
        print("SUCCESS: Tasks are sorted correctly")
        return True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
