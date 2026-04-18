"""
Test cases for patient priority_reason feature.
Tests that GET /api/patients returns priority_reason field with appropriate reasons.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPriorityReason:
    """Tests for priority_reason field in patient API responses"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Seed data before tests"""
        response = requests.post(f"{BASE_URL}/api/seed")
        assert response.status_code == 200
    
    def test_patients_have_priority_reason_field(self):
        """Test that all patients have priority_reason field"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        
        patients = response.json()
        assert len(patients) > 0, "Should have patients after seeding"
        
        for patient in patients:
            assert "priority_reason" in patient, f"Patient {patient['name']} missing priority_reason"
            assert isinstance(patient["priority_reason"], str), "priority_reason should be a string"
            assert len(patient["priority_reason"]) > 0, f"Patient {patient['name']} has empty priority_reason"
    
    def test_high_priority_patients_have_specific_reasons(self):
        """Test that high priority patients have specific reasons (not generic)"""
        response = requests.get(f"{BASE_URL}/api/patients?priority=high")
        assert response.status_code == 200
        
        patients = response.json()
        for patient in patients:
            reason = patient.get("priority_reason", "")
            # High priority should have specific reasons, not just "Marked as high priority"
            # Check for at least one specific condition
            has_specific_reason = any([
                "running low" in reason.lower(),
                "critically low" in reason.lower(),
                "low adherence" in reason.lower(),
                "doctor visit overdue" in reason.lower(),
                "multiple conditions" in reason.lower()
            ])
            assert has_specific_reason, f"High priority patient {patient['name']} should have specific reason, got: {reason}"
    
    def test_priority_reason_includes_medicine_stock_info(self):
        """Test that patients with low medicine stock have it mentioned in reason"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        
        patients = response.json()
        patients_with_low_stock = []
        
        for patient in patients:
            for med in patient.get("medicines", []):
                stock_status = med.get("stock_status", {})
                if stock_status.get("is_low"):
                    patients_with_low_stock.append({
                        "name": patient["name"],
                        "medicine": med["name"],
                        "reason": patient.get("priority_reason", "")
                    })
        
        # Verify at least some patients have low stock mentioned
        for p in patients_with_low_stock:
            assert "running low" in p["reason"].lower() or "critically low" in p["reason"].lower(), \
                f"Patient {p['name']} has low stock for {p['medicine']} but reason doesn't mention it: {p['reason']}"
    
    def test_priority_reason_includes_adherence_info(self):
        """Test that patients with low adherence (<70%) have it mentioned in reason"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        
        patients = response.json()
        low_adherence_patients = [p for p in patients if p.get("adherence_rate", 100) < 70]
        
        for patient in low_adherence_patients:
            reason = patient.get("priority_reason", "")
            assert "adherence" in reason.lower(), \
                f"Patient {patient['name']} has low adherence ({patient['adherence_rate']}%) but reason doesn't mention it: {reason}"
    
    def test_priority_reason_includes_doctor_visit_overdue(self):
        """Test that patients with overdue doctor visits have it mentioned"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        
        patients = response.json()
        # After seeding, most patients should have overdue visits (4-5 months ago)
        patients_with_overdue = [p for p in patients if "doctor visit overdue" in p.get("priority_reason", "").lower()]
        
        # Should have at least some patients with overdue visits
        assert len(patients_with_overdue) > 0, "Should have patients with overdue doctor visits after seeding"
    
    def test_priority_reason_includes_multiple_conditions(self):
        """Test that patients with 3+ diseases have it mentioned"""
        response = requests.get(f"{BASE_URL}/api/patients")
        assert response.status_code == 200
        
        patients = response.json()
        patients_with_multiple = [p for p in patients if len(p.get("diseases", [])) >= 3]
        
        for patient in patients_with_multiple:
            reason = patient.get("priority_reason", "")
            assert "multiple conditions" in reason.lower(), \
                f"Patient {patient['name']} has {len(patient['diseases'])} diseases but reason doesn't mention it: {reason}"
    
    def test_normal_priority_patients_have_reasons(self):
        """Test that normal priority patients also have appropriate reasons"""
        response = requests.get(f"{BASE_URL}/api/patients?priority=normal")
        assert response.status_code == 200
        
        patients = response.json()
        for patient in patients:
            reason = patient.get("priority_reason", "")
            assert len(reason) > 0, f"Normal priority patient {patient['name']} should have a reason"
            # Normal priority can have specific reasons or generic "Standard care plan"
    
    def test_low_priority_patients_have_reasons(self):
        """Test that low priority patients have appropriate reasons"""
        response = requests.get(f"{BASE_URL}/api/patients?priority=low")
        assert response.status_code == 200
        
        patients = response.json()
        for patient in patients:
            reason = patient.get("priority_reason", "")
            assert len(reason) > 0, f"Low priority patient {patient['name']} should have a reason"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
