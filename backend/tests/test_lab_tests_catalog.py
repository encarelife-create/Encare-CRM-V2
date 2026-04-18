"""
Test Lab Tests Catalog and Laboratories CRUD endpoints
Features tested:
- GET /api/catalog/lab-tests - Get all lab tests (built-in + custom)
- POST /api/catalog/lab-tests - Add custom lab test
- PUT /api/catalog/lab-tests/{name}/price - Update price for any test
- PUT /api/catalog/lab-tests/{id} - Update custom lab test
- DELETE /api/catalog/lab-tests/{id} - Delete custom lab test
- GET /api/laboratories - Get all laboratories
- POST /api/laboratories - Add laboratory
- PUT /api/laboratories/{id} - Update laboratory
- DELETE /api/laboratories/{id} - Delete laboratory
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module", autouse=True)
def seed_database(api_client):
    """Seed database before tests to ensure clean state"""
    response = api_client.post(f"{BASE_URL}/api/seed")
    assert response.status_code == 200, f"Seed failed: {response.text}"
    time.sleep(0.5)  # Allow DB to settle
    yield
    # Cleanup after all tests
    api_client.post(f"{BASE_URL}/api/seed")


class TestLabTestCatalogGet:
    """Test GET /api/catalog/lab-tests"""
    
    def test_get_lab_tests_returns_list(self, api_client):
        """GET /api/catalog/lab-tests returns a list of tests"""
        response = api_client.get(f"{BASE_URL}/api/catalog/lab-tests")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"Found {len(data)} lab tests")
    
    def test_lab_tests_have_required_fields(self, api_client):
        """Each lab test has name, diseases, frequency_months, price, source"""
        response = api_client.get(f"{BASE_URL}/api/catalog/lab-tests")
        assert response.status_code == 200
        data = response.json()
        
        for test in data:
            assert "name" in test, f"Test missing 'name': {test}"
            assert "diseases" in test, f"Test missing 'diseases': {test}"
            assert "frequency_months" in test, f"Test missing 'frequency_months': {test}"
            assert "price" in test, f"Test missing 'price': {test}"
            assert "source" in test, f"Test missing 'source': {test}"
            assert test["source"] in ["auto", "custom"], f"Invalid source: {test['source']}"
    
    def test_built_in_tests_have_source_auto(self, api_client):
        """Built-in tests (HbA1c, Lipid Profile, etc.) have source='auto'"""
        response = api_client.get(f"{BASE_URL}/api/catalog/lab-tests")
        assert response.status_code == 200
        data = response.json()
        
        # Check known built-in tests
        built_in_names = ["HbA1c", "Fasting Blood Sugar", "Lipid Profile"]
        for name in built_in_names:
            test = next((t for t in data if t["name"] == name), None)
            assert test is not None, f"Built-in test '{name}' not found"
            assert test["source"] == "auto", f"Built-in test '{name}' should have source='auto'"


class TestCustomLabTestCRUD:
    """Test custom lab test CRUD operations"""
    
    def test_add_custom_lab_test(self, api_client):
        """POST /api/catalog/lab-tests adds a custom test"""
        payload = {
            "name": "TEST_Vitamin B12",
            "diseases": ["Elderly Care", "Diabetes"],
            "frequency_months": 6,
            "price": 850
        }
        response = api_client.post(f"{BASE_URL}/api/catalog/lab-tests", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_Vitamin B12"
        assert data["diseases"] == ["Elderly Care", "Diabetes"]
        assert data["frequency_months"] == 6
        assert data["price"] == 850
        assert "id" in data
        print(f"Created custom test with ID: {data['id']}")
    
    def test_custom_test_appears_in_catalog(self, api_client):
        """Custom test appears in GET /api/catalog/lab-tests with source='custom'"""
        # First add a test
        payload = {
            "name": "TEST_Iron Studies",
            "diseases": ["Elderly Care"],
            "frequency_months": 12,
            "price": 600
        }
        create_response = api_client.post(f"{BASE_URL}/api/catalog/lab-tests", json=payload)
        assert create_response.status_code == 200
        
        # Verify it appears in catalog
        response = api_client.get(f"{BASE_URL}/api/catalog/lab-tests")
        assert response.status_code == 200
        data = response.json()
        
        test = next((t for t in data if t["name"] == "TEST_Iron Studies"), None)
        assert test is not None, "Custom test not found in catalog"
        assert test["source"] == "custom"
        assert test["price"] == 600
    
    def test_update_custom_lab_test(self, api_client):
        """PUT /api/catalog/lab-tests/{id} updates a custom test"""
        # First create a test
        payload = {
            "name": "TEST_Calcium",
            "diseases": ["Arthritis"],
            "frequency_months": 6,
            "price": 300
        }
        create_response = api_client.post(f"{BASE_URL}/api/catalog/lab-tests", json=payload)
        assert create_response.status_code == 200
        test_id = create_response.json()["id"]
        
        # Update the test
        update_payload = {
            "name": "TEST_Calcium Updated",
            "diseases": ["Arthritis", "Elderly Care"],
            "frequency_months": 3,
            "price": 350
        }
        update_response = api_client.put(f"{BASE_URL}/api/catalog/lab-tests/{test_id}", json=update_payload)
        assert update_response.status_code == 200
        
        # Verify update in catalog
        response = api_client.get(f"{BASE_URL}/api/catalog/lab-tests")
        data = response.json()
        # Filter only custom tests (which have 'id' field)
        test = next((t for t in data if t.get("id") == test_id), None)
        assert test is not None
        assert test["name"] == "TEST_Calcium Updated"
        assert "Elderly Care" in test["diseases"]
        assert test["frequency_months"] == 3
        assert test["price"] == 350
    
    def test_delete_custom_lab_test(self, api_client):
        """DELETE /api/catalog/lab-tests/{id} removes a custom test"""
        # First create a test
        payload = {
            "name": "TEST_To Delete",
            "diseases": ["Diabetes"],
            "frequency_months": 6,
            "price": 200
        }
        create_response = api_client.post(f"{BASE_URL}/api/catalog/lab-tests", json=payload)
        assert create_response.status_code == 200
        test_id = create_response.json()["id"]
        
        # Delete the test
        delete_response = api_client.delete(f"{BASE_URL}/api/catalog/lab-tests/{test_id}")
        assert delete_response.status_code == 200
        
        # Verify it's gone from catalog
        response = api_client.get(f"{BASE_URL}/api/catalog/lab-tests")
        data = response.json()
        # Filter only custom tests (which have 'id' field)
        test = next((t for t in data if t.get("id") == test_id), None)
        assert test is None, "Deleted test still appears in catalog"
    
    def test_delete_nonexistent_test_returns_404(self, api_client):
        """DELETE /api/catalog/lab-tests/{id} returns 404 for invalid ID"""
        response = api_client.delete(f"{BASE_URL}/api/catalog/lab-tests/nonexistent-id-12345")
        assert response.status_code == 404
    
    def test_update_nonexistent_test_returns_404(self, api_client):
        """PUT /api/catalog/lab-tests/{id} returns 404 for invalid ID"""
        response = api_client.put(
            f"{BASE_URL}/api/catalog/lab-tests/nonexistent-id-12345",
            json={"name": "Test", "price": 100}
        )
        assert response.status_code == 404


class TestLabTestPriceUpdate:
    """Test price update for both built-in and custom tests"""
    
    def test_update_builtin_test_price(self, api_client):
        """PUT /api/catalog/lab-tests/{name}/price updates built-in test price via override"""
        # Update HbA1c price (built-in test)
        response = api_client.put(
            f"{BASE_URL}/api/catalog/lab-tests/HbA1c/price",
            json={"price": 500}
        )
        assert response.status_code == 200
        
        # Verify price updated in catalog
        catalog_response = api_client.get(f"{BASE_URL}/api/catalog/lab-tests")
        data = catalog_response.json()
        test = next((t for t in data if t["name"] == "HbA1c"), None)
        assert test is not None
        assert test["price"] == 500
        assert test["source"] == "auto"  # Still auto, just price overridden
    
    def test_update_custom_test_price_via_name(self, api_client):
        """PUT /api/catalog/lab-tests/{name}/price updates custom test price"""
        # First create a custom test
        payload = {
            "name": "TEST_Price Update Test",
            "diseases": ["Diabetes"],
            "frequency_months": 6,
            "price": 100
        }
        create_response = api_client.post(f"{BASE_URL}/api/catalog/lab-tests", json=payload)
        assert create_response.status_code == 200
        
        # Update price via name endpoint
        response = api_client.put(
            f"{BASE_URL}/api/catalog/lab-tests/TEST_Price Update Test/price",
            json={"price": 150}
        )
        assert response.status_code == 200
        
        # Verify price updated
        catalog_response = api_client.get(f"{BASE_URL}/api/catalog/lab-tests")
        data = catalog_response.json()
        test = next((t for t in data if t["name"] == "TEST_Price Update Test"), None)
        assert test is not None
        assert test["price"] == 150
    
    def test_update_price_missing_price_returns_400(self, api_client):
        """PUT /api/catalog/lab-tests/{name}/price returns 400 if price missing"""
        response = api_client.put(
            f"{BASE_URL}/api/catalog/lab-tests/HbA1c/price",
            json={}
        )
        assert response.status_code == 400
    
    def test_update_price_nonexistent_test_returns_404(self, api_client):
        """PUT /api/catalog/lab-tests/{name}/price returns 404 for unknown test"""
        response = api_client.put(
            f"{BASE_URL}/api/catalog/lab-tests/NonExistentTest12345/price",
            json={"price": 100}
        )
        assert response.status_code == 404


class TestLaboratoriesCRUD:
    """Test Laboratories CRUD operations"""
    
    def test_get_laboratories_returns_list(self, api_client):
        """GET /api/laboratories returns a list"""
        response = api_client.get(f"{BASE_URL}/api/laboratories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_add_laboratory(self, api_client):
        """POST /api/laboratories adds a new laboratory"""
        payload = {
            "name": "TEST_Apollo Diagnostics",
            "address": "123 MG Road",
            "city": "Bangalore",
            "state": "Karnataka",
            "pincode": "560001",
            "phone": "+91 98765 43210",
            "email": "apollo@test.com",
            "notes": "Open 24x7, home collection available"
        }
        response = api_client.post(f"{BASE_URL}/api/laboratories", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_Apollo Diagnostics"
        assert data["address"] == "123 MG Road"
        assert data["city"] == "Bangalore"
        assert data["state"] == "Karnataka"
        assert data["pincode"] == "560001"
        assert data["phone"] == "+91 98765 43210"
        assert data["email"] == "apollo@test.com"
        assert data["notes"] == "Open 24x7, home collection available"
        assert "id" in data
        print(f"Created laboratory with ID: {data['id']}")
    
    def test_laboratory_appears_in_list(self, api_client):
        """Added laboratory appears in GET /api/laboratories"""
        # First add a lab
        payload = {
            "name": "TEST_SRL Diagnostics",
            "city": "Mumbai",
            "phone": "+91 12345 67890"
        }
        create_response = api_client.post(f"{BASE_URL}/api/laboratories", json=payload)
        assert create_response.status_code == 200
        lab_id = create_response.json()["id"]
        
        # Verify it appears in list
        response = api_client.get(f"{BASE_URL}/api/laboratories")
        assert response.status_code == 200
        data = response.json()
        
        lab = next((l for l in data if l["id"] == lab_id), None)
        assert lab is not None, "Laboratory not found in list"
        assert lab["name"] == "TEST_SRL Diagnostics"
        assert lab["city"] == "Mumbai"
    
    def test_update_laboratory(self, api_client):
        """PUT /api/laboratories/{id} updates a laboratory"""
        # First create a lab
        payload = {
            "name": "TEST_Lab to Update",
            "city": "Delhi"
        }
        create_response = api_client.post(f"{BASE_URL}/api/laboratories", json=payload)
        assert create_response.status_code == 200
        lab_id = create_response.json()["id"]
        
        # Update the lab
        update_payload = {
            "name": "TEST_Lab Updated",
            "city": "New Delhi",
            "phone": "+91 11111 22222",
            "notes": "Updated notes"
        }
        update_response = api_client.put(f"{BASE_URL}/api/laboratories/{lab_id}", json=update_payload)
        assert update_response.status_code == 200
        
        # Verify update
        response = api_client.get(f"{BASE_URL}/api/laboratories")
        data = response.json()
        lab = next((l for l in data if l["id"] == lab_id), None)
        assert lab is not None
        assert lab["name"] == "TEST_Lab Updated"
        assert lab["city"] == "New Delhi"
        assert lab["phone"] == "+91 11111 22222"
        assert lab["notes"] == "Updated notes"
    
    def test_delete_laboratory(self, api_client):
        """DELETE /api/laboratories/{id} removes a laboratory"""
        # First create a lab
        payload = {
            "name": "TEST_Lab to Delete",
            "city": "Chennai"
        }
        create_response = api_client.post(f"{BASE_URL}/api/laboratories", json=payload)
        assert create_response.status_code == 200
        lab_id = create_response.json()["id"]
        
        # Delete the lab
        delete_response = api_client.delete(f"{BASE_URL}/api/laboratories/{lab_id}")
        assert delete_response.status_code == 200
        
        # Verify it's gone
        response = api_client.get(f"{BASE_URL}/api/laboratories")
        data = response.json()
        lab = next((l for l in data if l["id"] == lab_id), None)
        assert lab is None, "Deleted laboratory still appears in list"
    
    def test_delete_nonexistent_lab_returns_404(self, api_client):
        """DELETE /api/laboratories/{id} returns 404 for invalid ID"""
        response = api_client.delete(f"{BASE_URL}/api/laboratories/nonexistent-lab-id-12345")
        assert response.status_code == 404
    
    def test_update_nonexistent_lab_returns_404(self, api_client):
        """PUT /api/laboratories/{id} returns 404 for invalid ID"""
        response = api_client.put(
            f"{BASE_URL}/api/laboratories/nonexistent-lab-id-12345",
            json={"name": "Test Lab"}
        )
        assert response.status_code == 404
    
    def test_add_laboratory_minimal_fields(self, api_client):
        """POST /api/laboratories works with only name field"""
        payload = {"name": "TEST_Minimal Lab"}
        response = api_client.post(f"{BASE_URL}/api/laboratories", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_Minimal Lab"
        assert "id" in data
        # Optional fields should have defaults
        assert data.get("address", "") == ""
        assert data.get("city", "") == ""


class TestEdgeCases:
    """Test edge cases and validation"""
    
    def test_add_custom_test_with_empty_diseases(self, api_client):
        """Custom test can be added with empty diseases array"""
        payload = {
            "name": "TEST_No Disease Test",
            "diseases": [],
            "frequency_months": 12,
            "price": 500
        }
        response = api_client.post(f"{BASE_URL}/api/catalog/lab-tests", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["diseases"] == []
    
    def test_add_custom_test_with_zero_price(self, api_client):
        """Custom test can be added with zero price"""
        payload = {
            "name": "TEST_Free Test",
            "diseases": ["Diabetes"],
            "frequency_months": 6,
            "price": 0
        }
        response = api_client.post(f"{BASE_URL}/api/catalog/lab-tests", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["price"] == 0
    
    def test_update_lab_with_empty_payload_returns_400(self, api_client):
        """PUT /api/laboratories/{id} with empty payload returns 400"""
        # First create a lab
        payload = {"name": "TEST_Empty Update Lab"}
        create_response = api_client.post(f"{BASE_URL}/api/laboratories", json=payload)
        assert create_response.status_code == 200
        lab_id = create_response.json()["id"]
        
        # Try to update with empty payload
        response = api_client.put(f"{BASE_URL}/api/laboratories/{lab_id}", json={})
        assert response.status_code == 400
    
    def test_update_custom_test_with_empty_payload_returns_400(self, api_client):
        """PUT /api/catalog/lab-tests/{id} with empty payload returns 400"""
        # First create a test
        payload = {
            "name": "TEST_Empty Update Test",
            "diseases": ["Diabetes"],
            "frequency_months": 6,
            "price": 100
        }
        create_response = api_client.post(f"{BASE_URL}/api/catalog/lab-tests", json=payload)
        assert create_response.status_code == 200
        test_id = create_response.json()["id"]
        
        # Try to update with empty payload
        response = api_client.put(f"{BASE_URL}/api/catalog/lab-tests/{test_id}", json={})
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
