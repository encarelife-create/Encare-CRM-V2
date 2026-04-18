"""
Test suite for enCARE Sync and Onboarding Profile endpoints.
Tests the new sync functionality (mock enCARE data pull) and onboarding profile CRUD.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSyncEndpoints:
    """Tests for sync endpoints - mock enCARE data pull"""
    
    def test_list_encare_patients(self):
        """GET /api/sync/encare-patients - List available enCARE patients for sync"""
        response = requests.get(f"{BASE_URL}/api/sync/encare-patients")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 3, f"Expected 3 enCARE patients, got {len(data)}"
        
        # Verify structure of each patient
        for patient in data:
            assert "encare_user_id" in patient, "Missing encare_user_id"
            assert "name" in patient, "Missing name"
            assert "phone" in patient, "Missing phone"
            assert "already_synced" in patient, "Missing already_synced flag"
            assert "diseases_hint" in patient, "Missing diseases_hint"
        
        # Verify expected enCARE IDs
        encare_ids = [p["encare_user_id"] for p in data]
        assert "ENC001" in encare_ids, "ENC001 should be in list"
        assert "ENC002" in encare_ids, "ENC002 should be in list"
        assert "ENC003" in encare_ids, "ENC003 should be in list"
        print(f"✓ Listed {len(data)} enCARE patients successfully")
    
    def test_sync_patient_enc002(self):
        """POST /api/sync/patient/ENC002 - Import/sync patient from enCARE"""
        response = requests.post(f"{BASE_URL}/api/sync/patient/ENC002")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "patient_id" in data, "Missing patient_id in response"
        assert "encare_user_id" in data, "Missing encare_user_id in response"
        assert data["encare_user_id"] == "ENC002", "encare_user_id should be ENC002"
        assert "action" in data, "Missing action in response"
        assert data["action"] in ["created", "updated"], f"Action should be created or updated, got {data['action']}"
        assert "medicines_synced" in data, "Missing medicines_synced count"
        assert data["medicines_synced"] >= 0, "medicines_synced should be >= 0"
        assert "diseases_detected" in data, "Missing diseases_detected"
        
        print(f"✓ Synced patient ENC002: {data['action']}, {data['medicines_synced']} medicines")
        return data["patient_id"]
    
    def test_sync_patient_enc003(self):
        """POST /api/sync/patient/ENC003 - Import/sync patient from enCARE"""
        response = requests.post(f"{BASE_URL}/api/sync/patient/ENC003")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "patient_id" in data, "Missing patient_id"
        assert data["encare_user_id"] == "ENC003", "encare_user_id should be ENC003"
        print(f"✓ Synced patient ENC003: {data['action']}, {data['medicines_synced']} medicines")
        return data["patient_id"]
    
    def test_sync_patient_invalid(self):
        """POST /api/sync/patient/INVALID - Should return 404 for non-existent enCARE user"""
        response = requests.post(f"{BASE_URL}/api/sync/patient/INVALID_USER")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid enCARE user returns 404 as expected")
    
    def test_sync_medications_for_synced_patient(self):
        """POST /api/sync/medications/ENC002 - Sync medications for already-synced patient"""
        # First ensure patient is synced
        requests.post(f"{BASE_URL}/api/sync/patient/ENC002")
        
        response = requests.post(f"{BASE_URL}/api/sync/medications/ENC002")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "patient_id" in data, "Missing patient_id"
        assert "medicines_synced" in data, "Missing medicines_synced"
        assert data["medicines_synced"] >= 0, "medicines_synced should be >= 0"
        print(f"✓ Synced medications for ENC002: {data['medicines_synced']} medicines")
    
    def test_sync_medications_for_unsynced_patient(self):
        """POST /api/sync/medications/INVALID - Should return 404 for unsynced patient"""
        response = requests.post(f"{BASE_URL}/api/sync/medications/INVALID_USER")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Medications sync for unsynced patient returns 404 as expected")
    
    def test_sync_vitals_for_synced_patient(self):
        """POST /api/sync/vitals/ENC002 - Sync vitals for already-synced patient"""
        # First ensure patient is synced
        requests.post(f"{BASE_URL}/api/sync/patient/ENC002")
        
        response = requests.post(f"{BASE_URL}/api/sync/vitals/ENC002")
        # ENC002 has vitals data in mock
        if response.status_code == 200:
            data = response.json()
            assert "patient_id" in data, "Missing patient_id"
            assert "counts" in data, "Missing counts"
            print(f"✓ Synced vitals for ENC002: {data['counts']}")
        elif response.status_code == 404:
            # No vitals data for this user is also valid
            print("✓ No vitals data for ENC002 (404 expected)")
        else:
            assert False, f"Unexpected status code: {response.status_code}"
    
    def test_sync_vitals_enc001(self):
        """POST /api/sync/vitals/ENC001 - Sync vitals for ENC001 (has vitals data)"""
        # First ensure patient is synced
        requests.post(f"{BASE_URL}/api/sync/patient/ENC001")
        
        response = requests.post(f"{BASE_URL}/api/sync/vitals/ENC001")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "counts" in data, "Missing counts"
        counts = data["counts"]
        assert "blood_glucose" in counts, "Missing blood_glucose count"
        assert "blood_pressure" in counts, "Missing blood_pressure count"
        print(f"✓ Synced vitals for ENC001: {counts['blood_glucose']} glucose, {counts['blood_pressure']} BP readings")
    
    def test_sync_vitals_for_unsynced_patient(self):
        """POST /api/sync/vitals/INVALID - Should return 404 for unsynced patient"""
        response = requests.post(f"{BASE_URL}/api/sync/vitals/INVALID_USER")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Vitals sync for unsynced patient returns 404 as expected")
    
    def test_get_sync_status(self):
        """GET /api/sync/status - Get sync activity logs"""
        response = requests.get(f"{BASE_URL}/api/sync/status")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If there are logs, verify structure
        if len(data) > 0:
            log = data[0]
            assert "sync_type" in log, "Missing sync_type"
            assert "patient_name" in log, "Missing patient_name"
            assert "synced_at" in log, "Missing synced_at"
            assert "details" in log, "Missing details"
        print(f"✓ Got {len(data)} sync logs")
    
    def test_get_patient_sync_status(self):
        """GET /api/sync/status/{patient_id} - Get patient-specific sync status"""
        # First sync a patient to get their ID
        sync_response = requests.post(f"{BASE_URL}/api/sync/patient/ENC002")
        assert sync_response.status_code == 200
        patient_id = sync_response.json()["patient_id"]
        
        response = requests.get(f"{BASE_URL}/api/sync/status/{patient_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "patient_id" in data, "Missing patient_id"
        assert data["patient_id"] == patient_id, "patient_id mismatch"
        assert "encare_user_id" in data, "Missing encare_user_id"
        assert data["encare_user_id"] == "ENC002", "encare_user_id should be ENC002"
        assert "last_synced_at" in data, "Missing last_synced_at"
        assert "sync_logs" in data, "Missing sync_logs"
        print(f"✓ Got sync status for patient {patient_id}")
    
    def test_get_patient_sync_status_invalid(self):
        """GET /api/sync/status/INVALID - Should return 404 for non-existent patient"""
        response = requests.get(f"{BASE_URL}/api/sync/status/invalid-patient-id")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Sync status for invalid patient returns 404 as expected")


class TestOnboardingEndpoints:
    """Tests for onboarding profile endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: ensure we have a synced patient to test with"""
        # Sync ENC002 to have a patient to test onboarding
        response = requests.post(f"{BASE_URL}/api/sync/patient/ENC002")
        assert response.status_code == 200
        self.patient_id = response.json()["patient_id"]
    
    def test_get_onboarding_profile(self):
        """GET /api/patients/{patient_id}/onboarding - Get onboarding profile data"""
        response = requests.get(f"{BASE_URL}/api/patients/{self.patient_id}/onboarding")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify all expected fields are present
        expected_fields = [
            "id", "name", "email", "phone", "picture", "age", "sex",
            "address", "city", "state", "country", "pincode",
            "diabetes_type", "diseases", "adherence_rate",
            "relative_name", "relative_email", "relative_whatsapp",
            "medicine_order_link", "medicine_invoice_link", "medicine_invoice_amount",
            "injection_order_link", "injection_invoice_link", "injection_invoice_amount",
            "priority"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify data values for ENC002 (Lakshmi Iyer)
        assert data["name"] == "Lakshmi Iyer", f"Expected 'Lakshmi Iyer', got '{data['name']}'"
        assert data["city"] == "Chennai", f"Expected 'Chennai', got '{data['city']}'"
        assert data["state"] == "Tamil Nadu", f"Expected 'Tamil Nadu', got '{data['state']}'"
        
        print(f"✓ Got onboarding profile for {data['name']}")
    
    def test_get_onboarding_profile_invalid(self):
        """GET /api/patients/INVALID/onboarding - Should return 404"""
        response = requests.get(f"{BASE_URL}/api/patients/invalid-patient-id/onboarding")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Onboarding profile for invalid patient returns 404 as expected")
    
    def test_update_onboarding_profile_basic(self):
        """PUT /api/patients/{patient_id}/onboarding - Update basic profile fields"""
        update_data = {
            "name": "Lakshmi Iyer Updated",
            "phone": "+91 98765 99999",
            "email": "lakshmi.updated@email.com"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/onboarding",
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["name"] == "Lakshmi Iyer Updated", "Name not updated"
        assert data["phone"] == "+91 98765 99999", "Phone not updated"
        assert data["email"] == "lakshmi.updated@email.com", "Email not updated"
        
        # Verify persistence with GET
        get_response = requests.get(f"{BASE_URL}/api/patients/{self.patient_id}/onboarding")
        assert get_response.status_code == 200
        get_data = get_response.json()
        assert get_data["name"] == "Lakshmi Iyer Updated", "Name not persisted"
        
        print("✓ Updated basic profile fields successfully")
    
    def test_update_onboarding_profile_address(self):
        """PUT /api/patients/{patient_id}/onboarding - Update address fields"""
        update_data = {
            "address": "123, Test Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "country": "India"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/onboarding",
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["address"] == "123, Test Street", "Address not updated"
        assert data["city"] == "Mumbai", "City not updated"
        assert data["state"] == "Maharashtra", "State not updated"
        assert data["pincode"] == "400001", "Pincode not updated"
        
        print("✓ Updated address fields successfully")
    
    def test_update_onboarding_profile_medical(self):
        """PUT /api/patients/{patient_id}/onboarding - Update medical fields"""
        update_data = {
            "diabetes_type": "Type 2",
            "adherence_rate": 92.5
        }
        
        response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/onboarding",
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["diabetes_type"] == "Type 2", "Diabetes type not updated"
        assert data["adherence_rate"] == 92.5, "Adherence rate not updated"
        
        print("✓ Updated medical fields successfully")
    
    def test_update_onboarding_profile_caregiver(self):
        """PUT /api/patients/{patient_id}/onboarding - Update caregiver/relative fields"""
        update_data = {
            "relative_name": "Test Relative",
            "relative_email": "relative@test.com",
            "relative_whatsapp": "+91 12345 67890"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/onboarding",
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["relative_name"] == "Test Relative", "Relative name not updated"
        assert data["relative_email"] == "relative@test.com", "Relative email not updated"
        assert data["relative_whatsapp"] == "+91 12345 67890", "Relative whatsapp not updated"
        
        # Verify caregivers array is also updated
        assert len(data.get("caregivers", [])) > 0, "Caregivers array should be populated"
        assert data["caregivers"][0]["name"] == "Test Relative", "Caregiver name mismatch"
        
        print("✓ Updated caregiver fields successfully")
    
    def test_update_onboarding_profile_invoice(self):
        """PUT /api/patients/{patient_id}/onboarding - Update invoice fields"""
        update_data = {
            "medicine_order_link": "https://order.example.com/med123",
            "medicine_invoice_link": "https://invoice.example.com/inv123",
            "medicine_invoice_amount": 1500.50,
            "injection_order_link": "https://order.example.com/inj456",
            "injection_invoice_link": "https://invoice.example.com/inj456",
            "injection_invoice_amount": 2500.00
        }
        
        response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/onboarding",
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["medicine_order_link"] == "https://order.example.com/med123", "Medicine order link not updated"
        assert data["medicine_invoice_amount"] == 1500.50, "Medicine invoice amount not updated"
        assert data["injection_invoice_amount"] == 2500.00, "Injection invoice amount not updated"
        
        print("✓ Updated invoice fields successfully")
    
    def test_update_onboarding_profile_priority(self):
        """PUT /api/patients/{patient_id}/onboarding - Update priority"""
        update_data = {
            "priority": "high"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/onboarding",
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["priority"] == "high", "Priority not updated"
        
        print("✓ Updated priority successfully")
    
    def test_update_onboarding_profile_elderly_care_auto_detect(self):
        """PUT /api/patients/{patient_id}/onboarding - Verify Elderly Care auto-detection"""
        # Update age to 70 (should add Elderly Care disease)
        update_data = {
            "age": 70
        }
        
        response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/onboarding",
            json=update_data
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["age"] == 70, "Age not updated"
        assert "Elderly Care" in data.get("diseases", []), "Elderly Care should be auto-detected for age >= 65"
        
        print("✓ Elderly Care auto-detection works correctly")
    
    def test_update_onboarding_profile_invalid_patient(self):
        """PUT /api/patients/INVALID/onboarding - Should return 404"""
        response = requests.put(
            f"{BASE_URL}/api/patients/invalid-patient-id/onboarding",
            json={"name": "Test"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Update onboarding for invalid patient returns 404 as expected")
    
    def test_update_onboarding_full_profile(self):
        """PUT /api/patients/{patient_id}/onboarding - Full profile update with all fields"""
        full_update = {
            "name": "Full Test Patient",
            "email": "full.test@email.com",
            "phone": "+91 11111 22222",
            "age": 55,
            "sex": "Female",
            "address": "456, Full Test Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560001",
            "country": "India",
            "diabetes_type": "Type 1",
            "adherence_rate": 88,
            "relative_name": "Full Test Relative",
            "relative_email": "fullrelative@test.com",
            "relative_whatsapp": "+91 33333 44444",
            "medicine_order_link": "https://full.order.com",
            "medicine_invoice_link": "https://full.invoice.com",
            "medicine_invoice_amount": 3000,
            "injection_order_link": "https://full.injection.order.com",
            "injection_invoice_link": "https://full.injection.invoice.com",
            "injection_invoice_amount": 4000,
            "priority": "normal"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/onboarding",
            json=full_update
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify all fields were updated
        for key, value in full_update.items():
            assert data.get(key) == value, f"Field {key} not updated correctly. Expected {value}, got {data.get(key)}"
        
        print("✓ Full profile update successful with all fields")


class TestSyncIntegration:
    """Integration tests for sync workflow"""
    
    def test_full_sync_workflow(self):
        """Test complete sync workflow: list -> sync patient -> sync meds -> sync vitals"""
        # Step 1: List available patients
        list_response = requests.get(f"{BASE_URL}/api/sync/encare-patients")
        assert list_response.status_code == 200
        patients = list_response.json()
        assert len(patients) >= 1, "Should have at least 1 enCARE patient"
        
        # Step 2: Sync a patient (ENC003)
        sync_response = requests.post(f"{BASE_URL}/api/sync/patient/ENC003")
        assert sync_response.status_code == 200
        patient_id = sync_response.json()["patient_id"]
        
        # Step 3: Sync medications
        meds_response = requests.post(f"{BASE_URL}/api/sync/medications/ENC003")
        assert meds_response.status_code == 200
        
        # Step 4: Sync vitals
        vitals_response = requests.post(f"{BASE_URL}/api/sync/vitals/ENC003")
        assert vitals_response.status_code == 200
        
        # Step 5: Verify sync status
        status_response = requests.get(f"{BASE_URL}/api/sync/status/{patient_id}")
        assert status_response.status_code == 200
        status = status_response.json()
        assert status["encare_user_id"] == "ENC003"
        assert len(status["sync_logs"]) >= 1, "Should have sync logs"
        
        # Step 6: Verify patient data via onboarding endpoint
        onboarding_response = requests.get(f"{BASE_URL}/api/patients/{patient_id}/onboarding")
        assert onboarding_response.status_code == 200
        onboarding = onboarding_response.json()
        assert onboarding["name"] == "Mohammed Faiz", "Patient name should match ENC003"
        
        print("✓ Full sync workflow completed successfully")
    
    def test_resync_updates_patient(self):
        """Test that re-syncing a patient updates their data"""
        # First sync
        first_sync = requests.post(f"{BASE_URL}/api/sync/patient/ENC001")
        assert first_sync.status_code == 200
        first_data = first_sync.json()
        
        # Second sync (should update)
        second_sync = requests.post(f"{BASE_URL}/api/sync/patient/ENC001")
        assert second_sync.status_code == 200
        second_data = second_sync.json()
        
        # Patient ID should remain the same
        assert first_data["patient_id"] == second_data["patient_id"], "Patient ID should remain same on resync"
        
        # Action should be 'updated' on second sync
        assert second_data["action"] == "updated", "Second sync should be an update"
        
        print("✓ Re-sync correctly updates patient data")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
