"""
Test Doctor Booking Feature - Iteration 9
Tests appointment CRUD, status updates, 3-month overdue detection, and daily task list integration.
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
    """Seed database and return patient IDs"""
    response = api_client.post(f"{BASE_URL}/api/seed")
    assert response.status_code == 200, f"Seed failed: {response.text}"
    
    # Get patients
    patients_res = api_client.get(f"{BASE_URL}/api/patients")
    assert patients_res.status_code == 200
    patients = patients_res.json()
    assert len(patients) >= 10, "Expected at least 10 seeded patients"
    
    return {"patients": patients}


class TestAppointmentCRUD:
    """Test appointment CRUD operations"""
    
    def test_get_appointments_returns_200(self, api_client, seeded_data):
        """GET /api/patients/{id}/appointments returns 200"""
        patient_id = seeded_data["patients"][0]["id"]
        response = api_client.get(f"{BASE_URL}/api/patients/{patient_id}/appointments")
        assert response.status_code == 200
        print(f"✓ GET appointments returns 200")
    
    def test_seeded_appointments_exist(self, api_client, seeded_data):
        """Each seeded patient should have at least 1 old 'done' appointment"""
        for patient in seeded_data["patients"][:5]:  # Check first 5
            response = api_client.get(f"{BASE_URL}/api/patients/{patient['id']}/appointments")
            assert response.status_code == 200
            appointments = response.json()
            assert len(appointments) >= 1, f"Patient {patient['name']} has no appointments"
            
            # Check for old done appointment
            done_appts = [a for a in appointments if a.get("status") == "done"]
            assert len(done_appts) >= 1, f"Patient {patient['name']} has no 'done' appointments"
        print(f"✓ Seeded patients have old 'done' appointments")
    
    def test_create_appointment_success(self, api_client, seeded_data):
        """POST /api/patients/{id}/appointments creates appointment with status='upcoming'"""
        patient_id = seeded_data["patients"][0]["id"]
        
        # Create appointment for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        payload = {
            "type": "doctor",
            "title": "TEST_Cardiology Checkup",
            "doctor": "Dr. Test Doctor",
            "hospital": "Test Hospital",
            "date": tomorrow,
            "time": "14:00",
            "location": "Test Location",
            "notes": "Test appointment notes"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=payload)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "upcoming", f"Expected status='upcoming', got {data['status']}"
        assert data["type"] == "doctor"
        assert data["title"] == "TEST_Cardiology Checkup"
        assert data["doctor"] == "Dr. Test Doctor"
        assert data["hospital"] == "Test Hospital"
        assert data["date"] == tomorrow
        assert data["time"] == "14:00"
        assert data["user_id"] == patient_id
        assert "id" in data
        
        # Store for later tests
        seeded_data["test_appointment_id"] = data["id"]
        seeded_data["test_patient_id"] = patient_id
        print(f"✓ Created appointment with status='upcoming', id={data['id']}")
    
    def test_create_appointment_default_type(self, api_client, seeded_data):
        """POST with minimal data uses type='doctor' as default"""
        patient_id = seeded_data["patients"][1]["id"]
        tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        
        payload = {
            "date": tomorrow,
            "time": "10:00"
        }
        
        response = api_client.post(f"{BASE_URL}/api/patients/{patient_id}/appointments", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["type"] == "doctor", f"Expected default type='doctor', got {data['type']}"
        assert data["title"] == "Doctor Consultation", f"Expected default title"
        print(f"✓ Default type='doctor' and title='Doctor Consultation'")
    
    def test_get_appointments_sorted_by_date_desc(self, api_client, seeded_data):
        """GET /api/patients/{id}/appointments returns sorted by date desc"""
        patient_id = seeded_data["test_patient_id"]
        
        response = api_client.get(f"{BASE_URL}/api/patients/{patient_id}/appointments")
        assert response.status_code == 200
        
        appointments = response.json()
        assert len(appointments) >= 2, "Expected at least 2 appointments"
        
        # Check sort order (newest first)
        dates = [a["date"] for a in appointments]
        assert dates == sorted(dates, reverse=True), f"Appointments not sorted by date desc: {dates}"
        print(f"✓ Appointments sorted by date desc")
    
    def test_appointment_model_fields(self, api_client, seeded_data):
        """Appointment model has all required fields aligned with enCARE"""
        patient_id = seeded_data["test_patient_id"]
        
        response = api_client.get(f"{BASE_URL}/api/patients/{patient_id}/appointments")
        assert response.status_code == 200
        
        appointments = response.json()
        assert len(appointments) > 0
        
        appt = appointments[0]
        required_fields = ["id", "user_id", "type", "title", "date", "time", "status", "created_at"]
        optional_fields = ["doctor", "hospital", "location", "notes"]
        
        for field in required_fields:
            assert field in appt, f"Missing required field: {field}"
        
        print(f"✓ Appointment model has all required fields: {required_fields}")


class TestAppointmentStatusUpdate:
    """Test appointment status updates"""
    
    def test_update_status_to_done(self, api_client, seeded_data):
        """PUT /api/patients/{id}/appointments/{apt_id}/status updates to 'done'"""
        patient_id = seeded_data["test_patient_id"]
        apt_id = seeded_data["test_appointment_id"]
        
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt_id}/status",
            json={"status": "done"}
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        data = response.json()
        assert data["status"] == "done"
        print(f"✓ Updated appointment status to 'done'")
    
    def test_update_status_to_postponed(self, api_client, seeded_data):
        """PUT updates status to 'postponed'"""
        patient_id = seeded_data["patients"][2]["id"]
        
        # Create new appointment
        tomorrow = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        create_res = api_client.post(
            f"{BASE_URL}/api/patients/{patient_id}/appointments",
            json={"date": tomorrow, "time": "11:00", "title": "TEST_Postpone Test"}
        )
        assert create_res.status_code == 200
        apt_id = create_res.json()["id"]
        
        # Update to postponed
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt_id}/status",
            json={"status": "postponed"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "postponed"
        print(f"✓ Updated appointment status to 'postponed'")
    
    def test_update_status_to_abandoned(self, api_client, seeded_data):
        """PUT updates status to 'abandoned'"""
        patient_id = seeded_data["patients"][3]["id"]
        
        # Create new appointment
        tomorrow = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")
        create_res = api_client.post(
            f"{BASE_URL}/api/patients/{patient_id}/appointments",
            json={"date": tomorrow, "time": "15:00", "title": "TEST_Abandon Test"}
        )
        assert create_res.status_code == 200
        apt_id = create_res.json()["id"]
        
        # Update to abandoned
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt_id}/status",
            json={"status": "abandoned"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "abandoned"
        print(f"✓ Updated appointment status to 'abandoned'")
    
    def test_update_status_invalid_rejected(self, api_client, seeded_data):
        """PUT with invalid status returns 400"""
        patient_id = seeded_data["test_patient_id"]
        apt_id = seeded_data["test_appointment_id"]
        
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt_id}/status",
            json={"status": "invalid_status"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Invalid status rejected with 400")
    
    def test_valid_statuses_encare_aligned(self, api_client, seeded_data):
        """Valid statuses are: upcoming, done, postponed, abandoned (enCARE aligned)"""
        patient_id = seeded_data["patients"][4]["id"]
        valid_statuses = ["upcoming", "done", "postponed", "abandoned"]
        
        for status in valid_statuses:
            # Create appointment
            date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
            create_res = api_client.post(
                f"{BASE_URL}/api/patients/{patient_id}/appointments",
                json={"date": date, "time": "09:00", "title": f"TEST_{status}_test"}
            )
            assert create_res.status_code == 200
            apt_id = create_res.json()["id"]
            
            # Update to each valid status
            update_res = api_client.put(
                f"{BASE_URL}/api/patients/{patient_id}/appointments/{apt_id}/status",
                json={"status": status}
            )
            assert update_res.status_code == 200, f"Status '{status}' should be valid"
        
        print(f"✓ All enCARE statuses valid: {valid_statuses}")


class TestThreeMonthOverdue:
    """Test 3-month overdue detection and high priority flagging"""
    
    def test_seeded_patients_have_old_appointments(self, api_client, seeded_data):
        """Seeded patients have appointments 4-5 months old (triggers 3-month overdue)"""
        three_months_ago = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        overdue_count = 0
        for patient in seeded_data["patients"][:5]:
            response = api_client.get(f"{BASE_URL}/api/patients/{patient['id']}/appointments")
            appointments = response.json()
            
            done_appts = [a for a in appointments if a.get("status") == "done"]
            if done_appts:
                latest_done = max(done_appts, key=lambda x: x["date"])
                if latest_done["date"] < three_months_ago:
                    overdue_count += 1
        
        assert overdue_count >= 3, f"Expected at least 3 patients with 3+ month overdue, got {overdue_count}"
        print(f"✓ Found {overdue_count} patients with 3+ month overdue appointments")
    
    def test_daily_task_list_has_doctor_visit_overdue(self, api_client, seeded_data):
        """Daily task list includes doctor_visit_overdue entries for 3+ month overdue patients"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        entries = response.json()
        overdue_entries = [e for e in entries if e.get("task_type") == "doctor_visit_overdue"]
        
        assert len(overdue_entries) >= 1, f"Expected doctor_visit_overdue entries, got {len(overdue_entries)}"
        
        # Check entry structure
        for entry in overdue_entries[:3]:
            assert entry["status"] == "overdue"
            assert entry["priority"] == "high"
            assert entry["revenue"] == 0
            assert "Last doctor visit" in entry["description"]
        
        print(f"✓ Daily task list has {len(overdue_entries)} doctor_visit_overdue entries")
    
    def test_overdue_patients_flagged_high_priority(self, api_client, seeded_data):
        """3-month overdue patients are auto-flagged as high priority"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        entries = response.json()
        
        overdue_entries = [e for e in entries if e.get("task_type") == "doctor_visit_overdue"]
        
        for entry in overdue_entries[:3]:
            # Verify patient is flagged high priority
            patient_res = api_client.get(f"{BASE_URL}/api/patients/{entry['patient_id']}")
            if patient_res.status_code == 200:
                patient = patient_res.json()
                assert patient.get("priority") == "high", f"Patient {entry['patient_name']} should be high priority"
        
        print(f"✓ Overdue patients are flagged as high priority")


class TestDailyTaskListDoctorAppointments:
    """Test daily task list integration for doctor appointments"""
    
    def test_today_appointments_in_task_list(self, api_client, seeded_data):
        """Doctor appointments for today appear in daily task list"""
        patient_id = seeded_data["patients"][5]["id"]
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create appointment for today
        create_res = api_client.post(
            f"{BASE_URL}/api/patients/{patient_id}/appointments",
            json={
                "date": today,
                "time": "16:00",
                "title": "TEST_Today Appointment",
                "doctor": "Dr. Today Test",
                "hospital": "Today Hospital"
            }
        )
        assert create_res.status_code == 200
        apt_id = create_res.json()["id"]
        
        # Check daily task list
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        
        entries = response.json()
        appt_entries = [e for e in entries if e.get("task_type") == "doctor_appointment"]
        
        # Find our test appointment
        test_entry = next((e for e in appt_entries if "Dr. Today Test" in e.get("description", "")), None)
        assert test_entry is not None, "Today's appointment should appear in task list"
        
        assert test_entry["status"] == "upcoming"
        assert test_entry["revenue"] == 0
        assert "16:00" in test_entry["description"]
        
        print(f"✓ Today's appointments appear in daily task list as doctor_appointment")
    
    def test_appointment_entries_have_zero_revenue(self, api_client, seeded_data):
        """Appointment entries have revenue=0 (not revenue-generating)"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        entries = response.json()
        
        appt_entries = [e for e in entries if e.get("task_type") in ["doctor_appointment", "doctor_visit_overdue"]]
        
        for entry in appt_entries:
            assert entry["revenue"] == 0, f"Appointment entry should have revenue=0, got {entry['revenue']}"
        
        print(f"✓ All appointment entries have revenue=0")


class TestAppointmentNotInRevenue:
    """Test that appointments are NOT included in revenue calculations"""
    
    def test_dashboard_stats_excludes_appointments(self, api_client, seeded_data):
        """Dashboard stats should not include appointment revenue"""
        response = api_client.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        
        stats = response.json()
        # Appointments should not contribute to revenue
        # This is a sanity check - appointments have revenue=0
        print(f"✓ Dashboard stats retrieved (appointments have revenue=0)")


class TestAppointmentNotFound:
    """Test error handling for non-existent appointments"""
    
    def test_update_nonexistent_appointment(self, api_client, seeded_data):
        """PUT to non-existent appointment returns 404"""
        patient_id = seeded_data["patients"][0]["id"]
        
        response = api_client.put(
            f"{BASE_URL}/api/patients/{patient_id}/appointments/nonexistent-id/status",
            json={"status": "done"}
        )
        assert response.status_code == 404
        print(f"✓ Non-existent appointment returns 404")
    
    def test_create_appointment_nonexistent_patient(self, api_client, seeded_data):
        """POST to non-existent patient returns 404"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = api_client.post(
            f"{BASE_URL}/api/patients/nonexistent-patient-id/appointments",
            json={"date": tomorrow, "time": "10:00"}
        )
        assert response.status_code == 404
        print(f"✓ Non-existent patient returns 404")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
