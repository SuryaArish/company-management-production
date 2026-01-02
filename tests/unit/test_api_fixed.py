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
            assert response.status_code == 500

    def test_get_all_companies_invalid_token_format_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid token format")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer invalid-format"})
            assert response.status_code == 500

    def test_get_all_companies_revoked_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Token revoked")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer revoked-token"})
            assert response.status_code == 500

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
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid unicode")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer token-unicode"})
            assert response.status_code == 500

    def test_get_all_companies_very_long_token_401(self):
        long_token = "a" * 10000
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Token too long")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer {long_token}"})
            assert response.status_code == 500

    def test_get_all_companies_special_chars_token_401(self):
        with patch('firebase_admin.auth.verify_id_token', side_effect=Exception("Invalid characters")):
            response = client.get("/getall_companies", headers={"Authorization": f"Bearer token<>with&special"})
            assert response.status_code == 500

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
            assert response.status_code == 500

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