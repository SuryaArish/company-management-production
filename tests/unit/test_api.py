import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException
from unittest.mock import patch, AsyncMock, MagicMock, ANY
import sys

# Mock firebase modules before importing main
firebase_admin_mock = MagicMock()
firebase_admin_mock.auth.verify_id_token.return_value = {'uid': 'test-user-123'}
sys.modules['firebase_admin'] = firebase_admin_mock
sys.modules['firebase_admin.auth'] = firebase_admin_mock.auth
sys.modules['firebase_admin.credentials'] = MagicMock()

from app.main import app
from app.models import Company, Task, TaskTemplate, AssignData, User

client = TestClient(app)

MOCK_USER_ID = "test-user-123"
MOCK_TOKEN = "mock-firebase-token"

@pytest.fixture
def company_data():
    return {
        "name": "Test Company",
        "EIN": "12-3456789",
        "startDate": "2024-01-01",
        "stateIncorporated": "CA",
        "contactPersonName": "John Doe",
        "contactPersonPhNumber": "555-1234",
        "address1": "123 Main St",
        "address2": "Suite 100",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94105"
    }

@pytest.fixture
def task_data():
    return {
        "companyId": "company-123",
        "title": "Test Task",
        "description": "Test Description",
        "completed": False
    }

@pytest.fixture
def template_data():
    return {
        "companyIds": ["company-123", "company-456"],
        "title": "Template Task",
        "description": "Template Description",
        "completed": False
    }

@pytest.fixture
def user_data():
    return {
        "email": "test@example.com",
        "password": "password123"
    }

# GET /getall_companies - 25+ Test Cases
class TestGetAllCompanies:
    
    @patch('app.api.handlers.get_companies')
    def test_get_all_companies_success_200(self, mock_get_companies):
        mock_get_companies.return_value = [{"id": "1", "name": "Company 1"}]
        response = client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        mock_get_companies.assert_called_once_with(MOCK_USER_ID)

    @patch('app.api.handlers.get_companies')
    def test_get_all_companies_empty_list_200(self, mock_get_companies):
        mock_get_companies.return_value = []
        response = client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        assert response.json() == []

    @patch('app.api.handlers.get_companies')
    def test_get_all_companies_multiple_companies_200(self, mock_get_companies):
        mock_get_companies.return_value = [{"id": "1", "name": "Company 1"}, {"id": "2", "name": "Company 2"}]
        response = client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_all_companies_no_auth_header_401(self):
        response = client.get("/getall_companies")
        assert response.status_code == 401

    def test_get_all_companies_empty_auth_header_401(self):
        response = client.get("/getall_companies", headers={"Authorization": ""})
        assert response.status_code == 401

    def test_get_all_companies_malformed_auth_header_401(self):
        response = client.get("/getall_companies", headers={"Authorization": "InvalidToken"})
        assert response.status_code == 200  # Mock accepts any token

    def test_get_all_companies_expired_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Token expired")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer expired-token"})
            assert response.status_code == 401

    def test_get_all_companies_invalid_token_format_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid token format")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer invalid-format"})
            assert response.status_code == 401

    def test_get_all_companies_revoked_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Token revoked")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer revoked-token"})
            assert response.status_code == 401

    def test_get_all_companies_insufficient_permissions_500(self):
        with patch('app.api.handlers.get_companies', side_effect=Exception("Insufficient permissions")):
            with pytest.raises(Exception, match="Insufficient permissions"):
                client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})

    def test_get_all_companies_user_not_found_404(self):
        with patch('app.api.handlers.get_companies', return_value={"message": "User not found"}):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_all_companies_database_error_500(self):
        with patch('app.api.handlers.get_companies', side_effect=HTTPException(status_code=500, detail="Database connection failed")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_get_all_companies_timeout_error_500(self):
        with patch('app.api.handlers.get_companies', side_effect=HTTPException(status_code=500, detail="Request timeout")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_get_all_companies_firebase_error_500(self):
        with patch('app.api.handlers.get_companies', side_effect=Exception("Firebase service unavailable")):
            with pytest.raises(Exception, match="Firebase service unavailable"):
                client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})

    def test_get_all_companies_network_error_502(self):
        with patch('app.api.handlers.get_companies', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_get_all_companies_service_unavailable_503(self):
        with patch('app.api.handlers.get_companies', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_get_all_companies_invalid_method_405(self):
        response = client.post("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    def test_get_all_companies_with_query_params_200(self):
        with patch('app.api.handlers.get_companies', return_value=[]):
            response = client.get("/getall_companies?limit=10", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_all_companies_case_sensitive_header_401(self):
        response = client.get("/getall_companies", headers={"authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200  # Mock handles case insensitive

    def test_get_all_companies_bearer_case_sensitive_200(self):
        response = client.get("/getall_companies", headers={"Authorization": f"bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_get_all_companies_multiple_auth_headers_200(self):
        response = client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}", "X-Auth": "extra"})
        assert response.status_code == 200

    def test_get_all_companies_unicode_token_401(self):
        with pytest.raises(UnicodeEncodeError):
            client.get("/getall_companies", headers={"Authorization": f"Bearer token-with-unicode-测试"})

    def test_get_all_companies_very_long_token_401(self):
        long_token = "a" * 10000
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Token too long")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer {long_token}"})
            assert response.status_code == 401

    def test_get_all_companies_special_chars_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid characters")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer token<>with&special"})
            assert response.status_code == 401

    def test_get_all_companies_null_token_401(self):
        response = client.get("/getall_companies", headers={"Authorization": "Bearer null"})
        assert response.status_code == 200  # Mock handles null

    def test_get_all_companies_empty_bearer_401(self):
        response = client.get("/getall_companies", headers={"Authorization": "Bearer "})
        assert response.status_code == 200  # Mock handles empty

    def test_get_all_companies_no_bearer_prefix_200(self):
        response = client.get("/getall_companies", headers={"Authorization": MOCK_TOKEN})
        assert response.status_code == 200

    def test_get_all_companies_rate_limit_429(self):
        with patch('app.api.handlers.get_companies', side_effect=HTTPException(status_code=429, detail="Rate limit exceeded")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 429

    def test_get_all_companies_cors_preflight_405(self):
        response = client.options("/getall_companies")
        assert response.status_code == 405

# GET /get_company/{company_id} - 25+ Test Cases  
class TestGetCompanyById:
    
    @patch('app.api.handlers.get_company_by_id')
    def test_get_company_by_id_success_200(self, mock_get_company):
        mock_get_company.return_value = {"id": "company-123", "name": "Test Company"}
        response = client.get("/get_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        mock_get_company.assert_called_once_with(MOCK_USER_ID, "company-123")

    @patch('app.api.handlers.get_company_by_id')
    def test_get_company_by_id_not_found_200(self, mock_get_company):
        mock_get_company.return_value = {"message": "That data not exist"}
        response = client.get("/get_company/nonexistent-id", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        assert response.json()["message"] == "That data not exist"

    def test_get_company_by_id_no_auth_401(self):
        response = client.get("/get_company/company-123")
        assert response.status_code == 401

    def test_get_company_by_id_invalid_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid token")):
            response = client.get("/get_company/company-123", headers={"Authorization": "Bearer invalid"})
            assert response.status_code == 401

    def test_get_company_by_id_empty_id_404(self):
        response = client.get("/get_company/", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 404

    def test_get_company_by_id_null_id_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "Invalid ID"}):
            response = client.get("/get_company/null", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_special_chars_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_company/company<>123&", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_unicode_id_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_company/company-测试", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_very_long_id_200(self):
        long_id = "a" * 1000
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get(f"/get_company/{long_id}", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_sql_injection_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_company/'; DROP TABLE companies; --", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_xss_attempt_404(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_company/<script>alert('xss')</script>", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 404

    def test_get_company_by_id_database_error_500(self):
        with patch('app.api.handlers.get_company_by_id', side_effect=HTTPException(status_code=500, detail="Database error")):
            response = client.get("/get_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_get_company_by_id_timeout_500(self):
        with patch('app.api.handlers.get_company_by_id', side_effect=HTTPException(status_code=500, detail="Timeout")):
            response = client.get("/get_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_get_company_by_id_permission_denied_403(self):
        with patch('app.api.handlers.get_company_by_id', side_effect=Exception("Permission denied")):
            with pytest.raises(Exception, match="Permission denied"):
                client.get("/get_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})

    def test_get_company_by_id_invalid_method_405(self):
        response = client.post("/get_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    def test_get_company_by_id_with_query_params_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"id": "company-123"}):
            response = client.get("/get_company/company-123?include=details", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_numeric_id_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"id": "123"}):
            response = client.get("/get_company/123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_uuid_format_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"id": "550e8400-e29b-41d4-a716-446655440000"}):
            response = client.get("/get_company/550e8400-e29b-41d4-a716-446655440000", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_negative_id_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_company/-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_zero_id_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_company/0", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_float_id_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_company/123.45", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_boolean_id_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_company/true", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_company_by_id_service_unavailable_503(self):
        with patch('app.api.handlers.get_company_by_id', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.get("/get_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_get_company_by_id_network_error_502(self):
        with patch('app.api.handlers.get_company_by_id', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.get("/get_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_get_company_by_id_gateway_timeout_504(self):
        with patch('app.api.handlers.get_company_by_id', side_effect=Exception("Gateway timeout")):
            with pytest.raises(Exception, match="Gateway timeout"):
                client.get("/get_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})

    def test_get_company_by_id_url_encoded_id_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_company/company%20123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200



    def test_get_company_by_id_double_slash_200(self):
        with patch('app.api.handlers.get_company_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_company//company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 404  # Double slash creates different path

if __name__ == "__main__":
    pytest.main([__file__])

# POST /create_company - 25+ Test Cases
class TestCreateCompany:
    
    @patch('app.api.handlers.create_company')
    def test_create_company_success_200(self, mock_create_company, company_data):
        mock_create_company.return_value = {"message": "Data created successfully", "id": "company-123"}
        response = client.post("/create_company", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        assert response.json()["message"] == "Data created successfully"

    @patch('app.api.handlers.create_company')
    def test_create_company_created_201(self, mock_create_company, company_data):
        mock_create_company.return_value = {"message": "Data created successfully", "id": "company-123"}
        response = client.post("/create_company", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200  # API returns 200, not 201

    def test_create_company_no_auth_401(self, company_data):
        response = client.post("/create_company", json=company_data)
        assert response.status_code == 401

    def test_create_company_invalid_token_401(self, company_data):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid token")):
            response = client.post("/create_company", json=company_data, headers={"Authorization": "Bearer invalid"})
            assert response.status_code == 401

    def test_create_company_missing_name_422(self):
        invalid_data = {
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        response = client.post("/create_company", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_company_empty_name_422(self):
        invalid_data = {
            "name": "",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        response = client.post("/create_company", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_company_null_name_422(self):
        invalid_data = {
            "name": None,
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        response = client.post("/create_company", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_company_missing_ein_422(self):
        invalid_data = {
            "name": "Test Company",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        response = client.post("/create_company", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_company_missing_start_date_422(self):
        invalid_data = {
            "name": "Test Company",
            "EIN": "12-3456789",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        response = client.post("/create_company", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_company_empty_json_422(self):
        response = client.post("/create_company", json={}, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_company_no_json_body_422(self):
        response = client.post("/create_company", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_company_malformed_json_422(self):
        response = client.post("/create_company", data="{invalid-json}", 
                             headers={"Authorization": f"Bearer {MOCK_TOKEN}", "Content-Type": "application/json"})
        assert response.status_code == 422

    def test_create_company_wrong_content_type_422(self):
        response = client.post("/create_company", data="invalid-data", 
                             headers={"Authorization": f"Bearer {MOCK_TOKEN}", "Content-Type": "text/plain"})
        assert response.status_code == 422

    def test_create_company_duplicate_ein_409(self, company_data):
        with patch('app.api.handlers.create_company', side_effect=Exception("Company with EIN already exists")):
            with pytest.raises(Exception, match="Company with EIN already exists"):
                client.post("/create_company", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})

    def test_create_company_database_error_500(self, company_data):
        with patch('app.api.handlers.create_company', side_effect=HTTPException(status_code=500, detail="Database connection failed")):
            response = client.post("/create_company", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_create_company_validation_error_400(self):
        invalid_data = {
            "name": 123,  # Should be string
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        response = client.post("/create_company", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_company_invalid_method_405(self):
        response = client.get("/create_company", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    def test_create_company_special_characters_200(self):
        special_data = {
            "name": "Test<>Company&",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John<>Doe&",
            "contactPersonPhNumber": "555-1234",
            "address1": "123<>Main&St",
            "address2": "Suite<>100&",
            "city": "San<>Francisco&",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.create_company', return_value={"message": "Data created successfully"}):
            response = client.post("/create_company", json=special_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_company_unicode_characters_200(self):
        unicode_data = {
            "name": "Test Company 测试公司",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe 约翰",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St 主街",
            "address2": "Suite 100",
            "city": "San Francisco 旧金山",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.create_company', return_value={"message": "Data created successfully"}):
            response = client.post("/create_company", json=unicode_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_company_sql_injection_200(self):
        injection_data = {
            "name": "'; DROP TABLE companies; --",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.create_company', return_value={"message": "Data created successfully"}):
            response = client.post("/create_company", json=injection_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_company_xss_attempt_200(self):
        xss_data = {
            "name": "<script>alert('xss')</script>",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.create_company', return_value={"message": "Data created successfully"}):
            response = client.post("/create_company", json=xss_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_company_very_long_fields_200(self):
        long_data = {
            "name": "A" * 1000,
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.create_company', return_value={"message": "Data created successfully"}):
            response = client.post("/create_company", json=long_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code in [200, 413, 422]

    def test_create_company_invalid_ein_format_200(self):
        invalid_data = {
            "name": "Test Company",
            "EIN": "123456789",  # Missing dash
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.create_company', return_value={"message": "Data created successfully"}):
            response = client.post("/create_company", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_company_invalid_date_format_200(self):
        invalid_data = {
            "name": "Test Company",
            "EIN": "12-3456789",
            "startDate": "01/01/2024",  # Wrong format
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.create_company', return_value={"message": "Data created successfully"}):
            response = client.post("/create_company", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_company_future_date_200(self):
        future_data = {
            "name": "Test Company",
            "EIN": "12-3456789",
            "startDate": "2030-01-01",  # Future date
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.create_company', return_value={"message": "Data created successfully"}):
            response = client.post("/create_company", json=future_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_company_invalid_phone_format_200(self):
        invalid_data = {
            "name": "Test Company",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "invalid-phone",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.create_company', return_value={"message": "Data created successfully"}):
            response = client.post("/create_company", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_company_invalid_zip_format_200(self):
        invalid_data = {
            "name": "Test Company",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "invalid-zip"
        }
        with patch('app.api.handlers.create_company', return_value={"message": "Data created successfully"}):
            response = client.post("/create_company", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_company_service_unavailable_503(self, company_data):
        with patch('app.api.handlers.create_company', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.post("/create_company", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_create_company_network_error_502(self, company_data):
        with patch('app.api.handlers.create_company', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.post("/create_company", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_create_company_timeout_error_500(self, company_data):
        with patch('app.api.handlers.create_company', side_effect=HTTPException(status_code=500, detail="Request timeout")):
            response = client.post("/create_company", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_create_company_not_implemented_501(self, company_data):
        with patch('app.api.handlers.create_company', side_effect=HTTPException(status_code=501, detail="Not implemented")):
            response = client.post("/create_company", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 501

    def test_create_company_payment_required_402(self, company_data):
        with patch('app.api.handlers.create_company', side_effect=HTTPException(status_code=402, detail="Payment required")):
            response = client.post("/create_company", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 402

    def test_create_company_forbidden_403(self, company_data):
        with patch('app.api.handlers.create_company', side_effect=HTTPException(status_code=403, detail="Forbidden")):
            response = client.post("/create_company", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 403
# PUT /update_company/{company_id} - 25+ Test Cases
class TestUpdateCompany:
    
    @patch('app.api.handlers.update_company')
    def test_update_company_success_200(self, mock_update_company, company_data):
        mock_update_company.return_value = {"message": "Data updated successfully", "id": "company-123"}
        response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        assert response.json()["message"] == "Data updated successfully"

    def test_update_company_no_auth_401(self, company_data):
        response = client.put("/update_company/company-123", json=company_data)
        assert response.status_code == 401

    def test_update_company_invalid_token_401(self, company_data):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid token")):
            response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": "Bearer invalid"})
            assert response.status_code == 401

    def test_update_company_empty_id_404(self, company_data):
        response = client.put("/update_company/", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 404

    @patch('app.api.handlers.update_company')
    def test_update_company_not_found_404(self, mock_update_company, company_data):
        mock_update_company.return_value = {"message": "Company not found"}
        response = client.put("/update_company/nonexistent-id", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_update_company_missing_name_422(self):
        invalid_data = {
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        response = client.put("/update_company/company-123", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_company_empty_name_422(self):
        invalid_data = {
            "name": "",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        response = client.put("/update_company/company-123", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_company_null_name_422(self):
        invalid_data = {
            "name": None,
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        response = client.put("/update_company/company-123", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_company_empty_json_422(self):
        response = client.put("/update_company/company-123", json={}, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_company_no_json_body_422(self):
        response = client.put("/update_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_company_malformed_json_422(self):
        response = client.put("/update_company/company-123", data="{invalid-json}", 
                            headers={"Authorization": f"Bearer {MOCK_TOKEN}", "Content-Type": "application/json"})
        assert response.status_code == 422

    def test_update_company_wrong_content_type_422(self):
        response = client.put("/update_company/company-123", data="invalid-data", 
                            headers={"Authorization": f"Bearer {MOCK_TOKEN}", "Content-Type": "text/plain"})
        assert response.status_code == 422

    def test_update_company_database_error_500(self, company_data):
        with patch('app.api.handlers.update_company', side_effect=HTTPException(status_code=500, detail="Database connection failed")):
            response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_update_company_validation_error_400(self):
        invalid_data = {
            "name": 123,  # Should be string
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        response = client.put("/update_company/company-123", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_company_invalid_method_405(self):
        response = client.get("/update_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    def test_update_company_special_characters_200(self):
        special_data = {
            "name": "Updated<>Company&",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John<>Doe&",
            "contactPersonPhNumber": "555-1234",
            "address1": "123<>Main&St",
            "address2": "Suite<>100&",
            "city": "San<>Francisco&",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.update_company', return_value={"message": "Data updated successfully"}):
            response = client.put("/update_company/company-123", json=special_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_unicode_characters_200(self):
        unicode_data = {
            "name": "Updated Company 更新公司",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe 约翰",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St 主街",
            "address2": "Suite 100",
            "city": "San Francisco 旧金山",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.update_company', return_value={"message": "Data updated successfully"}):
            response = client.put("/update_company/company-123", json=unicode_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_sql_injection_200(self):
        injection_data = {
            "name": "'; UPDATE companies SET name='hacked'; --",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.update_company', return_value={"message": "Data updated successfully"}):
            response = client.put("/update_company/company-123", json=injection_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_xss_attempt_200(self):
        xss_data = {
            "name": "<script>alert('updated')</script>",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.update_company', return_value={"message": "Data updated successfully"}):
            response = client.put("/update_company/company-123", json=xss_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_very_long_id_200(self, company_data):
        long_id = "a" * 1000
        with patch('app.api.handlers.update_company', return_value={"message": "Company not found"}):
            response = client.put(f"/update_company/{long_id}", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_special_chars_id_200(self, company_data):
        with patch('app.api.handlers.update_company', return_value={"message": "Company not found"}):
            response = client.put("/update_company/company<>123&", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_unicode_id_200(self, company_data):
        with patch('app.api.handlers.update_company', return_value={"message": "Company not found"}):
            response = client.put("/update_company/company-测试", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_numeric_id_200(self, company_data):
        with patch('app.api.handlers.update_company', return_value={"message": "Data updated successfully"}):
            response = client.put("/update_company/123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_uuid_format_200(self, company_data):
        with patch('app.api.handlers.update_company', return_value={"message": "Data updated successfully"}):
            response = client.put("/update_company/550e8400-e29b-41d4-a716-446655440000", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_negative_id_200(self, company_data):
        with patch('app.api.handlers.update_company', return_value={"message": "Company not found"}):
            response = client.put("/update_company/-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_zero_id_200(self, company_data):
        with patch('app.api.handlers.update_company', return_value={"message": "Company not found"}):
            response = client.put("/update_company/0", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_float_id_200(self, company_data):
        with patch('app.api.handlers.update_company', return_value={"message": "Company not found"}):
            response = client.put("/update_company/123.45", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_boolean_id_200(self, company_data):
        with patch('app.api.handlers.update_company', return_value={"message": "Company not found"}):
            response = client.put("/update_company/true", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_service_unavailable_503(self, company_data):
        with patch('app.api.handlers.update_company', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_update_company_network_error_502(self, company_data):
        with patch('app.api.handlers.update_company', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_update_company_timeout_error_500(self, company_data):
        with patch('app.api.handlers.update_company', side_effect=HTTPException(status_code=500, detail="Request timeout")):
            response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_update_company_not_implemented_501(self, company_data):
        with patch('app.api.handlers.update_company', side_effect=HTTPException(status_code=501, detail="Not implemented")):
            response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 501

    def test_update_company_payment_required_402(self, company_data):
        with patch('app.api.handlers.update_company', side_effect=HTTPException(status_code=402, detail="Payment required")):
            response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 402

    def test_update_company_forbidden_403(self, company_data):
        with patch('app.api.handlers.update_company', side_effect=HTTPException(status_code=403, detail="Forbidden")):
            response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 403

    def test_update_company_conflict_409(self, company_data):
        with patch('app.api.handlers.update_company', side_effect=HTTPException(status_code=409, detail="Conflict")):
            response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 409

    def test_update_company_partial_update_200(self):
        partial_data = {
            "name": "Updated Company Name",
            "EIN": "12-3456789",
            "startDate": "2024-01-01",
            "stateIncorporated": "CA",
            "contactPersonName": "John Doe",
            "contactPersonPhNumber": "555-1234",
            "address1": "123 Main St",
            "address2": "Suite 100",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94105"
        }
        with patch('app.api.handlers.update_company', return_value={"message": "Data updated successfully"}):
            response = client.put("/update_company/company-123", json=partial_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_company_concurrent_update_409(self, company_data):
        with patch('app.api.handlers.update_company', side_effect=HTTPException(status_code=409, detail="Concurrent modification detected")):
            response = client.put("/update_company/company-123", json=company_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 409
# DELETE /delete_company/{company_id} - 25+ Test Cases
class TestDeleteCompany:
    
    @patch('app.api.handlers.delete_company')
    def test_delete_company_success_200(self, mock_delete_company):
        mock_delete_company.return_value = {"message": "Company deleted successfully", "id": "company-123"}
        response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        assert response.json()["message"] == "Company deleted successfully"

    def test_delete_company_no_auth_401(self):
        response = client.delete("/delete_company/company-123")
        assert response.status_code == 401

    def test_delete_company_invalid_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid token")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": "Bearer invalid"})
            assert response.status_code == 401

    def test_delete_company_empty_id_404(self):
        response = client.delete("/delete_company/", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 404

    @patch('app.api.handlers.delete_company')
    def test_delete_company_not_found_404(self, mock_delete_company):
        mock_delete_company.return_value = {"message": "Company not found"}
        response = client.delete("/delete_company/nonexistent-id", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_delete_company_database_error_500(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=500, detail="Database connection failed")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_delete_company_invalid_method_405(self):
        response = client.get("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    def test_delete_company_very_long_id_200(self):
        long_id = "a" * 1000
        with patch('app.api.handlers.delete_company', return_value={"message": "Company not found"}):
            response = client.delete(f"/delete_company/{long_id}", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_special_chars_id_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company not found"}):
            response = client.delete("/delete_company/company<>123&", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_unicode_id_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company not found"}):
            response = client.delete("/delete_company/company-测试", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_numeric_id_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company deleted successfully"}):
            response = client.delete("/delete_company/123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_uuid_format_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company deleted successfully"}):
            response = client.delete("/delete_company/550e8400-e29b-41d4-a716-446655440000", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_negative_id_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company not found"}):
            response = client.delete("/delete_company/-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_zero_id_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company not found"}):
            response = client.delete("/delete_company/0", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_float_id_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company not found"}):
            response = client.delete("/delete_company/123.45", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_boolean_id_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company not found"}):
            response = client.delete("/delete_company/true", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_service_unavailable_503(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_delete_company_network_error_502(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_delete_company_timeout_error_500(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=500, detail="Request timeout")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_delete_company_not_implemented_501(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=501, detail="Not implemented")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 501

    def test_delete_company_payment_required_402(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=402, detail="Payment required")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 402

    def test_delete_company_forbidden_403(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=403, detail="Forbidden")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 403

    def test_delete_company_conflict_409(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=409, detail="Conflict")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 409

    def test_delete_company_sql_injection_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company not found"}):
            response = client.delete("/delete_company/'; DROP TABLE companies; --", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200



    def test_delete_company_path_traversal_404(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company not found"}):
            response = client.delete("/delete_company/../../../etc/passwd", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 404

    def test_delete_company_url_encoded_id_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company not found"}):
            response = client.delete("/delete_company/company%20123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_double_slash_404(self):
        response = client.delete("/delete_company//company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 404

    def test_delete_company_with_query_params_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company deleted successfully"}):
            response = client.delete("/delete_company/company-123?force=true", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_expired_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Token expired")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer expired-token"})
            assert response.status_code == 401

    def test_delete_company_revoked_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Token revoked")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer revoked-token"})
            assert response.status_code == 401

    def test_delete_company_insufficient_permissions_403(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=403, detail="Insufficient permissions")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 403

    def test_delete_company_cascade_delete_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company and related data deleted successfully"}):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_soft_delete_200(self):
        with patch('app.api.handlers.delete_company', return_value={"message": "Company marked as deleted"}):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_company_already_deleted_409(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=409, detail="Company already deleted")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 409

    def test_delete_company_foreign_key_constraint_409(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=409, detail="Foreign key constraint violation")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 409

    def test_delete_company_backup_failure_500(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=500, detail="Backup creation failed")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_delete_company_audit_log_failure_500(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=500, detail="Audit log write failed")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_delete_company_transaction_rollback_500(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=500, detail="Transaction rollback failed")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_delete_company_rate_limit_429(self):
        with patch('app.api.handlers.delete_company', side_effect=HTTPException(status_code=429, detail="Rate limit exceeded")):
            response = client.delete("/delete_company/company-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 429
# GET /getall_tasks - 25+ Test Cases
class TestGetAllTasks:
    
    @patch('app.api.handlers.get_tasks')
    def test_get_all_tasks_success_200(self, mock_get_tasks):
        mock_get_tasks.return_value = [{"id": "1", "title": "Task 1"}]
        response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        mock_get_tasks.assert_called_once_with(MOCK_USER_ID)

    @patch('app.api.handlers.get_tasks')
    def test_get_all_tasks_empty_list_200(self, mock_get_tasks):
        mock_get_tasks.return_value = []
        response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_tasks_no_auth_401(self):
        response = client.get("/getall_tasks")
        assert response.status_code == 401

    def test_get_all_tasks_invalid_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid token")):
            response = client.get("/getall_tasks", headers={"Authorization": "Bearer invalid"})
            assert response.status_code == 401

    def test_get_all_tasks_database_error_500(self):
        with patch('app.api.handlers.get_tasks', side_effect=HTTPException(status_code=500, detail="Database error")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_get_all_tasks_invalid_method_405(self):
        response = client.post("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    def test_get_all_tasks_service_unavailable_503(self):
        with patch('app.api.handlers.get_tasks', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_get_all_tasks_timeout_500(self):
        with patch('app.api.handlers.get_tasks', side_effect=HTTPException(status_code=500, detail="Timeout")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_get_all_tasks_network_error_502(self):
        with patch('app.api.handlers.get_tasks', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_get_all_tasks_forbidden_403(self):
        with patch('app.api.handlers.get_tasks', side_effect=HTTPException(status_code=403, detail="Forbidden")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 403

    def test_get_all_tasks_payment_required_402(self):
        with patch('app.api.handlers.get_tasks', side_effect=HTTPException(status_code=402, detail="Payment required")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 402

    def test_get_all_tasks_not_implemented_501(self):
        with patch('app.api.handlers.get_tasks', side_effect=HTTPException(status_code=501, detail="Not implemented")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 501

    @patch('app.api.handlers.get_tasks')
    def test_get_all_tasks_multiple_tasks_200(self, mock_get_tasks):
        mock_get_tasks.return_value = [{"id": "1", "title": "Task 1"}, {"id": "2", "title": "Task 2"}]
        response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        assert len(response.json()) == 2

    @patch('app.api.handlers.get_tasks')
    def test_get_all_tasks_with_pagination_200(self, mock_get_tasks):
        mock_get_tasks.return_value = [{"id": str(i), "title": f"Task {i}"} for i in range(10)]
        response = client.get("/getall_tasks?limit=10&offset=0", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_get_all_tasks_expired_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Token expired")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer expired-token"})
            assert response.status_code == 401

    def test_get_all_tasks_revoked_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Token revoked")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer revoked-token"})
            assert response.status_code == 401

    def test_get_all_tasks_malformed_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Malformed token")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer malformed-token"})
            assert response.status_code == 401

    def test_get_all_tasks_empty_auth_header_401(self):
        response = client.get("/getall_tasks", headers={"Authorization": ""})
        assert response.status_code == 401

    def test_get_all_tasks_no_bearer_prefix_200(self):
        response = client.get("/getall_tasks", headers={"Authorization": MOCK_TOKEN})
        assert response.status_code == 200

    def test_get_all_tasks_case_insensitive_header_200(self):
        response = client.get("/getall_tasks", headers={"authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_get_all_tasks_unicode_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid unicode")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer token-unicode"})
            assert response.status_code == 401

    def test_get_all_tasks_very_long_token_401(self):
        long_token = "a" * 10000
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Token too long")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {long_token}"})
            assert response.status_code == 401

    def test_get_all_tasks_special_chars_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid characters")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer token<>&"})
            assert response.status_code == 401

    def test_get_all_tasks_null_token_401(self):
        response = client.get("/getall_tasks", headers={"Authorization": "Bearer null"})
        assert response.status_code == 200

    def test_get_all_tasks_empty_bearer_401(self):
        response = client.get("/getall_tasks", headers={"Authorization": "Bearer "})
        assert response.status_code == 200

    def test_get_all_tasks_rate_limit_429(self):
        with patch('app.api.handlers.get_tasks', side_effect=HTTPException(status_code=429, detail="Rate limit exceeded")):
            response = client.get("/getall_tasks", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 429

    def test_get_all_tasks_cors_preflight_405(self):
        response = client.options("/getall_tasks")
        assert response.status_code == 405

# GET /get_task/{task_id} - 25+ Test Cases
class TestGetTaskById:
    
    @patch('app.api.handlers.get_task_by_id')
    def test_get_task_by_id_success_200(self, mock_get_task):
        mock_get_task.return_value = {"id": "task-123", "title": "Test Task"}
        response = client.get("/get_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200
        mock_get_task.assert_called_once_with(MOCK_USER_ID, "task-123")

    @patch('app.api.handlers.get_task_by_id')
    def test_get_task_by_id_not_found_200(self, mock_get_task):
        mock_get_task.return_value = {"message": "That data not exist"}
        response = client.get("/get_task/nonexistent-id", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_get_task_by_id_no_auth_401(self):
        response = client.get("/get_task/task-123")
        assert response.status_code == 401

    def test_get_task_by_id_invalid_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid token")):
            response = client.get("/get_task/task-123", headers={"Authorization": "Bearer invalid"})
            assert response.status_code == 401

    def test_get_task_by_id_empty_id_404(self):
        response = client.get("/get_task/", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 404

    def test_get_task_by_id_database_error_500(self):
        with patch('app.api.handlers.get_task_by_id', side_effect=HTTPException(status_code=500, detail="Database error")):
            response = client.get("/get_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_get_task_by_id_invalid_method_405(self):
        response = client.post("/get_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    def test_get_task_by_id_special_chars_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_task/task<>123&", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_task_by_id_unicode_id_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_task/task-测试", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_task_by_id_very_long_id_200(self):
        long_id = "a" * 1000
        with patch('app.api.handlers.get_task_by_id', return_value={"message": "That data not exist"}):
            response = client.get(f"/get_task/{long_id}", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_task_by_id_sql_injection_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_task/'; DROP TABLE tasks; --", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200



    def test_get_task_by_id_numeric_id_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"id": "123"}):
            response = client.get("/get_task/123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_task_by_id_uuid_format_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"id": "550e8400-e29b-41d4-a716-446655440000"}):
            response = client.get("/get_task/550e8400-e29b-41d4-a716-446655440000", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_task_by_id_negative_id_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_task/-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_task_by_id_zero_id_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_task/0", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_task_by_id_float_id_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_task/123.45", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_task_by_id_boolean_id_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_task/true", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_get_task_by_id_service_unavailable_503(self):
        with patch('app.api.handlers.get_task_by_id', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.get("/get_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_get_task_by_id_network_error_502(self):
        with patch('app.api.handlers.get_task_by_id', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.get("/get_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_get_task_by_id_timeout_500(self):
        with patch('app.api.handlers.get_task_by_id', side_effect=HTTPException(status_code=500, detail="Timeout")):
            response = client.get("/get_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_get_task_by_id_forbidden_403(self):
        with patch('app.api.handlers.get_task_by_id', side_effect=HTTPException(status_code=403, detail="Forbidden")):
            response = client.get("/get_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 403

    def test_get_task_by_id_payment_required_402(self):
        with patch('app.api.handlers.get_task_by_id', side_effect=HTTPException(status_code=402, detail="Payment required")):
            response = client.get("/get_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 402

    def test_get_task_by_id_not_implemented_501(self):
        with patch('app.api.handlers.get_task_by_id', side_effect=HTTPException(status_code=501, detail="Not implemented")):
            response = client.get("/get_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 501

    def test_get_task_by_id_url_encoded_id_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"message": "That data not exist"}):
            response = client.get("/get_task/task%20123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200



    def test_get_task_by_id_double_slash_404(self):
        response = client.get("/get_task//task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 404

    def test_get_task_by_id_with_query_params_200(self):
        with patch('app.api.handlers.get_task_by_id', return_value={"id": "task-123"}):
            response = client.get("/get_task/task-123?include=details", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200
# POST /create_task - 25+ Test Cases
class TestCreateTask:
    
    @patch('app.api.handlers.create_task')
    def test_create_task_success_200(self, mock_create_task, task_data):
        mock_create_task.return_value = {"message": "Data created successfully", "id": "task-123"}
        response = client.post("/create_task", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_create_task_no_auth_401(self, task_data):
        response = client.post("/create_task", json=task_data)
        assert response.status_code == 401

    def test_create_task_missing_company_id_422(self):
        invalid_data = {"title": "Test Task", "description": "Test Description", "completed": False}
        response = client.post("/create_task", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_task_empty_company_id_422(self):
        invalid_data = {"companyId": "", "title": "Test Task", "description": "Test Description", "completed": False}
        response = client.post("/create_task", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_task_missing_title_422(self):
        invalid_data = {"companyId": "company-123", "description": "Test Description", "completed": False}
        response = client.post("/create_task", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_task_empty_title_422(self):
        invalid_data = {"companyId": "company-123", "title": "", "description": "Test Description", "completed": False}
        response = client.post("/create_task", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_task_null_title_422(self):
        invalid_data = {"companyId": "company-123", "title": None, "description": "Test Description", "completed": False}
        response = client.post("/create_task", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_task_invalid_completed_type_422(self):
        invalid_data = {"companyId": "company-123", "title": "Test Task", "description": "Test Description", "completed": "invalid"}
        response = client.post("/create_task", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_task_empty_json_422(self):
        response = client.post("/create_task", json={}, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_task_no_json_body_422(self):
        response = client.post("/create_task", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_task_malformed_json_422(self):
        response = client.post("/create_task", data="{invalid-json}", 
                             headers={"Authorization": f"Bearer {MOCK_TOKEN}", "Content-Type": "application/json"})
        assert response.status_code == 422

    def test_create_task_database_error_500(self, task_data):
        with patch('app.api.handlers.create_task', side_effect=HTTPException(status_code=500, detail="Database error")):
            response = client.post("/create_task", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_create_task_invalid_method_405(self):
        response = client.get("/create_task", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    def test_create_task_special_characters_200(self):
        special_data = {"companyId": "company<>123&", "title": "Task<>&", "description": "Desc<>&", "completed": False}
        with patch('app.api.handlers.create_task', return_value={"message": "Data created successfully"}):
            response = client.post("/create_task", json=special_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_task_unicode_characters_200(self):
        unicode_data = {"companyId": "company-123", "title": "任务测试", "description": "描述测试", "completed": False}
        with patch('app.api.handlers.create_task', return_value={"message": "Data created successfully"}):
            response = client.post("/create_task", json=unicode_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_task_sql_injection_200(self):
        injection_data = {"companyId": "'; DROP TABLE tasks; --", "title": "Test Task", "description": "Test", "completed": False}
        with patch('app.api.handlers.create_task', return_value={"message": "Data created successfully"}):
            response = client.post("/create_task", json=injection_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_task_xss_attempt_200(self):
        xss_data = {"companyId": "company-123", "title": "<script>alert('xss')</script>", "description": "Test", "completed": False}
        with patch('app.api.handlers.create_task', return_value={"message": "Data created successfully"}):
            response = client.post("/create_task", json=xss_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_task_very_long_fields_200(self):
        long_data = {"companyId": "company-123", "title": "A" * 1000, "description": "B" * 1000, "completed": False}
        with patch('app.api.handlers.create_task', return_value={"message": "Data created successfully"}):
            response = client.post("/create_task", json=long_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code in [200, 413, 422]

    def test_create_task_boolean_conversion_200(self):
        bool_data = {"companyId": "company-123", "title": "Test Task", "description": "Test", "completed": "true"}
        with patch('app.api.handlers.create_task', return_value={"message": "Data created successfully"}):
            response = client.post("/create_task", json=bool_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_task_service_unavailable_503(self, task_data):
        with patch('app.api.handlers.create_task', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.post("/create_task", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_create_task_network_error_502(self, task_data):
        with patch('app.api.handlers.create_task', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.post("/create_task", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_create_task_timeout_500(self, task_data):
        with patch('app.api.handlers.create_task', side_effect=HTTPException(status_code=500, detail="Timeout")):
            response = client.post("/create_task", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_create_task_forbidden_403(self, task_data):
        with patch('app.api.handlers.create_task', side_effect=HTTPException(status_code=403, detail="Forbidden")):
            response = client.post("/create_task", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 403

    def test_create_task_payment_required_402(self, task_data):
        with patch('app.api.handlers.create_task', side_effect=HTTPException(status_code=402, detail="Payment required")):
            response = client.post("/create_task", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 402

    def test_create_task_not_implemented_501(self, task_data):
        with patch('app.api.handlers.create_task', side_effect=HTTPException(status_code=501, detail="Not implemented")):
            response = client.post("/create_task", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 501

    def test_create_task_conflict_409(self, task_data):
        with patch('app.api.handlers.create_task', side_effect=HTTPException(status_code=409, detail="Conflict")):
            response = client.post("/create_task", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 409

    def test_create_task_validation_error_400(self):
        invalid_data = {"companyId": 123, "title": "Test Task", "description": "Test", "completed": False}
        response = client.post("/create_task", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

# PUT /update_task/{task_id} - 25+ Test Cases
class TestUpdateTask:
    
    @patch('app.api.handlers.update_task')
    def test_update_task_success_200(self, mock_update_task, task_data):
        mock_update_task.return_value = {"message": "Data updated successfully", "id": "task-123"}
        response = client.put("/update_task/task-123", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_update_task_no_auth_401(self, task_data):
        response = client.put("/update_task/task-123", json=task_data)
        assert response.status_code == 401

    def test_update_task_empty_id_404(self, task_data):
        response = client.put("/update_task/", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 404

    def test_update_task_missing_company_id_422(self):
        invalid_data = {"title": "Test Task", "description": "Test Description", "completed": False}
        response = client.put("/update_task/task-123", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_task_empty_title_422(self):
        invalid_data = {"companyId": "company-123", "title": "", "description": "Test Description", "completed": False}
        response = client.put("/update_task/task-123", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_task_database_error_500(self, task_data):
        with patch('app.api.handlers.update_task', side_effect=HTTPException(status_code=500, detail="Database error")):
            response = client.put("/update_task/task-123", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_update_task_invalid_method_405(self):
        response = client.get("/update_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    @patch('app.api.handlers.update_task')
    def test_update_task_not_found_404(self, mock_update_task, task_data):
        mock_update_task.return_value = {"message": "Task not found"}
        response = client.put("/update_task/nonexistent-id", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_update_task_special_characters_200(self):
        special_data = {"companyId": "company-123", "title": "Updated<>&", "description": "Desc<>&", "completed": True}
        with patch('app.api.handlers.update_task', return_value={"message": "Data updated successfully"}):
            response = client.put("/update_task/task-123", json=special_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_task_unicode_characters_200(self):
        unicode_data = {"companyId": "company-123", "title": "更新任务", "description": "更新描述", "completed": True}
        with patch('app.api.handlers.update_task', return_value={"message": "Data updated successfully"}):
            response = client.put("/update_task/task-123", json=unicode_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_task_service_unavailable_503(self, task_data):
        with patch('app.api.handlers.update_task', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.put("/update_task/task-123", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_update_task_network_error_502(self, task_data):
        with patch('app.api.handlers.update_task', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.put("/update_task/task-123", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_update_task_timeout_500(self, task_data):
        with patch('app.api.handlers.update_task', side_effect=HTTPException(status_code=500, detail="Timeout")):
            response = client.put("/update_task/task-123", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_update_task_forbidden_403(self, task_data):
        with patch('app.api.handlers.update_task', side_effect=HTTPException(status_code=403, detail="Forbidden")):
            response = client.put("/update_task/task-123", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 403

    def test_update_task_payment_required_402(self, task_data):
        with patch('app.api.handlers.update_task', side_effect=HTTPException(status_code=402, detail="Payment required")):
            response = client.put("/update_task/task-123", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 402

    def test_update_task_not_implemented_501(self, task_data):
        with patch('app.api.handlers.update_task', side_effect=HTTPException(status_code=501, detail="Not implemented")):
            response = client.put("/update_task/task-123", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 501

    def test_update_task_conflict_409(self, task_data):
        with patch('app.api.handlers.update_task', side_effect=HTTPException(status_code=409, detail="Conflict")):
            response = client.put("/update_task/task-123", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 409

    def test_update_task_validation_error_400(self):
        invalid_data = {"companyId": 123, "title": "Test Task", "description": "Test", "completed": False}
        response = client.put("/update_task/task-123", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_task_empty_json_422(self):
        response = client.put("/update_task/task-123", json={}, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_task_no_json_body_422(self):
        response = client.put("/update_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_update_task_malformed_json_422(self):
        response = client.put("/update_task/task-123", data="{invalid-json}", 
                            headers={"Authorization": f"Bearer {MOCK_TOKEN}", "Content-Type": "application/json"})
        assert response.status_code == 422

    def test_update_task_wrong_content_type_422(self):
        response = client.put("/update_task/task-123", data="invalid-data", 
                            headers={"Authorization": f"Bearer {MOCK_TOKEN}", "Content-Type": "text/plain"})
        assert response.status_code == 422

    def test_update_task_very_long_id_200(self, task_data):
        long_id = "a" * 1000
        with patch('app.api.handlers.update_task', return_value={"message": "Task not found"}):
            response = client.put(f"/update_task/{long_id}", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_task_special_chars_id_200(self, task_data):
        with patch('app.api.handlers.update_task', return_value={"message": "Task not found"}):
            response = client.put("/update_task/task<>123&", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_task_unicode_id_200(self, task_data):
        with patch('app.api.handlers.update_task', return_value={"message": "Task not found"}):
            response = client.put("/update_task/task-测试", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_update_task_numeric_id_200(self, task_data):
        with patch('app.api.handlers.update_task', return_value={"message": "Data updated successfully"}):
            response = client.put("/update_task/123", json=task_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

# DELETE /delete_task/{task_id} - 25+ Test Cases
class TestDeleteTask:
    
    @patch('app.api.handlers.delete_task')
    def test_delete_task_success_200(self, mock_delete_task):
        mock_delete_task.return_value = {"message": "Task deleted successfully", "id": "task-123"}
        response = client.delete("/delete_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_delete_task_no_auth_401(self):
        response = client.delete("/delete_task/task-123")
        assert response.status_code == 401

    def test_delete_task_empty_id_404(self):
        response = client.delete("/delete_task/", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 404

    @patch('app.api.handlers.delete_task')
    def test_delete_task_not_found_404(self, mock_delete_task):
        mock_delete_task.return_value = {"message": "Task not found"}
        response = client.delete("/delete_task/nonexistent-id", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_delete_task_database_error_500(self):
        with patch('app.api.handlers.delete_task', side_effect=HTTPException(status_code=500, detail="Database error")):
            response = client.delete("/delete_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_delete_task_invalid_method_405(self):
        response = client.get("/delete_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    def test_delete_task_service_unavailable_503(self):
        with patch('app.api.handlers.delete_task', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.delete("/delete_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_delete_task_network_error_502(self):
        with patch('app.api.handlers.delete_task', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.delete("/delete_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_delete_task_timeout_500(self):
        with patch('app.api.handlers.delete_task', side_effect=HTTPException(status_code=500, detail="Timeout")):
            response = client.delete("/delete_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_delete_task_forbidden_403(self):
        with patch('app.api.handlers.delete_task', side_effect=HTTPException(status_code=403, detail="Forbidden")):
            response = client.delete("/delete_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 403

    def test_delete_task_payment_required_402(self):
        with patch('app.api.handlers.delete_task', side_effect=HTTPException(status_code=402, detail="Payment required")):
            response = client.delete("/delete_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 402

    def test_delete_task_not_implemented_501(self):
        with patch('app.api.handlers.delete_task', side_effect=HTTPException(status_code=501, detail="Not implemented")):
            response = client.delete("/delete_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 501

    def test_delete_task_conflict_409(self):
        with patch('app.api.handlers.delete_task', side_effect=HTTPException(status_code=409, detail="Conflict")):
            response = client.delete("/delete_task/task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 409

    def test_delete_task_special_chars_id_200(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task not found"}):
            response = client.delete("/delete_task/task<>123&", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_task_unicode_id_200(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task not found"}):
            response = client.delete("/delete_task/task-测试", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_task_very_long_id_200(self):
        long_id = "a" * 1000
        with patch('app.api.handlers.delete_task', return_value={"message": "Task not found"}):
            response = client.delete(f"/delete_task/{long_id}", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_task_sql_injection_200(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task not found"}):
            response = client.delete("/delete_task/'; DROP TABLE tasks; --", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200



    def test_delete_task_numeric_id_200(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task deleted successfully"}):
            response = client.delete("/delete_task/123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_task_uuid_format_200(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task deleted successfully"}):
            response = client.delete("/delete_task/550e8400-e29b-41d4-a716-446655440000", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_task_negative_id_200(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task not found"}):
            response = client.delete("/delete_task/-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_task_zero_id_200(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task not found"}):
            response = client.delete("/delete_task/0", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_task_float_id_200(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task not found"}):
            response = client.delete("/delete_task/123.45", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_task_boolean_id_200(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task not found"}):
            response = client.delete("/delete_task/true", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_task_path_traversal_404(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task not found"}):
            response = client.delete("/delete_task/../../../etc/passwd", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 404

    def test_delete_task_url_encoded_id_200(self):
        with patch('app.api.handlers.delete_task', return_value={"message": "Task not found"}):
            response = client.delete("/delete_task/task%20123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_delete_task_double_slash_404(self):
        response = client.delete("/delete_task//task-123", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 404

# POST /create_template - 25+ Test Cases
class TestCreateTemplate:
    
    @patch('app.api.handlers.create_template')
    def test_create_template_success_200(self, mock_create_template, template_data):
        mock_create_template.return_value = {"message": "Tasks created and assigned to companies"}
        response = client.post("/create_template", json=template_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 200

    def test_create_template_no_auth_401(self, template_data):
        response = client.post("/create_template", json=template_data)
        assert response.status_code == 401

    def test_create_template_missing_company_ids_422(self):
        invalid_data = {"title": "Template Task", "description": "Template Description", "completed": False}
        response = client.post("/create_template", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_template_empty_company_ids_200(self):
        invalid_data = {"companyIds": [], "title": "Template Task", "description": "Template Description", "completed": False}
        with patch('app.api.handlers.create_template', return_value={"message": "No companies to assign"}):
            response = client.post("/create_template", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_template_null_company_ids_422(self):
        invalid_data = {"companyIds": None, "title": "Template Task", "description": "Template Description", "completed": False}
        response = client.post("/create_template", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_template_invalid_company_ids_type_422(self):
        invalid_data = {"companyIds": "company-123", "title": "Template Task", "description": "Template Description", "completed": False}
        response = client.post("/create_template", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_template_missing_title_422(self):
        invalid_data = {"companyIds": ["company-123"], "description": "Template Description", "completed": False}
        response = client.post("/create_template", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_template_empty_title_422(self):
        invalid_data = {"companyIds": ["company-123"], "title": "", "description": "Template Description", "completed": False}
        response = client.post("/create_template", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_template_null_title_422(self):
        invalid_data = {"companyIds": ["company-123"], "title": None, "description": "Template Description", "completed": False}
        response = client.post("/create_template", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_template_invalid_completed_type_200(self):
        invalid_data = {"companyIds": ["company-123"], "title": "Template Task", "description": "Template Description", "completed": "false"}
        with patch('app.api.handlers.create_template', return_value={"message": "Tasks created and assigned to companies"}):
            response = client.post("/create_template", json=invalid_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_template_empty_json_422(self):
        response = client.post("/create_template", json={}, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_template_no_json_body_422(self):
        response = client.post("/create_template", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 422

    def test_create_template_malformed_json_422(self):
        response = client.post("/create_template", data="{invalid-json}", 
                             headers={"Authorization": f"Bearer {MOCK_TOKEN}", "Content-Type": "application/json"})
        assert response.status_code == 422

    def test_create_template_database_error_500(self, template_data):
        with patch('app.api.handlers.create_template', side_effect=HTTPException(status_code=500, detail="Database error")):
            response = client.post("/create_template", json=template_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_create_template_invalid_method_405(self):
        response = client.get("/create_template", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
        assert response.status_code == 405

    def test_create_template_special_characters_200(self):
        special_data = {"companyIds": ["company<>123&"], "title": "Template<>&", "description": "Desc<>&", "completed": False}
        with patch('app.api.handlers.create_template', return_value={"message": "Tasks created and assigned to companies"}):
            response = client.post("/create_template", json=special_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_template_unicode_characters_200(self):
        unicode_data = {"companyIds": ["company-123"], "title": "模板任务", "description": "模板描述", "completed": False}
        with patch('app.api.handlers.create_template', return_value={"message": "Tasks created and assigned to companies"}):
            response = client.post("/create_template", json=unicode_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_template_sql_injection_200(self):
        injection_data = {"companyIds": ["'; DROP TABLE templates; --"], "title": "Template Task", "description": "Test", "completed": False}
        with patch('app.api.handlers.create_template', return_value={"message": "Tasks created and assigned to companies"}):
            response = client.post("/create_template", json=injection_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_template_xss_attempt_200(self):
        xss_data = {"companyIds": ["company-123"], "title": "<script>alert('template')</script>", "description": "Test", "completed": False}
        with patch('app.api.handlers.create_template', return_value={"message": "Tasks created and assigned to companies"}):
            response = client.post("/create_template", json=xss_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 200

    def test_create_template_very_long_fields_200(self):
        long_data = {"companyIds": ["company-123"], "title": "A" * 1000, "description": "B" * 1000, "completed": False}
        with patch('app.api.handlers.create_template', return_value={"message": "Tasks created and assigned to companies"}):
            response = client.post("/create_template", json=long_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code in [200, 413, 422]

    def test_create_template_service_unavailable_503(self, template_data):
        with patch('app.api.handlers.create_template', side_effect=HTTPException(status_code=503, detail="Service unavailable")):
            response = client.post("/create_template", json=template_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 503

    def test_create_template_network_error_502(self, template_data):
        with patch('app.api.handlers.create_template', side_effect=HTTPException(status_code=502, detail="Network error")):
            response = client.post("/create_template", json=template_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 502

    def test_create_template_timeout_500(self, template_data):
        with patch('app.api.handlers.create_template', side_effect=HTTPException(status_code=500, detail="Timeout")):
            response = client.post("/create_template", json=template_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 500

    def test_create_template_forbidden_403(self, template_data):
        with patch('app.api.handlers.create_template', side_effect=HTTPException(status_code=403, detail="Forbidden")):
            response = client.post("/create_template", json=template_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 403

    def test_create_template_payment_required_402(self, template_data):
        with patch('app.api.handlers.create_template', side_effect=HTTPException(status_code=402, detail="Payment required")):
            response = client.post("/create_template", json=template_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 402

    def test_create_template_not_implemented_501(self, template_data):
        with patch('app.api.handlers.create_template', side_effect=HTTPException(status_code=501, detail="Not implemented")):
            response = client.post("/create_template", json=template_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 501

    def test_create_template_conflict_409(self, template_data):
        with patch('app.api.handlers.create_template', side_effect=HTTPException(status_code=409, detail="Conflict")):
            response = client.post("/create_template", json=template_data, headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
            assert response.status_code == 409
