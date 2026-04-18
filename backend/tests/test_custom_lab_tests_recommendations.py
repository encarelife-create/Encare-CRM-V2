"""
Test suite for P0 Bug Fix: Custom lab tests appearing in Patient Recommendations

Bug: Custom lab tests added via Lab Tests page were NOT appearing in 'Recommended Lab Tests' 
section on Patient Detail pages.

Root cause: get_lab_test_suggestions() only used hardcoded LAB_TEST_CATALOG.
Fix: Created get_lab_test_suggestions_with_custom() async helper that merges:
  - Built-in catalog
  - Price overrides
  - Custom tests from MongoDB custom_lab_tests collection
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCustomLabTestsInRecommendations:
    """Test that custom lab tests appear in patient recommendations when diseases match"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Seed database before tests"""
        response = requests.post(f"{BASE_URL}/api/seed")
        assert response.status_code == 200, f"Seed failed: {response.text}"
        yield
    
    def test_seed_creates_patients_with_diseases(self):
        """Verify seed creates patients with various diseases"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        patients = response.json()
        assert len(patients) >= 5, "Should have at least 5 patients"
        
        # Check disease distribution
        all_diseases = set()
        for p in patients:
            all_diseases.update(p.get("diseases", []))
        
        print(f"Diseases in seeded data: {all_diseases}")
        assert "Diabetes" in all_diseases, "Should have Diabetes patients"
        assert "Thyroid" in all_diseases, "Should have Thyroid patients"
    
    def test_get_diabetes_patient(self):
        """Find a patient with Diabetes for testing"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        patients = response.json()
        
        diabetes_patient = next((p for p in patients if "Diabetes" in p.get("diseases", [])), None)
        assert diabetes_patient is not None, "Should have at least one Diabetes patient"
        print(f"Found Diabetes patient: {diabetes_patient['name']} (ID: {diabetes_patient['id']})")
        return diabetes_patient
    
    def test_get_thyroid_patient(self):
        """Find a patient with Thyroid for testing"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        patients = response.json()
        
        thyroid_patient = next((p for p in patients if "Thyroid" in p.get("diseases", [])), None)
        assert thyroid_patient is not None, "Should have at least one Thyroid patient"
        print(f"Found Thyroid patient: {thyroid_patient['name']} (ID: {thyroid_patient['id']})")
        return thyroid_patient
    
    def test_builtin_lab_tests_appear_in_recommendations(self):
        """Built-in lab tests should appear in patient recommendations"""
        # Get a Diabetes patient
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        diabetes_patient = next((p for p in patients if "Diabetes" in p.get("diseases", [])), None)
        assert diabetes_patient is not None
        
        # Get lab test suggestions
        response = requests.get(f"{BASE_URL}/api/patients/{diabetes_patient['id']}/suggestions/lab-tests")
        assert response.status_code == 200
        suggestions = response.json()
        
        # Should include built-in tests for Diabetes
        test_names = [t["name"] for t in suggestions]
        print(f"Lab test suggestions for Diabetes patient: {test_names}")
        
        assert "HbA1c" in test_names, "HbA1c should be recommended for Diabetes"
        assert "Fasting Blood Sugar" in test_names, "Fasting Blood Sugar should be recommended for Diabetes"
    
    def test_create_custom_lab_test_for_diabetes(self):
        """Create a custom lab test for Diabetes"""
        custom_test = {
            "name": "TEST_Custom_Diabetes_Panel",
            "diseases": ["Diabetes"],
            "frequency_months": 3,
            "price": 999
        }
        
        response = requests.post(f"{BASE_URL}/api/catalog/lab-tests", json=custom_test)
        assert response.status_code == 200
        created = response.json()
        
        assert created["name"] == custom_test["name"]
        assert created["diseases"] == custom_test["diseases"]
        assert created["price"] == custom_test["price"]
        assert "id" in created
        
        print(f"Created custom test: {created['name']} (ID: {created['id']})")
        return created
    
    def test_custom_lab_test_appears_in_catalog(self):
        """Custom lab test should appear in catalog with source='custom'"""
        # Create custom test
        custom_test = {
            "name": "TEST_Catalog_Check_Test",
            "diseases": ["Diabetes"],
            "frequency_months": 6,
            "price": 500
        }
        requests.post(f"{BASE_URL}/api/catalog/lab-tests", json=custom_test)
        
        # Check catalog
        response = requests.get(f"{BASE_URL}/api/catalog/lab-tests")
        assert response.status_code == 200
        catalog = response.json()
        
        custom_in_catalog = next((t for t in catalog if t["name"] == custom_test["name"]), None)
        assert custom_in_catalog is not None, "Custom test should appear in catalog"
        assert custom_in_catalog.get("source") == "custom", "Custom test should have source='custom'"
        print(f"Custom test in catalog: {custom_in_catalog}")
    
    def test_custom_lab_test_appears_in_patient_recommendations(self):
        """P0 BUG FIX: Custom lab test should appear in patient recommendations when diseases match"""
        # Get a Diabetes patient
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        diabetes_patient = next((p for p in patients if "Diabetes" in p.get("diseases", [])), None)
        assert diabetes_patient is not None, "Need a Diabetes patient for this test"
        
        # Create custom test for Diabetes
        custom_test = {
            "name": "TEST_P0_Fix_Diabetes_Test",
            "diseases": ["Diabetes"],
            "frequency_months": 2,
            "price": 777
        }
        create_response = requests.post(f"{BASE_URL}/api/catalog/lab-tests", json=custom_test)
        assert create_response.status_code == 200
        
        # Get lab test suggestions for the Diabetes patient
        response = requests.get(f"{BASE_URL}/api/patients/{diabetes_patient['id']}/suggestions/lab-tests")
        assert response.status_code == 200
        suggestions = response.json()
        
        test_names = [t["name"] for t in suggestions]
        print(f"Suggestions for {diabetes_patient['name']}: {test_names}")
        
        # THE KEY ASSERTION - Custom test should appear in recommendations
        assert custom_test["name"] in test_names, \
            f"Custom test '{custom_test['name']}' should appear in recommendations for Diabetes patient"
        
        # Verify the custom test has correct data
        custom_in_suggestions = next((t for t in suggestions if t["name"] == custom_test["name"]), None)
        assert custom_in_suggestions is not None
        assert custom_in_suggestions["price"] == custom_test["price"]
        assert custom_in_suggestions.get("source") == "custom"
        print(f"SUCCESS: Custom test found in recommendations: {custom_in_suggestions}")
    
    def test_custom_lab_test_NOT_in_unrelated_patient_recommendations(self):
        """Custom lab test should NOT appear for patients without matching diseases"""
        # Get patients
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        
        # Find a patient WITHOUT Diabetes (e.g., only Thyroid)
        non_diabetes_patient = next(
            (p for p in patients if "Diabetes" not in p.get("diseases", []) and len(p.get("diseases", [])) > 0), 
            None
        )
        
        if non_diabetes_patient is None:
            pytest.skip("No patient without Diabetes found for this test")
        
        print(f"Testing with patient: {non_diabetes_patient['name']} (diseases: {non_diabetes_patient.get('diseases', [])})")
        
        # Create custom test ONLY for Diabetes
        custom_test = {
            "name": "TEST_Diabetes_Only_Test",
            "diseases": ["Diabetes"],
            "frequency_months": 3,
            "price": 888
        }
        requests.post(f"{BASE_URL}/api/catalog/lab-tests", json=custom_test)
        
        # Get suggestions for non-Diabetes patient
        response = requests.get(f"{BASE_URL}/api/patients/{non_diabetes_patient['id']}/suggestions/lab-tests")
        assert response.status_code == 200
        suggestions = response.json()
        
        test_names = [t["name"] for t in suggestions]
        print(f"Suggestions for {non_diabetes_patient['name']}: {test_names}")
        
        # Custom Diabetes test should NOT appear
        assert custom_test["name"] not in test_names, \
            f"Custom Diabetes test should NOT appear for patient without Diabetes"
        print("SUCCESS: Custom Diabetes test correctly excluded from non-Diabetes patient")
    
    def test_price_override_reflects_in_recommendations(self):
        """Price overrides on built-in tests should reflect in recommendations"""
        # Get a Diabetes patient
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        diabetes_patient = next((p for p in patients if "Diabetes" in p.get("diseases", [])), None)
        assert diabetes_patient is not None
        
        # Update price of HbA1c (built-in test)
        new_price = 999
        response = requests.put(
            f"{BASE_URL}/api/catalog/lab-tests/HbA1c/price",
            json={"price": new_price}
        )
        assert response.status_code == 200
        
        # Get suggestions
        response = requests.get(f"{BASE_URL}/api/patients/{diabetes_patient['id']}/suggestions/lab-tests")
        assert response.status_code == 200
        suggestions = response.json()
        
        hba1c = next((t for t in suggestions if t["name"] == "HbA1c"), None)
        assert hba1c is not None, "HbA1c should be in suggestions"
        assert hba1c["price"] == new_price, f"HbA1c price should be {new_price}, got {hba1c['price']}"
        print(f"SUCCESS: Price override reflected in recommendations: HbA1c = ₹{hba1c['price']}")
    
    def test_medicine_analyze_includes_custom_lab_tests(self):
        """POST /api/medicine/analyze should include custom lab tests in suggestions"""
        # Create custom test for Diabetes
        custom_test = {
            "name": "TEST_Medicine_Analyze_Test",
            "diseases": ["Diabetes"],
            "frequency_months": 3,
            "price": 555
        }
        requests.post(f"{BASE_URL}/api/catalog/lab-tests", json=custom_test)
        
        # Analyze a Diabetes medicine
        response = requests.post(f"{BASE_URL}/api/medicine/analyze?medicine_name=Metformin")
        assert response.status_code == 200
        result = response.json()
        
        assert "Diabetes" in result["detected_diseases"], "Metformin should detect Diabetes"
        
        lab_test_names = [t["name"] for t in result.get("suggested_lab_tests", [])]
        print(f"Lab tests suggested for Metformin: {lab_test_names}")
        
        # Custom test should be in suggestions
        assert custom_test["name"] in lab_test_names, \
            f"Custom test should appear in medicine analyze suggestions"
        print("SUCCESS: Custom test appears in medicine analyze suggestions")
    
    def test_custom_test_for_thyroid_appears_for_thyroid_patient(self):
        """Custom Thyroid test should appear for Thyroid patients"""
        # Get a Thyroid patient
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        thyroid_patient = next((p for p in patients if "Thyroid" in p.get("diseases", [])), None)
        assert thyroid_patient is not None, "Need a Thyroid patient"
        
        # Create custom test for Thyroid
        custom_test = {
            "name": "TEST_Custom_Thyroid_Panel",
            "diseases": ["Thyroid"],
            "frequency_months": 4,
            "price": 650
        }
        requests.post(f"{BASE_URL}/api/catalog/lab-tests", json=custom_test)
        
        # Get suggestions
        response = requests.get(f"{BASE_URL}/api/patients/{thyroid_patient['id']}/suggestions/lab-tests")
        assert response.status_code == 200
        suggestions = response.json()
        
        test_names = [t["name"] for t in suggestions]
        print(f"Suggestions for Thyroid patient {thyroid_patient['name']}: {test_names}")
        
        assert custom_test["name"] in test_names, \
            "Custom Thyroid test should appear for Thyroid patient"
        print("SUCCESS: Custom Thyroid test appears in Thyroid patient recommendations")
    
    def test_custom_test_with_multiple_diseases(self):
        """Custom test with multiple diseases should appear for patients with any matching disease"""
        # Create custom test for both Diabetes AND Hypertension
        custom_test = {
            "name": "TEST_Multi_Disease_Panel",
            "diseases": ["Diabetes", "Hypertension"],
            "frequency_months": 6,
            "price": 1200
        }
        requests.post(f"{BASE_URL}/api/catalog/lab-tests", json=custom_test)
        
        # Get patients
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        
        # Find Diabetes patient
        diabetes_patient = next((p for p in patients if "Diabetes" in p.get("diseases", [])), None)
        assert diabetes_patient is not None
        
        # Find Hypertension patient (preferably without Diabetes)
        hypertension_patient = next(
            (p for p in patients if "Hypertension" in p.get("diseases", [])), 
            None
        )
        assert hypertension_patient is not None
        
        # Check Diabetes patient
        response = requests.get(f"{BASE_URL}/api/patients/{diabetes_patient['id']}/suggestions/lab-tests")
        diabetes_suggestions = [t["name"] for t in response.json()]
        assert custom_test["name"] in diabetes_suggestions, \
            "Multi-disease test should appear for Diabetes patient"
        
        # Check Hypertension patient
        response = requests.get(f"{BASE_URL}/api/patients/{hypertension_patient['id']}/suggestions/lab-tests")
        hypertension_suggestions = [t["name"] for t in response.json()]
        assert custom_test["name"] in hypertension_suggestions, \
            "Multi-disease test should appear for Hypertension patient"
        
        print("SUCCESS: Multi-disease custom test appears for both Diabetes and Hypertension patients")


class TestExistingCustomLabTests:
    """Test existing custom lab tests mentioned in the bug report"""
    
    def test_existing_custom_tests_in_catalog(self):
        """Check if existing custom tests (Free T4, Triglycerides) are in catalog"""
        response = requests.get(f"{BASE_URL}/api/catalog/lab-tests")
        assert response.status_code == 200
        catalog = response.json()
        
        test_names = [t["name"] for t in catalog]
        print(f"All tests in catalog: {test_names}")
        
        # Note: These may or may not exist depending on seed state
        # Just log what we find
        free_t4 = next((t for t in catalog if "Free T4" in t["name"]), None)
        triglycerides = next((t for t in catalog if "Triglycerides" in t["name"]), None)
        
        if free_t4:
            print(f"Found Free T4: {free_t4}")
        if triglycerides:
            print(f"Found Triglycerides: {triglycerides}")


class TestPatientSuggestionsEndpoint:
    """Direct tests for /api/patients/{id}/suggestions/lab-tests endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Seed database before tests"""
        requests.post(f"{BASE_URL}/api/seed")
        yield
    
    def test_endpoint_returns_list(self):
        """Endpoint should return a list of lab tests"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        patient = patients[0] if patients else None
        assert patient is not None
        
        response = requests.get(f"{BASE_URL}/api/patients/{patient['id']}/suggestions/lab-tests")
        assert response.status_code == 200
        suggestions = response.json()
        assert isinstance(suggestions, list)
    
    def test_endpoint_returns_404_for_invalid_patient(self):
        """Endpoint should return 404 for non-existent patient"""
        response = requests.get(f"{BASE_URL}/api/patients/invalid-id-12345/suggestions/lab-tests")
        assert response.status_code == 404
    
    def test_suggestions_have_required_fields(self):
        """Each suggestion should have name, diseases, frequency_months, price"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        diabetes_patient = next((p for p in patients if "Diabetes" in p.get("diseases", [])), None)
        assert diabetes_patient is not None
        
        response = requests.get(f"{BASE_URL}/api/patients/{diabetes_patient['id']}/suggestions/lab-tests")
        suggestions = response.json()
        
        for test in suggestions:
            assert "name" in test, f"Test missing 'name': {test}"
            assert "diseases" in test, f"Test missing 'diseases': {test}"
            assert "frequency_months" in test, f"Test missing 'frequency_months': {test}"
            assert "price" in test, f"Test missing 'price': {test}"
        
        print(f"All {len(suggestions)} suggestions have required fields")
    
    def test_patient_with_no_diseases_gets_empty_suggestions(self):
        """Patient with no diseases should get empty suggestions"""
        # Create a patient with no diseases
        new_patient = {
            "name": "TEST_No_Disease_Patient",
            "email": "test@example.com",
            "phone": "+91 12345 67890"
        }
        response = requests.post(f"{BASE_URL}/api/patients", json=new_patient)
        assert response.status_code == 200
        patient = response.json()
        
        # Get suggestions
        response = requests.get(f"{BASE_URL}/api/patients/{patient['id']}/suggestions/lab-tests")
        assert response.status_code == 200
        suggestions = response.json()
        
        assert suggestions == [], "Patient with no diseases should get empty suggestions"
        print("SUCCESS: Patient with no diseases gets empty suggestions")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/patients/{patient['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
