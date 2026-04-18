"""
enCARE Healthcare CRM Backend API Tests
Tests for: Dashboard, Patients, Vitals, Medicines, Lab Tests, Interactions, Opportunities
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndSeed:
    """Health check and seed data tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "enCARE" in data["message"]
        print(f"✓ API root working: {data['message']}")
    
    def test_seed_database(self):
        """Test database seeding with 10 patients"""
        response = requests.post(f"{BASE_URL}/api/seed")
        assert response.status_code == 200
        data = response.json()
        assert "10 patients" in data.get("message", "")
        print(f"✓ Database seeded: {data['message']}")


class TestDashboard:
    """Dashboard stats and patients-to-call tests"""
    
    def test_dashboard_stats(self):
        """Test dashboard stats returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "total_patients" in data
        assert "high_priority_patients" in data
        assert "opportunities" in data
        assert "expected_revenue" in data
        assert "total_monthly_invoice" in data
        
        # Verify patient count
        assert data["total_patients"] == 10, f"Expected 10 patients, got {data['total_patients']}"
        
        # Verify opportunities structure
        opps = data["opportunities"]
        assert "refills" in opps
        assert "lab_tests" in opps
        assert "products" in opps
        assert "invoices" in opps
        assert "adherence" in opps
        
        print(f"✓ Dashboard stats: {data['total_patients']} patients, {data['high_priority_patients']} high priority")
        print(f"  Opportunities: refills={opps['refills']}, lab_tests={opps['lab_tests']}, products={opps['products']}, invoices={opps['invoices']}, adherence={opps['adherence']}")
    
    def test_dashboard_high_priority_count(self):
        """Test that high priority count is 3"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["high_priority_patients"] == 3, f"Expected 3 high priority, got {data['high_priority_patients']}"
        print(f"✓ High priority patients: {data['high_priority_patients']}")
    
    def test_patients_to_call(self):
        """Test patients to call endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/patients-to-call")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Patients to call: {len(data)} patients")


class TestPatients:
    """Patient CRUD and listing tests"""
    
    def test_get_all_patients(self):
        """Test getting all patients returns 10 patients"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        patients = response.json()
        assert len(patients) == 10, f"Expected 10 patients, got {len(patients)}"
        print(f"✓ Got {len(patients)} patients")
    
    def test_patient_has_correct_fields(self):
        """Test patient has sex (not gender), city, state fields"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        patients = response.json()
        
        patient = patients[0]
        # Check for sex field (not gender)
        assert "sex" in patient, "Patient should have 'sex' field"
        assert "gender" not in patient, "Patient should NOT have 'gender' field"
        
        # Check for city/state
        assert "city" in patient, "Patient should have 'city' field"
        assert "state" in patient, "Patient should have 'state' field"
        
        # Check for diseases and adherence_rate
        assert "diseases" in patient
        assert "adherence_rate" in patient
        
        print(f"✓ Patient fields correct: sex={patient.get('sex')}, city={patient.get('city')}, state={patient.get('state')}")
    
    def test_patient_has_picture_field(self):
        """Test patient has picture field (not avatar_url)"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        patients = response.json()
        
        patient = patients[0]
        assert "picture" in patient, "Patient should have 'picture' field"
        assert "avatar_url" not in patient, "Patient should NOT have 'avatar_url' field"
        print(f"✓ Patient has picture field: {patient.get('picture', '')[:50]}...")
    
    def test_get_single_patient(self):
        """Test getting a single patient by ID"""
        # First get all patients to get an ID
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        patient_id = patients[0]["id"]
        
        # Get single patient
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}")
        assert response.status_code == 200
        patient = response.json()
        
        # Verify patient detail includes vitals collections
        assert "blood_glucose" in patient, "Patient detail should include blood_glucose"
        assert "blood_pressure" in patient, "Patient detail should include blood_pressure"
        assert "body_metrics" in patient, "Patient detail should include body_metrics"
        assert "lab_tests" in patient, "Patient detail should include lab_tests"
        
        print(f"✓ Got patient: {patient['name']}")
        print(f"  Vitals: BP readings={len(patient.get('blood_pressure', []))}, Glucose readings={len(patient.get('blood_glucose', []))}")
    
    def test_patient_medicines_have_correct_structure(self):
        """Test medicines have form, color, dosage_timings, stock_status"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        
        # Find a patient with medicines
        patient_with_meds = None
        for p in patients:
            if p.get("medicines") and len(p["medicines"]) > 0:
                patient_with_meds = p
                break
        
        assert patient_with_meds is not None, "Should have at least one patient with medicines"
        
        med = patient_with_meds["medicines"][0]
        assert "form" in med, "Medicine should have 'form' field"
        assert "color" in med, "Medicine should have 'color' field"
        assert "schedule" in med, "Medicine should have 'schedule' field"
        assert "stock_status" in med, "Medicine should have 'stock_status' field"
        
        # Check schedule has dosage_timings
        schedule = med.get("schedule", {})
        assert "dosage_timings" in schedule, "Schedule should have 'dosage_timings'"
        
        print(f"✓ Medicine structure correct: {med['name']}, form={med['form']}, color={med['color']}")
        print(f"  Dosage timings: {schedule.get('dosage_timings', [])}")
    
    def test_create_patient_with_sex_city_state(self):
        """Test creating a patient with sex, city, state fields"""
        new_patient = {
            "name": "TEST_New Patient",
            "age": 45,
            "sex": "Female",
            "phone": "+91 99999 00000",
            "city": "Mumbai",
            "state": "Maharashtra"
        }
        
        response = requests.post(f"{BASE_URL}/api/patients", json=new_patient)
        assert response.status_code == 200
        created = response.json()
        
        assert created["name"] == new_patient["name"]
        assert created["sex"] == new_patient["sex"]
        assert created["city"] == new_patient["city"]
        assert created["state"] == new_patient["state"]
        
        print(f"✓ Created patient: {created['name']}, sex={created['sex']}, city={created['city']}")
        
        # Cleanup - delete the test patient
        requests.delete(f"{BASE_URL}/api/patients/{created['id']}")
    
    def test_search_patients(self):
        """Test patient search functionality"""
        response = requests.get(f"{BASE_URL}/api/patients", params={"search": "Rajesh"})
        assert response.status_code == 200
        patients = response.json()
        assert len(patients) >= 1, "Should find at least one patient named Rajesh"
        print(f"✓ Search found {len(patients)} patients matching 'Rajesh'")
    
    def test_filter_by_priority(self):
        """Test filtering patients by priority"""
        response = requests.get(f"{BASE_URL}/api/patients", params={"priority": "high"})
        assert response.status_code == 200
        patients = response.json()
        assert len(patients) == 3, f"Expected 3 high priority patients, got {len(patients)}"
        for p in patients:
            assert p["priority"] == "high"
        print(f"✓ Priority filter: {len(patients)} high priority patients")


class TestMedicineRefill:
    """Medicine refill API tests"""
    
    def test_refill_medicine_tablet(self):
        """Test refilling a tablet medicine"""
        # Get a patient with medicines
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        
        patient_with_meds = None
        med_index = 0
        for p in patients:
            if p.get("medicines") and len(p["medicines"]) > 0:
                for i, med in enumerate(p["medicines"]):
                    if med.get("form", "").lower() == "tablet":
                        patient_with_meds = p
                        med_index = i
                        break
            if patient_with_meds:
                break
        
        assert patient_with_meds is not None, "Should have a patient with tablet medicines"
        
        patient_id = patient_with_meds["id"]
        original_stock = patient_with_meds["medicines"][med_index].get("tablet_stock_count", 0)
        
        # Refill medicine using PUT
        response = requests.put(
            f"{BASE_URL}/api/patients/{patient_id}/medicines/{med_index}/refill",
            params={"quantity": 30}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "refilled" in data["message"].lower()
        
        # Verify stock increased
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}")
        updated_patient = response.json()
        new_stock = updated_patient["medicines"][med_index].get("tablet_stock_count", 0)
        assert new_stock == original_stock + 30, f"Stock should increase by 30, was {original_stock}, now {new_stock}"
        
        print(f"✓ Refilled medicine: stock {original_stock} -> {new_stock}")


class TestVitals:
    """Vitals recording tests"""
    
    def test_add_bp_vital(self):
        """Test adding blood pressure vital"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patient_id = response.json()[0]["id"]
        
        vital_data = {
            "type": "bp",
            "systolic": 125,
            "diastolic": 82
        }
        
        response = requests.post(f"{BASE_URL}/api/patients/{patient_id}/vitals", json=vital_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["systolic"] == 125
        assert data["diastolic"] == 82
        assert data["user_id"] == patient_id
        
        print(f"✓ Added BP vital: {data['systolic']}/{data['diastolic']} mmHg")
    
    def test_add_sugar_vital(self):
        """Test adding blood sugar vital"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patient_id = response.json()[0]["id"]
        
        vital_data = {
            "type": "sugar",
            "value": 145,
            "meal_context": "After Lunch"
        }
        
        response = requests.post(f"{BASE_URL}/api/patients/{patient_id}/vitals", json=vital_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["value"] == 145
        assert data["meal_context"] == "After Lunch"
        
        print(f"✓ Added sugar vital: {data['value']} mg/dL ({data['meal_context']})")
    
    def test_add_weight_vital(self):
        """Test adding weight/body metrics vital"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patient_id = response.json()[0]["id"]
        
        vital_data = {
            "type": "weight",
            "value": 72.5,
            "height": 170
        }
        
        response = requests.post(f"{BASE_URL}/api/patients/{patient_id}/vitals", json=vital_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["weight"] == 72.5
        assert "bmi" in data
        
        print(f"✓ Added weight vital: {data['weight']} kg, BMI={data['bmi']}")
    
    def test_get_patient_vitals(self):
        """Test getting patient vitals"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patient_id = response.json()[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}/vitals")
        assert response.status_code == 200
        data = response.json()
        
        assert "blood_glucose" in data
        assert "blood_pressure" in data
        assert "body_metrics" in data
        
        print(f"✓ Got vitals: BP={len(data['blood_pressure'])}, Glucose={len(data['blood_glucose'])}, Metrics={len(data['body_metrics'])}")


class TestLabTests:
    """Lab test booking tests"""
    
    def test_book_lab_test(self):
        """Test booking a lab test"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patient_id = response.json()[0]["id"]
        
        booking_data = {
            "test_name": "HbA1c",
            "booked_date": (datetime.now() + timedelta(days=3)).isoformat(),
            "price": 450
        }
        
        response = requests.post(f"{BASE_URL}/api/patients/{patient_id}/lab-tests/book", json=booking_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["test_name"] == "HbA1c"
        assert data["status"] == "booked"
        assert data["patient_id"] == patient_id
        
        print(f"✓ Booked lab test: {data['test_name']}, status={data['status']}")
    
    def test_get_lab_tests(self):
        """Test getting lab tests for a patient"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patient_id = response.json()[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}/lab-tests")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        print(f"✓ Got {len(data)} lab tests for patient")


class TestInteractions:
    """Interaction logging tests"""
    
    def test_log_interaction(self):
        """Test logging an interaction"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patient_id = response.json()[0]["id"]
        
        interaction_data = {
            "type": "call",
            "notes": "Discussed medicine refill schedule",
            "outcome": "positive",
            "follow_up_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        }
        
        response = requests.post(f"{BASE_URL}/api/patients/{patient_id}/interactions", json=interaction_data)
        assert response.status_code == 200
        data = response.json()
        
        assert data["type"] == "call"
        assert data["outcome"] == "positive"
        
        print(f"✓ Logged interaction: {data['type']}, outcome={data['outcome']}")
    
    def test_get_interactions(self):
        """Test getting interactions for a patient"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patient_id = response.json()[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}/interactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        print(f"✓ Got {len(data)} interactions for patient")


class TestSuggestions:
    """Product and lab test suggestions tests"""
    
    def test_get_product_suggestions(self):
        """Test getting product suggestions based on diseases"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        
        # Find a patient with diseases
        patient_with_diseases = None
        for p in patients:
            if p.get("diseases") and len(p["diseases"]) > 0:
                patient_with_diseases = p
                break
        
        assert patient_with_diseases is not None
        
        response = requests.get(f"{BASE_URL}/api/patients/{patient_with_diseases['id']}/suggestions/products")
        assert response.status_code == 200
        products = response.json()
        
        assert isinstance(products, list)
        if len(products) > 0:
            assert "name" in products[0]
            assert "price" in products[0]
            assert "disease" in products[0]
        
        print(f"✓ Got {len(products)} product suggestions for patient with diseases: {patient_with_diseases['diseases']}")
    
    def test_get_lab_test_suggestions(self):
        """Test getting lab test suggestions based on diseases"""
        response = requests.get(f"{BASE_URL}/api/patients")
        patients = response.json()
        
        patient_with_diseases = None
        for p in patients:
            if p.get("diseases") and len(p["diseases"]) > 0:
                patient_with_diseases = p
                break
        
        assert patient_with_diseases is not None
        
        response = requests.get(f"{BASE_URL}/api/patients/{patient_with_diseases['id']}/suggestions/lab-tests")
        assert response.status_code == 200
        tests = response.json()
        
        assert isinstance(tests, list)
        if len(tests) > 0:
            assert "name" in tests[0]
            assert "price" in tests[0]
        
        print(f"✓ Got {len(tests)} lab test suggestions")


class TestOpportunities:
    """Opportunities generation and management tests"""
    
    def test_generate_opportunities(self):
        """Test generating opportunities"""
        response = requests.post(f"{BASE_URL}/api/opportunities/generate")
        assert response.status_code == 200
        data = response.json()
        assert "generated" in data
        print(f"✓ Generated {data['generated']} opportunities")
    
    def test_get_opportunities(self):
        """Test getting opportunities"""
        response = requests.get(f"{BASE_URL}/api/opportunities")
        assert response.status_code == 200
        opportunities = response.json()
        assert isinstance(opportunities, list)
        
        # Check opportunity structure
        if len(opportunities) > 0:
            opp = opportunities[0]
            assert "type" in opp
            assert "patient_id" in opp
            assert "patient_name" in opp
            assert "description" in opp
            assert "priority" in opp
        
        print(f"✓ Got {len(opportunities)} opportunities")
    
    def test_filter_opportunities_by_type(self):
        """Test filtering opportunities by type"""
        response = requests.get(f"{BASE_URL}/api/opportunities", params={"opportunity_type": "refill"})
        assert response.status_code == 200
        opportunities = response.json()
        
        for opp in opportunities:
            assert opp["type"] == "refill"
        
        print(f"✓ Filtered to {len(opportunities)} refill opportunities")


class TestCatalogs:
    """Product and lab test catalog tests"""
    
    def test_get_product_catalog(self):
        """Test getting product catalog"""
        response = requests.get(f"{BASE_URL}/api/catalog/products")
        assert response.status_code == 200
        catalog = response.json()
        
        assert isinstance(catalog, dict)
        assert "Diabetes" in catalog
        assert "Hypertension" in catalog
        
        print(f"✓ Got product catalog with {len(catalog)} disease categories")
    
    def test_get_lab_test_catalog(self):
        """Test getting lab test catalog"""
        response = requests.get(f"{BASE_URL}/api/catalog/lab-tests")
        assert response.status_code == 200
        catalog = response.json()
        
        assert isinstance(catalog, list)
        assert len(catalog) > 0
        assert "name" in catalog[0]
        assert "price" in catalog[0]
        
        print(f"✓ Got lab test catalog with {len(catalog)} tests")


class TestDeletePatient:
    """Patient deletion tests"""
    
    def test_delete_patient(self):
        """Test deleting a patient"""
        # Create a test patient first
        new_patient = {
            "name": "TEST_Delete Patient",
            "age": 50,
            "sex": "Male",
            "phone": "+91 88888 00000"
        }
        
        response = requests.post(f"{BASE_URL}/api/patients", json=new_patient)
        assert response.status_code == 200
        created = response.json()
        patient_id = created["id"]
        
        # Delete the patient
        response = requests.delete(f"{BASE_URL}/api/patients/{patient_id}")
        assert response.status_code == 200
        
        # Verify patient is deleted
        response = requests.get(f"{BASE_URL}/api/patients/{patient_id}")
        assert response.status_code == 404
        
        print(f"✓ Deleted patient and verified 404 on GET")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
