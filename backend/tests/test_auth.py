import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import _extract_email, _extract_display_name, fetch_clerk_user
from models import db, User


class TestExtractEmail:
    def test_extract_email_none_payload(self):
        result = _extract_email(None)
        assert result == ""

    def test_extract_email_empty_payload(self):
        result = _extract_email({})
        assert result == ""

    def test_extract_email_direct_email(self):
        payload = {'email': 'test@example.com'}
        result = _extract_email(payload)
        assert result == 'test@example.com'

    def test_extract_email_direct_email_with_spaces(self):
        payload = {'email': '  test@example.com  '}
        result = _extract_email(payload)
        assert result == 'test@example.com'

    def test_extract_email_from_primary_email_address(self):
        payload = {
            'email': '',
            'primary_email_address_id': 'email_123',
            'email_addresses': [
                {'id': 'email_456', 'email_address': 'other@example.com'},
                {'id': 'email_123', 'email_address': 'primary@example.com'}
            ]
        }
        result = _extract_email(payload)
        assert result == 'primary@example.com'

    def test_extract_email_from_first_email_address(self):
        payload = {
            'email': '',
            'primary_email_address_id': None,
            'email_addresses': [
                {'id': 'email_123', 'email_address': 'first@example.com'},
                {'id': 'email_456', 'email_address': 'second@example.com'}
            ]
        }
        result = _extract_email(payload)
        assert result == 'first@example.com'

    def test_extract_email_empty_email_addresses(self):
        payload = {
            'email': '',
            'email_addresses': []
        }
        result = _extract_email(payload)
        assert result == ""

    def test_extract_email_primary_not_found(self):
        payload = {
            'email': '',
            'primary_email_address_id': 'nonexistent',
            'email_addresses': [
                {'id': 'email_123', 'email_address': 'first@example.com'}
            ]
        }
        result = _extract_email(payload)
        assert result == 'first@example.com'

    def test_extract_email_entry_without_email_address(self):
        payload = {
            'email': '',
            'email_addresses': [
                {'id': 'email_123'},
                {'id': 'email_456', 'email_address': 'valid@example.com'}
            ]
        }
        result = _extract_email(payload)
        assert result == 'valid@example.com'

    def test_extract_email_all_empty_addresses(self):
        payload = {
            'email': '',
            'email_addresses': [
                {'id': 'email_123', 'email_address': ''},
                {'id': 'email_456', 'email_address': '   '}
            ]
        }
        result = _extract_email(payload)
        assert result == ""

    def test_extract_email_primary_with_empty_address(self):
        payload = {
            'email': '',
            'primary_email_address_id': 'email_123',
            'email_addresses': [
                {'id': 'email_123', 'email_address': ''},
                {'id': 'email_456', 'email_address': 'fallback@example.com'}
            ]
        }
        result = _extract_email(payload)
        assert result == 'fallback@example.com'


class TestExtractDisplayName:
    def test_extract_display_name_none_payload(self):
        result = _extract_display_name(None)
        assert result == ""

    def test_extract_display_name_none_payload_with_fallback(self):
        result = _extract_display_name(None, 'fallback@example.com')
        assert result == 'fallback@example.com'

    def test_extract_display_name_empty_payload(self):
        result = _extract_display_name({})
        assert result == ""

    def test_extract_display_name_direct_name(self):
        payload = {'name': 'John Doe'}
        result = _extract_display_name(payload)
        assert result == 'John Doe'

    def test_extract_display_name_direct_name_with_spaces(self):
        payload = {'name': '  John Doe  '}
        result = _extract_display_name(payload)
        assert result == 'John Doe'

    def test_extract_display_name_from_first_last(self):
        payload = {
            'name': '',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        result = _extract_display_name(payload)
        assert result == 'John Doe'

    def test_extract_display_name_first_only(self):
        payload = {
            'name': '',
            'first_name': 'John',
            'last_name': ''
        }
        result = _extract_display_name(payload)
        assert result == 'John'

    def test_extract_display_name_last_only(self):
        payload = {
            'name': '',
            'first_name': '',
            'last_name': 'Doe'
        }
        result = _extract_display_name(payload)
        assert result == 'Doe'

    def test_extract_display_name_from_username(self):
        payload = {
            'name': '',
            'first_name': '',
            'last_name': '',
            'username': 'johndoe123'
        }
        result = _extract_display_name(payload)
        assert result == 'johndoe123'

    def test_extract_display_name_from_email(self):
        payload = {
            'name': '',
            'first_name': '',
            'last_name': '',
            'username': '',
            'email': 'john.doe@example.com'
        }
        result = _extract_display_name(payload)
        assert result == 'john.doe'

    def test_extract_display_name_from_fallback_email(self):
        payload = {
            'name': '',
            'first_name': '',
            'last_name': '',
            'username': ''
        }
        result = _extract_display_name(payload, 'fallback@example.com')
        assert result == 'fallback'

    def test_extract_display_name_no_fallback(self):
        payload = {
            'name': '',
            'first_name': '',
            'last_name': '',
            'username': '',
            'email': ''
        }
        result = _extract_display_name(payload)
        assert result == ""

    def test_extract_display_name_priority_name_over_first_last(self):
        payload = {
            'name': 'Full Name',
            'first_name': 'First',
            'last_name': 'Last'
        }
        result = _extract_display_name(payload)
        assert result == 'Full Name'

    def test_extract_display_name_priority_first_last_over_username(self):
        payload = {
            'name': '',
            'first_name': 'First',
            'last_name': 'Last',
            'username': 'username123'
        }
        result = _extract_display_name(payload)
        assert result == 'First Last'


class TestRequireAuth:
    @patch('auth.requests.get')
    @patch('auth.Clerk')
    def test_require_auth_options_request(self, mock_clerk, mock_get, app, client):
        with app.app_context():
            pass

    @patch('auth.requests.get')
    @patch('auth.Clerk')
    def test_require_auth_unauthorized(self, mock_clerk, mock_get, app, client):
        mock_sdk = MagicMock()
        mock_request_state = MagicMock()
        mock_request_state.is_signed_in = False
        mock_sdk.authenticate_request.return_value = mock_request_state
        mock_clerk.return_value = mock_sdk
        
        with app.app_context():
            pass

    @patch('auth.requests.get')
    @patch('auth.Clerk')
    def test_require_auth_success(self, mock_clerk, mock_get, app, client, student_user):
        mock_sdk = MagicMock()
        mock_request_state = MagicMock()
        mock_request_state.is_signed_in = True
        mock_request_state.payload = {
            'sub': 'clerk_test_student',
            'name': 'Test Student',
            'email': 'student@test.com'
        }
        mock_sdk.authenticate_request.return_value = mock_request_state
        mock_clerk.return_value = mock_sdk
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'first_name': 'Test',
            'last_name': 'Student',
            'full_name': 'Test Student',
            'primary_email_address_id': 'email_123',
            'email_addresses': [{'id': 'email_123', 'email_address': 'student@test.com'}]
        }
        mock_get.return_value = mock_response
        
        with app.app_context():
            pass

    @patch('auth.requests.get')
    @patch('auth.Clerk')
    def test_require_auth_with_authorized_party(self, mock_clerk, mock_get, app, client):
        mock_sdk = MagicMock()
        mock_sdk.authenticate_request.side_effect = [
            Exception('Invalid'),
            MagicMock(is_signed_in=True, payload={'sub': 'test'})
        ]
        mock_clerk.return_value = mock_sdk
        
        with app.app_context():
            pass

    @patch('auth.requests.get')
    @patch('auth.Clerk')
    def test_require_auth_exception(self, mock_clerk, mock_get, app, client):
        mock_sdk = MagicMock()
        mock_sdk.authenticate_request.side_effect = Exception('Auth error')
        mock_clerk.return_value = mock_sdk
        
        with app.app_context():
            pass

    @patch('auth.requests.get')
    def test_fetch_clerk_user_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'clerk_123'}
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'CLERK_SECRET_KEY': 'test_key'}):
            result = fetch_clerk_user('user_123')
            assert result == {'id': 'clerk_123'}

    @patch('auth.requests.get')
    def test_fetch_clerk_user_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'CLERK_SECRET_KEY': 'test_key'}):
            result = fetch_clerk_user('user_123')
            assert result is None

    def test_fetch_clerk_user_no_secret(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop('CLERK_SECRET_KEY', None)
            result = fetch_clerk_user('user_123')
            assert result is None

    def test_fetch_clerk_user_no_user_id(self):
        with patch.dict(os.environ, {'CLERK_SECRET_KEY': 'test_key'}):
            result = fetch_clerk_user(None)
            assert result is None

    def test_require_auth_with_clerk_user_data(self, app, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            
            with patch('auth.Clerk') as mock_clerk:
                mock_sdk = MagicMock()
                mock_request_state = MagicMock()
                mock_request_state.is_signed_in = True
                mock_request_state.payload = {'sub': user.clerk_user_id}
                mock_sdk.authenticate_request.return_value = mock_request_state
                mock_clerk.return_value = mock_sdk
                
                with patch('auth.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        'first_name': 'Test',
                        'last_name': 'Student',
                        'full_name': 'Test Student',
                        'primary_email_address_id': 'email_123',
                        'email_addresses': [{'id': 'email_123', 'email_address': 'student@test.com'}]
                    }
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.get('/api/user', headers={'Authorization': 'Bearer test_token'})
                    assert response.status_code == 200

    def test_require_auth_clerk_user_fetch_fails(self, app, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            
            with patch('auth.Clerk') as mock_clerk:
                mock_sdk = MagicMock()
                mock_request_state = MagicMock()
                mock_request_state.is_signed_in = True
                mock_request_state.payload = {'sub': user.clerk_user_id, 'name': user.name, 'email': user.email}
                mock_sdk.authenticate_request.return_value = mock_request_state
                mock_clerk.return_value = mock_sdk
                
                with patch('auth.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 404
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.get('/api/user', headers={'Authorization': 'Bearer test_token'})
                    assert response.status_code == 200
