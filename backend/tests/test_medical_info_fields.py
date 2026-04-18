"""
Test suite for new Medical Information fields in onboarding profile.
Tests: main_disease, consulting_doctor_name, clinic_hospital_details, 
last_doctor_visit_date, regular_lab_details, last_lab_visit_date, 
mobility_status, other_critical_info
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test patient ID with pre-filled medical data
TEST_PATIENT_ID = "5d16441e-5b76-4dac-a164-8ca85ec5a614"


class TestOnboardingMedicalFields:
    """Tests for GET /api/patients/{id}/onboarding - new medical fields"""
    
    def test_onboarding_returns_main_disease(self):
        """Verify main_disease field is returned in onboarding profile"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.status_code == 200
        data = response.json()
        assert "main_disease" in data
        assert data["main_disease"] == "Hypothyroidism"
        print(f"✓ main_disease returned: {data['main_disease']}")
    
    def test_onboarding_returns_consulting_doctor_name(self):
        """Verify consulting_doctor_name field is returned"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.status_code == 200
        data = response.json()
        assert "consulting_doctor_name" in data
        assert data["consulting_doctor_name"] == "Dr. Meena Kapoor"
        print(f"✓ consulting_doctor_name returned: {data['consulting_doctor_name']}")
    
    def test_onboarding_returns_clinic_hospital_details(self):
        """Verify clinic_hospital_details field is returned"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.status_code == 200
        data = response.json()
        assert "clinic_hospital_details" in data
        assert "Apollo Clinic" in data["clinic_hospital_details"]
        print(f"✓ clinic_hospital_details returned: {data['clinic_hospital_details']}")
    
    def test_onboarding_returns_last_doctor_visit_date(self):
        """Verify last_doctor_visit_date field is returned"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.status_code == 200
        data = response.json()
        assert "last_doctor_visit_date" in data
        assert data["last_doctor_visit_date"] == "2026-03-15"
        print(f"✓ last_doctor_visit_date returned: {data['last_doctor_visit_date']}")
    
    def test_onboarding_returns_regular_lab_details(self):
        """Verify regular_lab_details field is returned"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.status_code == 200
        data = response.json()
        assert "regular_lab_details" in data
        assert "SRL Diagnostics" in data["regular_lab_details"]
        print(f"✓ regular_lab_details returned: {data['regular_lab_details']}")
    
    def test_onboarding_returns_last_lab_visit_date(self):
        """Verify last_lab_visit_date field is returned"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.status_code == 200
        data = response.json()
        assert "last_lab_visit_date" in data
        assert data["last_lab_visit_date"] == "2026-02-20"
        print(f"✓ last_lab_visit_date returned: {data['last_lab_visit_date']}")
    
    def test_onboarding_returns_mobility_status(self):
        """Verify mobility_status field is returned"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.status_code == 200
        data = response.json()
        assert "mobility_status" in data
        assert data["mobility_status"] == "Needs Assistance"
        print(f"✓ mobility_status returned: {data['mobility_status']}")
    
    def test_onboarding_returns_other_critical_info(self):
        """Verify other_critical_info field is returned"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.status_code == 200
        data = response.json()
        assert "other_critical_info" in data
        assert "Allergic to sulfa drugs" in data["other_critical_info"]
        print(f"✓ other_critical_info returned: {data['other_critical_info']}")
    
    def test_onboarding_returns_diseases_array(self):
        """Verify diseases array (auto-detected) is returned"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.status_code == 200
        data = response.json()
        assert "diseases" in data
        assert isinstance(data["diseases"], list)
        assert "Thyroid" in data["diseases"]
        assert "Hypertension" in data["diseases"]
        assert "Elderly Care" in data["diseases"]
        print(f"✓ diseases returned: {data['diseases']}")


class TestPatientDetailMedicalFields:
    """Tests for GET /api/patients/{id} - medical fields on patient detail"""
    
    def test_patient_detail_returns_main_disease(self):
        """Verify main_disease is returned in patient detail"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "main_disease" in data
        assert data["main_disease"] == "Hypothyroidism"
        print(f"✓ Patient detail main_disease: {data['main_disease']}")
    
    def test_patient_detail_returns_consulting_doctor(self):
        """Verify consulting_doctor_name is returned in patient detail"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "consulting_doctor_name" in data
        assert data["consulting_doctor_name"] == "Dr. Meena Kapoor"
        print(f"✓ Patient detail consulting_doctor_name: {data['consulting_doctor_name']}")
    
    def test_patient_detail_returns_clinic_hospital(self):
        """Verify clinic_hospital_details is returned in patient detail"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "clinic_hospital_details" in data
        print(f"✓ Patient detail clinic_hospital_details: {data['clinic_hospital_details']}")
    
    def test_patient_detail_returns_last_doctor_visit(self):
        """Verify last_doctor_visit_date is returned in patient detail"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "last_doctor_visit_date" in data
        print(f"✓ Patient detail last_doctor_visit_date: {data['last_doctor_visit_date']}")
    
    def test_patient_detail_returns_regular_lab(self):
        """Verify regular_lab_details is returned in patient detail"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "regular_lab_details" in data
        print(f"✓ Patient detail regular_lab_details: {data['regular_lab_details']}")
    
    def test_patient_detail_returns_last_lab_visit(self):
        """Verify last_lab_visit_date is returned in patient detail"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "last_lab_visit_date" in data
        print(f"✓ Patient detail last_lab_visit_date: {data['last_lab_visit_date']}")
    
    def test_patient_detail_returns_mobility_status(self):
        """Verify mobility_status is returned in patient detail"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "mobility_status" in data
        print(f"✓ Patient detail mobility_status: {data['mobility_status']}")
    
    def test_patient_detail_returns_other_critical_info(self):
        """Verify other_critical_info is returned in patient detail"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert "other_critical_info" in data
        print(f"✓ Patient detail other_critical_info: {data['other_critical_info']}")


class TestUpdateOnboardingMedicalFields:
    """Tests for PUT /api/patients/{id}/onboarding - updating medical fields"""
    
    def test_update_main_disease(self):
        """Test updating main_disease field"""
        # Get current value
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        original_value = response.json().get("main_disease")
        
        # Update
        update_data = {"main_disease": "TEST_Hypothyroidism_Updated"}
        response = requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=update_data
        )
        assert response.status_code == 200
        
        # Verify update persisted
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.json()["main_disease"] == "TEST_Hypothyroidism_Updated"
        print("✓ main_disease update persisted")
        
        # Restore original
        requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json={"main_disease": original_value}
        )
    
    def test_update_consulting_doctor_name(self):
        """Test updating consulting_doctor_name field"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        original_value = response.json().get("consulting_doctor_name")
        
        update_data = {"consulting_doctor_name": "TEST_Dr. Test Doctor"}
        response = requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=update_data
        )
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.json()["consulting_doctor_name"] == "TEST_Dr. Test Doctor"
        print("✓ consulting_doctor_name update persisted")
        
        requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json={"consulting_doctor_name": original_value}
        )
    
    def test_update_clinic_hospital_details(self):
        """Test updating clinic_hospital_details field"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        original_value = response.json().get("clinic_hospital_details")
        
        update_data = {"clinic_hospital_details": "TEST_Hospital Name"}
        response = requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=update_data
        )
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.json()["clinic_hospital_details"] == "TEST_Hospital Name"
        print("✓ clinic_hospital_details update persisted")
        
        requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json={"clinic_hospital_details": original_value}
        )
    
    def test_update_last_doctor_visit_date(self):
        """Test updating last_doctor_visit_date field"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        original_value = response.json().get("last_doctor_visit_date")
        
        update_data = {"last_doctor_visit_date": "2026-01-01"}
        response = requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=update_data
        )
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.json()["last_doctor_visit_date"] == "2026-01-01"
        print("✓ last_doctor_visit_date update persisted")
        
        requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json={"last_doctor_visit_date": original_value}
        )
    
    def test_update_regular_lab_details(self):
        """Test updating regular_lab_details field"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        original_value = response.json().get("regular_lab_details")
        
        update_data = {"regular_lab_details": "TEST_Lab Name"}
        response = requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=update_data
        )
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.json()["regular_lab_details"] == "TEST_Lab Name"
        print("✓ regular_lab_details update persisted")
        
        requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json={"regular_lab_details": original_value}
        )
    
    def test_update_last_lab_visit_date(self):
        """Test updating last_lab_visit_date field"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        original_value = response.json().get("last_lab_visit_date")
        
        update_data = {"last_lab_visit_date": "2026-01-15"}
        response = requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=update_data
        )
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.json()["last_lab_visit_date"] == "2026-01-15"
        print("✓ last_lab_visit_date update persisted")
        
        requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json={"last_lab_visit_date": original_value}
        )
    
    def test_update_mobility_status(self):
        """Test updating mobility_status field"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        original_value = response.json().get("mobility_status")
        
        update_data = {"mobility_status": "Independent"}
        response = requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=update_data
        )
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.json()["mobility_status"] == "Independent"
        print("✓ mobility_status update persisted")
        
        requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json={"mobility_status": original_value}
        )
    
    def test_update_other_critical_info(self):
        """Test updating other_critical_info field"""
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        original_value = response.json().get("other_critical_info")
        
        update_data = {"other_critical_info": "TEST_Critical info updated"}
        response = requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=update_data
        )
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        assert response.json()["other_critical_info"] == "TEST_Critical info updated"
        print("✓ other_critical_info update persisted")
        
        requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json={"other_critical_info": original_value}
        )
    
    def test_update_all_medical_fields_at_once(self):
        """Test updating all medical fields in a single request"""
        # Get original values
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        original = response.json()
        
        # Update all fields
        update_data = {
            "main_disease": "TEST_All_Fields_Disease",
            "consulting_doctor_name": "TEST_All_Fields_Doctor",
            "clinic_hospital_details": "TEST_All_Fields_Hospital",
            "last_doctor_visit_date": "2026-01-20",
            "regular_lab_details": "TEST_All_Fields_Lab",
            "last_lab_visit_date": "2026-01-25",
            "mobility_status": "Wheelchair",
            "other_critical_info": "TEST_All_Fields_Info"
        }
        response = requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=update_data
        )
        assert response.status_code == 200
        
        # Verify all updates persisted
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        data = response.json()
        assert data["main_disease"] == "TEST_All_Fields_Disease"
        assert data["consulting_doctor_name"] == "TEST_All_Fields_Doctor"
        assert data["clinic_hospital_details"] == "TEST_All_Fields_Hospital"
        assert data["last_doctor_visit_date"] == "2026-01-20"
        assert data["regular_lab_details"] == "TEST_All_Fields_Lab"
        assert data["last_lab_visit_date"] == "2026-01-25"
        assert data["mobility_status"] == "Wheelchair"
        assert data["other_critical_info"] == "TEST_All_Fields_Info"
        print("✓ All medical fields updated successfully in single request")
        
        # Restore original values
        restore_data = {
            "main_disease": original.get("main_disease", ""),
            "consulting_doctor_name": original.get("consulting_doctor_name", ""),
            "clinic_hospital_details": original.get("clinic_hospital_details", ""),
            "last_doctor_visit_date": original.get("last_doctor_visit_date", ""),
            "regular_lab_details": original.get("regular_lab_details", ""),
            "last_lab_visit_date": original.get("last_lab_visit_date", ""),
            "mobility_status": original.get("mobility_status", ""),
            "other_critical_info": original.get("other_critical_info", "")
        }
        requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=restore_data
        )


class TestMedicalFieldsOnPatientDetailAfterUpdate:
    """Test that updates to onboarding are reflected on patient detail page"""
    
    def test_onboarding_update_reflects_on_patient_detail(self):
        """Verify that updating onboarding profile reflects on patient detail"""
        # Get original values
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding")
        original = response.json()
        
        # Update via onboarding
        update_data = {
            "main_disease": "TEST_Reflect_Disease",
            "consulting_doctor_name": "TEST_Reflect_Doctor"
        }
        response = requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json=update_data
        )
        assert response.status_code == 200
        
        # Verify on patient detail endpoint
        response = requests.get(f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["main_disease"] == "TEST_Reflect_Disease"
        assert data["consulting_doctor_name"] == "TEST_Reflect_Doctor"
        print("✓ Onboarding updates reflected on patient detail page")
        
        # Restore
        requests.put(
            f"{BASE_URL}/api/patients/{TEST_PATIENT_ID}/onboarding",
            json={
                "main_disease": original.get("main_disease", ""),
                "consulting_doctor_name": original.get("consulting_doctor_name", "")
            }
        )


class TestEmptyMedicalFields:
    """Test behavior when medical fields are empty"""
    
    def test_empty_medical_fields_return_empty_strings(self):
        """Verify empty medical fields return empty strings, not null"""
        # Create a test patient without medical fields
        create_response = requests.post(
            f"{BASE_URL}/api/patients",
            json={"name": "TEST_Empty_Medical_Fields_Patient"}
        )
        assert create_response.status_code == 200
        new_patient_id = create_response.json()["id"]
        
        try:
            # Get onboarding profile
            response = requests.get(f"{BASE_URL}/api/patients/{new_patient_id}/onboarding")
            assert response.status_code == 200
            data = response.json()
            
            # Verify empty fields return empty strings
            assert data.get("main_disease") == ""
            assert data.get("consulting_doctor_name") == ""
            assert data.get("clinic_hospital_details") == ""
            assert data.get("last_doctor_visit_date") == ""
            assert data.get("regular_lab_details") == ""
            assert data.get("last_lab_visit_date") == ""
            assert data.get("mobility_status") == ""
            assert data.get("other_critical_info") == ""
            print("✓ Empty medical fields return empty strings")
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/patients/{new_patient_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
