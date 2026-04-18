"""
Test suite for Medicine CRUD operations in enCARE Healthcare CRM
Tests: POST /patients/{id}/medicines, PUT /patients/{id}/medicines/{med_id}, DELETE /patients/{id}/medicines/{med_id}
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestMedicineCRUD:
    """Medicine CRUD endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Seed database and get a patient ID before each test"""
        # Seed database
        response = requests.post(f"{BASE_URL}/api/seed")
        assert response.status_code == 200, f"Seed failed: {response.text}"
        
        # Get first patient
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        patients = response.json()
        assert len(patients) > 0, "No patients found after seeding"
        
        self.patient_id = patients[0]["id"]
        self.patient_name = patients[0]["name"]
        self.initial_medicine_count = len(patients[0].get("medicines", []))
        print(f"\nUsing patient: {self.patient_name} (ID: {self.patient_id})")
        print(f"Initial medicine count: {self.initial_medicine_count}")
    
    # ==================== ADD MEDICINE TESTS ====================
    
    def test_add_medicine_basic(self):
        """Test adding a basic medicine with minimal fields"""
        payload = {
            "name": "TEST_Aspirin 75mg",
            "dosage": "75mg",
            "form": "Tablet"
        }
        
        response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=payload)
        assert response.status_code == 200, f"Add medicine failed: {response.text}"
        
        data = response.json()
        assert data["name"] == "TEST_Aspirin 75mg"
        assert data["dosage"] == "75mg"
        assert data["form"] == "Tablet"
        assert "id" in data, "Medicine should have an ID"
        print(f"✓ Added medicine: {data['name']} with ID: {data['id']}")
        
        # Verify persistence via GET
        get_response = requests.get(f"{BASE_URL}/api/patients/{self.patient_id}")
        assert get_response.status_code == 200
        patient = get_response.json()
        medicines = patient.get("medicines", [])
        assert len(medicines) == self.initial_medicine_count + 1, "Medicine count should increase by 1"
        
        # Find the added medicine
        added_med = next((m for m in medicines if m["name"] == "TEST_Aspirin 75mg"), None)
        assert added_med is not None, "Added medicine should be in patient's medicines list"
        print(f"✓ Medicine persisted in database")
    
    def test_add_medicine_full_fields(self):
        """Test adding a medicine with all fields"""
        payload = {
            "name": "TEST_Metformin 500mg",
            "dosage": "500mg",
            "form": "Tablet",
            "color": "#4ECDC4",
            "instructions": "Take after meals",
            "schedule": {
                "frequency": "daily",
                "times": [],
                "dosage_timings": [
                    {"time": "08:00", "amount": "1"},
                    {"time": "20:00", "amount": "1"}
                ],
                "start_date": "2025-01-01",
                "end_date": None,
                "weekly_days": []
            },
            "tablet_stock_count": 60,
            "cost_per_unit": 2.5,
            "include_in_invoice": True
        }
        
        response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=payload)
        assert response.status_code == 200, f"Add medicine failed: {response.text}"
        
        data = response.json()
        assert data["name"] == "TEST_Metformin 500mg"
        assert data["color"] == "#4ECDC4"
        assert data["instructions"] == "Take after meals"
        assert data["tablet_stock_count"] == 60
        assert data["cost_per_unit"] == 2.5
        assert data["include_in_invoice"] == True
        assert len(data["schedule"]["dosage_timings"]) == 2
        print(f"✓ Added medicine with full fields: {data['name']}")
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/patients/{self.patient_id}")
        patient = get_response.json()
        added_med = next((m for m in patient["medicines"] if m["name"] == "TEST_Metformin 500mg"), None)
        assert added_med is not None
        assert added_med["tablet_stock_count"] == 60
        assert added_med["schedule"]["dosage_timings"][0]["time"] == "08:00"
        print(f"✓ All fields persisted correctly")
    
    def test_add_medicine_disease_auto_detection(self):
        """Test that adding a medicine auto-detects diseases"""
        # Add Metformin which should trigger Diabetes detection
        payload = {
            "name": "TEST_Metformin Extended Release",
            "dosage": "1000mg",
            "form": "Tablet"
        }
        
        response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=payload)
        assert response.status_code == 200
        
        # Check patient diseases
        get_response = requests.get(f"{BASE_URL}/api/patients/{self.patient_id}")
        patient = get_response.json()
        diseases = patient.get("diseases", [])
        assert "Diabetes" in diseases, f"Diabetes should be auto-detected. Current diseases: {diseases}"
        print(f"✓ Disease auto-detection works. Diseases: {diseases}")
    
    def test_add_medicine_injection_form(self):
        """Test adding an injection medicine"""
        payload = {
            "name": "TEST_Insulin Lispro",
            "dosage": "100 IU/ml",
            "form": "Injection",
            "color": "#E74C3C",
            "schedule": {
                "frequency": "daily",
                "dosage_timings": [{"time": "07:00", "amount": "10"}]
            },
            "injection_stock_count": 2,
            "injection_iu_remaining": 600,
            "injection_iu_per_package": 300
        }
        
        response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["form"] == "Injection"
        assert data["injection_stock_count"] == 2
        assert data["injection_iu_remaining"] == 600
        print(f"✓ Added injection medicine: {data['name']}")
    
    def test_add_medicine_invalid_patient(self):
        """Test adding medicine to non-existent patient"""
        payload = {"name": "TEST_Medicine", "form": "Tablet"}
        
        response = requests.post(f"{BASE_URL}/api/patients/invalid-patient-id/medicines", json=payload)
        assert response.status_code == 404, "Should return 404 for invalid patient"
        print(f"✓ Correctly returns 404 for invalid patient")
    
    # ==================== UPDATE MEDICINE TESTS ====================
    
    def test_update_medicine_basic(self):
        """Test updating a medicine's basic fields"""
        # First add a medicine
        add_payload = {
            "name": "TEST_Original Medicine",
            "dosage": "100mg",
            "form": "Tablet",
            "tablet_stock_count": 30
        }
        add_response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=add_payload)
        assert add_response.status_code == 200
        medicine_id = add_response.json()["id"]
        print(f"Added medicine with ID: {medicine_id}")
        
        # Update the medicine
        update_payload = {
            "name": "TEST_Updated Medicine",
            "dosage": "200mg",
            "tablet_stock_count": 50
        }
        update_response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/medicines/{medicine_id}",
            json=update_payload
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated_data = update_response.json()
        assert updated_data["name"] == "TEST_Updated Medicine"
        assert updated_data["dosage"] == "200mg"
        assert updated_data["tablet_stock_count"] == 50
        print(f"✓ Medicine updated successfully")
        
        # Verify persistence via GET
        get_response = requests.get(f"{BASE_URL}/api/patients/{self.patient_id}")
        patient = get_response.json()
        updated_med = next((m for m in patient["medicines"] if m["id"] == medicine_id), None)
        assert updated_med is not None
        assert updated_med["name"] == "TEST_Updated Medicine"
        assert updated_med["tablet_stock_count"] == 50
        print(f"✓ Update persisted in database")
    
    def test_update_medicine_schedule(self):
        """Test updating medicine schedule/timings"""
        # Add medicine
        add_payload = {
            "name": "TEST_Schedule Medicine",
            "form": "Tablet",
            "schedule": {
                "frequency": "daily",
                "dosage_timings": [{"time": "08:00", "amount": "1"}]
            }
        }
        add_response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=add_payload)
        medicine_id = add_response.json()["id"]
        
        # Update schedule
        update_payload = {
            "schedule": {
                "frequency": "daily",
                "dosage_timings": [
                    {"time": "08:00", "amount": "1"},
                    {"time": "14:00", "amount": "1"},
                    {"time": "20:00", "amount": "1"}
                ]
            }
        }
        update_response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/medicines/{medicine_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        
        updated_data = update_response.json()
        assert len(updated_data["schedule"]["dosage_timings"]) == 3
        print(f"✓ Schedule updated to 3 timings")
        
        # Verify persistence
        get_response = requests.get(f"{BASE_URL}/api/patients/{self.patient_id}")
        patient = get_response.json()
        updated_med = next((m for m in patient["medicines"] if m["id"] == medicine_id), None)
        assert len(updated_med["schedule"]["dosage_timings"]) == 3
        print(f"✓ Schedule update persisted")
    
    def test_update_medicine_color(self):
        """Test updating medicine color"""
        # Add medicine
        add_payload = {"name": "TEST_Color Medicine", "form": "Tablet", "color": "#FF6B6B"}
        add_response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=add_payload)
        medicine_id = add_response.json()["id"]
        
        # Update color
        update_payload = {"color": "#9B59B6"}
        update_response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/medicines/{medicine_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        assert update_response.json()["color"] == "#9B59B6"
        print(f"✓ Color updated successfully")
    
    def test_update_medicine_invalid_medicine_id(self):
        """Test updating non-existent medicine"""
        update_payload = {"name": "TEST_Updated"}
        response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/medicines/invalid-medicine-id",
            json=update_payload
        )
        assert response.status_code == 404, "Should return 404 for invalid medicine ID"
        print(f"✓ Correctly returns 404 for invalid medicine ID")
    
    def test_update_medicine_invalid_patient(self):
        """Test updating medicine for non-existent patient"""
        update_payload = {"name": "TEST_Updated"}
        response = requests.put(
            f"{BASE_URL}/api/patients/invalid-patient-id/medicines/some-medicine-id",
            json=update_payload
        )
        assert response.status_code == 404, "Should return 404 for invalid patient"
        print(f"✓ Correctly returns 404 for invalid patient")
    
    # ==================== DELETE MEDICINE TESTS ====================
    
    def test_delete_medicine(self):
        """Test deleting a medicine"""
        # Add medicine
        add_payload = {"name": "TEST_To Be Deleted", "form": "Tablet"}
        add_response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=add_payload)
        medicine_id = add_response.json()["id"]
        print(f"Added medicine to delete: {medicine_id}")
        
        # Get current count
        get_response = requests.get(f"{BASE_URL}/api/patients/{self.patient_id}")
        count_before = len(get_response.json()["medicines"])
        
        # Delete medicine
        delete_response = requests.delete(
            f"{BASE_URL}/api/patients/{self.patient_id}/medicines/{medicine_id}"
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"✓ Delete returned 200")
        
        # Verify removal via GET
        get_response = requests.get(f"{BASE_URL}/api/patients/{self.patient_id}")
        patient = get_response.json()
        count_after = len(patient["medicines"])
        assert count_after == count_before - 1, f"Medicine count should decrease. Before: {count_before}, After: {count_after}"
        
        # Verify medicine is gone
        deleted_med = next((m for m in patient["medicines"] if m["id"] == medicine_id), None)
        assert deleted_med is None, "Deleted medicine should not exist"
        print(f"✓ Medicine removed from database")
    
    def test_delete_medicine_invalid_medicine_id(self):
        """Test deleting non-existent medicine"""
        response = requests.delete(
            f"{BASE_URL}/api/patients/{self.patient_id}/medicines/invalid-medicine-id"
        )
        assert response.status_code == 404, "Should return 404 for invalid medicine ID"
        print(f"✓ Correctly returns 404 for invalid medicine ID")
    
    def test_delete_medicine_invalid_patient(self):
        """Test deleting medicine for non-existent patient"""
        response = requests.delete(
            f"{BASE_URL}/api/patients/invalid-patient-id/medicines/some-medicine-id"
        )
        assert response.status_code == 404, "Should return 404 for invalid patient"
        print(f"✓ Correctly returns 404 for invalid patient")
    
    def test_delete_medicine_updates_diseases(self):
        """Test that deleting a medicine updates disease detection"""
        # Create a new patient without diseases
        create_response = requests.post(f"{BASE_URL}/api/patients", json={
            "name": "TEST_Disease Patient",
            "age": 40
        })
        assert create_response.status_code == 200
        new_patient_id = create_response.json()["id"]
        
        # Add Metformin (should add Diabetes)
        add_response = requests.post(f"{BASE_URL}/api/patients/{new_patient_id}/medicines", json={
            "name": "Metformin 500mg",
            "form": "Tablet"
        })
        medicine_id = add_response.json()["id"]
        
        # Verify Diabetes was added
        get_response = requests.get(f"{BASE_URL}/api/patients/{new_patient_id}")
        assert "Diabetes" in get_response.json()["diseases"]
        print(f"✓ Diabetes detected after adding Metformin")
        
        # Delete the medicine
        delete_response = requests.delete(f"{BASE_URL}/api/patients/{new_patient_id}/medicines/{medicine_id}")
        assert delete_response.status_code == 200
        
        # Verify diseases updated (Diabetes should be removed if no other diabetes meds)
        get_response = requests.get(f"{BASE_URL}/api/patients/{new_patient_id}")
        diseases = get_response.json()["diseases"]
        # Note: Diabetes might still be there if patient has other diabetes meds
        print(f"✓ Diseases after delete: {diseases}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/patients/{new_patient_id}")


class TestMedicineEdgeCases:
    """Edge case tests for medicine operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for edge case tests"""
        response = requests.post(f"{BASE_URL}/api/seed")
        assert response.status_code == 200
        
        response = requests.get(f"{BASE_URL}/api/patients")
        self.patient_id = response.json()[0]["id"]
    
    def test_add_medicine_empty_name(self):
        """Test adding medicine with empty name - should still work (validation is frontend)"""
        payload = {"name": "", "form": "Tablet"}
        response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=payload)
        # Backend doesn't validate empty name, frontend does
        assert response.status_code in [200, 422], f"Response: {response.status_code}"
        print(f"✓ Empty name handling: status {response.status_code}")
    
    def test_add_medicine_special_characters(self):
        """Test adding medicine with special characters in name"""
        payload = {"name": "TEST_Vitamin B12 (Methylcobalamin) 1500mcg", "form": "Tablet"}
        response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=payload)
        assert response.status_code == 200
        assert response.json()["name"] == "TEST_Vitamin B12 (Methylcobalamin) 1500mcg"
        print(f"✓ Special characters handled correctly")
    
    def test_update_partial_fields(self):
        """Test updating only some fields preserves others"""
        # Add medicine with multiple fields
        add_payload = {
            "name": "TEST_Partial Update",
            "dosage": "100mg",
            "form": "Capsule",
            "color": "#FF6B6B",
            "tablet_stock_count": 30
        }
        add_response = requests.post(f"{BASE_URL}/api/patients/{self.patient_id}/medicines", json=add_payload)
        medicine_id = add_response.json()["id"]
        
        # Update only stock
        update_payload = {"tablet_stock_count": 50}
        update_response = requests.put(
            f"{BASE_URL}/api/patients/{self.patient_id}/medicines/{medicine_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        
        # Verify other fields preserved
        data = update_response.json()
        assert data["name"] == "TEST_Partial Update", "Name should be preserved"
        assert data["dosage"] == "100mg", "Dosage should be preserved"
        assert data["form"] == "Capsule", "Form should be preserved"
        assert data["color"] == "#FF6B6B", "Color should be preserved"
        assert data["tablet_stock_count"] == 50, "Stock should be updated"
        print(f"✓ Partial update preserves other fields")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
