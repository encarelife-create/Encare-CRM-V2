"""
Test suite for Log Interaction follow-up date/time validation
Tests the new requirements:
1. Follow-up date is mandatory (was optional)
2. Follow-up time field added
3. Both must be in the future
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def patient_id():
    """Get a patient ID from the seeded data"""
    response = requests.get(f"{BASE_URL}/api/patients")
    assert response.status_code == 200
    patients = response.json()
    assert len(patients) > 0, "No patients found - run seed first"
    return patients[0]['id']


class TestInteractionFollowUpValidation:
    """Tests for follow-up date/time validation in interactions"""
    
    def test_missing_follow_up_date_returns_400(self, patient_id):
        """POST without follow_up_date should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/patients/{patient_id}/interactions",
            json={
                "type": "call",
                "notes": "Test call without follow-up date",
                "outcome": "positive"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "follow-up date" in data["detail"].lower() or "required" in data["detail"].lower()
    
    def test_empty_follow_up_date_returns_400(self, patient_id):
        """POST with empty follow_up_date should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/patients/{patient_id}/interactions",
            json={
                "type": "call",
                "notes": "Test call with empty follow-up date",
                "outcome": "positive",
                "follow_up_date": "",
                "follow_up_time": "10:00"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_past_date_returns_400(self, patient_id):
        """POST with past date should return 400"""
        past_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        response = requests.post(
            f"{BASE_URL}/api/patients/{patient_id}/interactions",
            json={
                "type": "call",
                "notes": "Test call with past date",
                "outcome": "positive",
                "follow_up_date": past_date,
                "follow_up_time": "10:00"
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "future" in data["detail"].lower()
    
    def test_past_datetime_today_returns_400(self, patient_id):
        """POST with today's date but past time should return 400"""
        today = datetime.now().strftime("%Y-%m-%d")
        past_time = (datetime.now() - timedelta(hours=2)).strftime("%H:%M")
        response = requests.post(
            f"{BASE_URL}/api/patients/{patient_id}/interactions",
            json={
                "type": "call",
                "notes": "Test call with past time today",
                "outcome": "positive",
                "follow_up_date": today,
                "follow_up_time": past_time
            }
        )
        # This should return 400 since the datetime is in the past
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "future" in data["detail"].lower()
    
    def test_future_date_with_time_succeeds(self, patient_id):
        """POST with future date and time should succeed"""
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        response = requests.post(
            f"{BASE_URL}/api/patients/{patient_id}/interactions",
            json={
                "type": "call",
                "notes": "TEST_Valid future interaction",
                "outcome": "positive",
                "follow_up_date": future_date,
                "follow_up_time": "14:30"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "id" in data
        assert data["follow_up_date"] == future_date
        assert data["follow_up_time"] == "14:30"
        assert data["type"] == "call"
        assert data["outcome"] == "positive"
        assert "created_at" in data
    
    def test_future_date_default_time(self, patient_id):
        """POST with future date and no time should use default 09:00"""
        future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        response = requests.post(
            f"{BASE_URL}/api/patients/{patient_id}/interactions",
            json={
                "type": "message",
                "notes": "TEST_Future interaction with default time",
                "outcome": "neutral",
                "follow_up_date": future_date
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["follow_up_date"] == future_date
        assert data["follow_up_time"] == "09:00"  # Default time
    
    def test_interaction_persisted_with_follow_up_time(self, patient_id):
        """Verify interaction is persisted and retrievable with follow_up_time"""
        future_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        
        # Create interaction
        create_response = requests.post(
            f"{BASE_URL}/api/patients/{patient_id}/interactions",
            json={
                "type": "visit",
                "notes": "TEST_Persistence check interaction",
                "outcome": "positive",
                "follow_up_date": future_date,
                "follow_up_time": "16:45"
            }
        )
        assert create_response.status_code == 200
        created = create_response.json()
        
        # Retrieve patient and check interactions
        get_response = requests.get(f"{BASE_URL}/api/patients/{patient_id}")
        assert get_response.status_code == 200
        patient = get_response.json()
        
        # Find our interaction
        interactions = patient.get("interactions", [])
        found = None
        for interaction in interactions:
            if interaction.get("notes") == "TEST_Persistence check interaction":
                found = interaction
                break
        
        assert found is not None, "Created interaction not found in patient data"
        assert found["follow_up_date"] == future_date
        assert found["follow_up_time"] == "16:45"
    
    def test_invalid_date_format_returns_400(self, patient_id):
        """POST with invalid date format should return 400"""
        response = requests.post(
            f"{BASE_URL}/api/patients/{patient_id}/interactions",
            json={
                "type": "call",
                "notes": "Test with invalid date format",
                "outcome": "positive",
                "follow_up_date": "15-05-2026",  # Wrong format
                "follow_up_time": "10:00"
            }
        )
        assert response.status_code == 400
    
    def test_all_interaction_types_work(self, patient_id):
        """Test all interaction types (call, message, visit) work with follow-up"""
        future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        
        for interaction_type in ["call", "message", "visit"]:
            response = requests.post(
                f"{BASE_URL}/api/patients/{patient_id}/interactions",
                json={
                    "type": interaction_type,
                    "notes": f"TEST_{interaction_type} interaction",
                    "outcome": "positive",
                    "follow_up_date": future_date,
                    "follow_up_time": "11:00"
                }
            )
            assert response.status_code == 200, f"Failed for type: {interaction_type}"
            data = response.json()
            assert data["type"] == interaction_type
    
    def test_all_outcomes_work(self, patient_id):
        """Test all outcome types work with follow-up"""
        future_date = (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d")
        
        for outcome in ["positive", "neutral", "negative", "no_answer"]:
            response = requests.post(
                f"{BASE_URL}/api/patients/{patient_id}/interactions",
                json={
                    "type": "call",
                    "notes": f"TEST_{outcome} outcome interaction",
                    "outcome": outcome,
                    "follow_up_date": future_date,
                    "follow_up_time": "12:00"
                }
            )
            assert response.status_code == 200, f"Failed for outcome: {outcome}"
            data = response.json()
            assert data["outcome"] == outcome


class TestInteractionRetrieval:
    """Tests for retrieving interactions with follow-up time"""
    
    def test_get_interactions_includes_follow_up_time(self, patient_id):
        """GET interactions should include follow_up_time field"""
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}/interactions")
        assert response.status_code == 200
        interactions = response.json()
        
        # Check that interactions have follow_up_time
        for interaction in interactions:
            if interaction.get("follow_up_date"):
                assert "follow_up_time" in interaction, "follow_up_time missing from interaction"
    
    def test_patient_detail_includes_interactions_with_time(self, patient_id):
        """GET patient should include interactions with follow_up_time"""
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}")
        assert response.status_code == 200
        patient = response.json()
        
        interactions = patient.get("interactions", [])
        for interaction in interactions:
            if interaction.get("follow_up_date"):
                assert "follow_up_time" in interaction


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
