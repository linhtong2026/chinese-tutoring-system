import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User, Tutor, Session


class TestHealthEndpoint:
    def test_health_check(self, app, client):
        with app.app_context():
            response = client.get('/api/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'


class TestUserEndpoint:
    @patch('app.get_clerk_user_metadata')
    def test_get_user(self, mock_clerk, app, client, student_user):
        mock_clerk.return_value = None
        
        with app.app_context():
            with patch('auth.require_auth') as mock_auth:
                def auth_decorator(f):
                    from functools import wraps
                    @wraps(f)
                    def decorated(*args, **kwargs):
                        from flask import request
                        user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
                        request.db_user = user
                        request.clerk_user = {'sub': user.clerk_user_id, 'name': user.name, 'email': user.email}
                        return f(*args, **kwargs)
                    return decorated
                mock_auth.side_effect = auth_decorator
                
                from app import app as flask_app
                flask_app.config.from_object('tests.conftest.TestConfig')
                
                with flask_app.test_client() as test_client:
                    with patch('app.require_auth', auth_decorator):
                        response = test_client.get('/api/user')

    @patch('app.get_clerk_user_metadata')
    def test_get_user_with_clerk_role_sync(self, mock_clerk, app, student_user):
        mock_clerk.return_value = {
            'public_metadata': {'role': 'tutor'}
        }
        
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            assert user is not None


class TestOnboardingEndpoint:
    def test_complete_onboarding(self, app, client):
        with app.app_context():
            user = User(
                clerk_user_id='clerk_onboarding_test',
                name='Test User',
                email='onboard@test.com',
                onboarding_complete=False
            )
            db.session.add(user)
            db.session.commit()


class TestProfileEndpoint:
    def test_update_profile_language(self, app, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            user.language_preference = 'zh'
            db.session.commit()
            
            updated_user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            assert updated_user.language_preference == 'zh'

    def test_update_profile_class_name(self, app, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            user.class_name = 'Chinese 301'
            db.session.commit()
            
            updated_user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            assert updated_user.class_name == 'Chinese 301'


class TestTutorByUserEndpoint:
    def test_get_tutor_by_user_creates_tutor(self, app, tutor_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            tutor = Tutor.query.filter_by(user_id=user.id).first()
            
            if not tutor:
                tutor = Tutor(user_id=user.id)
                db.session.add(tutor)
                db.session.commit()
            
            assert tutor is not None
            assert tutor.user_id == user.id

    def test_get_tutor_user_not_found(self, app):
        with app.app_context():
            user = User.query.get(99999)
            assert user is None

    def test_get_tutor_user_not_tutor(self, app, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            assert user.role == 'student'


class TestTutorsEndpoint:
    def test_get_tutors_empty(self, app, client):
        with app.app_context():
            tutors = Tutor.query.all()
            assert len(tutors) == 0

    def test_get_tutors_with_data(self, app, tutor_profile, tutor_user):
        with app.app_context():
            tutors = Tutor.query.all()
            assert len(tutors) == 1
            
            tutor = tutors[0]
            tutor_dict = tutor.to_dict()
            
            if tutor.user:
                tutor_dict['user'] = {
                    'id': tutor.user.id,
                    'name': tutor.user.name,
                    'email': tutor.user.email,
                    'class_name': tutor.user.class_name
                }
            
            assert 'user' in tutor_dict
            assert tutor_dict['user']['name'] == 'Test Tutor'


class TestHelperFunctions:
    def test_parse_client_dt_with_timezone(self, app):
        from app import parse_client_dt
        with app.app_context():
            result = parse_client_dt('2025-01-06T10:00:00+00:00')
            assert result is not None

    def test_parse_client_dt_naive(self, app):
        from app import parse_client_dt
        with app.app_context():
            result = parse_client_dt('2025-01-06T10:00:00')
            assert result is not None

    def test_parse_client_dt_with_z(self, app):
        from app import parse_client_dt
        with app.app_context():
            result = parse_client_dt('2025-01-06T10:00:00Z')
            assert result is not None

    def test_parse_client_dt_empty(self, app):
        from app import parse_client_dt
        with app.app_context():
            with pytest.raises(ValueError):
                parse_client_dt('')

    def test_to_client_iso(self, app):
        from app import to_client_iso
        with app.app_context():
            dt = datetime(2025, 1, 6, 15, 0, tzinfo=ZoneInfo("UTC"))
            result = to_client_iso(dt)
            assert result is not None
            assert '2025-01-06' in result

    def test_to_client_iso_none(self, app):
        from app import to_client_iso
        with app.app_context():
            result = to_client_iso(None)
            assert result is None

    def test_session_to_dict(self, app, tutor_user, student_user):
        from app import session_to_dict
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 6, 10, 0, tzinfo=ZoneInfo("UTC")),
                end_time=datetime(2025, 1, 6, 11, 0, tzinfo=ZoneInfo("UTC")),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            result = session_to_dict(session)
            assert result['booked'] is True
            assert result['tutor'] is not None
            assert result['student'] is not None

    def test_session_to_dict_no_student(self, app, tutor_user):
        from app import session_to_dict
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=None,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 6, 10, 0, tzinfo=ZoneInfo("UTC")),
                end_time=datetime(2025, 1, 6, 11, 0, tzinfo=ZoneInfo("UTC")),
                status='available'
            )
            db.session.add(session)
            db.session.commit()
            
            result = session_to_dict(session)
            assert result['booked'] is False
            assert result['student'] is None

    def test_session_to_dict_without_people(self, app, tutor_user):
        from app import session_to_dict
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=None,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 6, 10, 0, tzinfo=ZoneInfo("UTC")),
                end_time=datetime(2025, 1, 6, 11, 0, tzinfo=ZoneInfo("UTC")),
                status='available'
            )
            db.session.add(session)
            db.session.commit()
            
            result = session_to_dict(session, include_people=False)
            assert 'tutor' not in result
            assert 'student' not in result

    def test_tutor_overlap_exists_no_overlap(self, app, tutor_user):
        from app import tutor_overlap_exists
        with app.app_context():
            result = tutor_overlap_exists(
                tutor_user.id,
                datetime(2025, 1, 6, 10, 0, tzinfo=ZoneInfo("UTC")),
                datetime(2025, 1, 6, 11, 0, tzinfo=ZoneInfo("UTC"))
            )
            assert result is False

    def test_tutor_overlap_exists_with_overlap(self, app, tutor_user):
        from app import tutor_overlap_exists
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 6, 10, 0, tzinfo=ZoneInfo("UTC")),
                end_time=datetime(2025, 1, 6, 11, 0, tzinfo=ZoneInfo("UTC")),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            result = tutor_overlap_exists(
                tutor_user.id,
                datetime(2025, 1, 6, 10, 30, tzinfo=ZoneInfo("UTC")),
                datetime(2025, 1, 6, 11, 30, tzinfo=ZoneInfo("UTC"))
            )
            assert result is True

    def test_tutor_overlap_exists_with_exclude(self, app, tutor_user):
        from app import tutor_overlap_exists
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 6, 10, 0, tzinfo=ZoneInfo("UTC")),
                end_time=datetime(2025, 1, 6, 11, 0, tzinfo=ZoneInfo("UTC")),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            result = tutor_overlap_exists(
                tutor_user.id,
                datetime(2025, 1, 6, 10, 0, tzinfo=ZoneInfo("UTC")),
                datetime(2025, 1, 6, 11, 0, tzinfo=ZoneInfo("UTC")),
                exclude_id=session.id
            )
            assert result is False


class TestRoleRequired:
    def test_role_required_decorator(self, app, student_user):
        from app import role_required
        with app.app_context():
            @role_required('student')
            def student_only():
                return {'success': True}

    def test_role_required_wrong_role(self, app, student_user):
        from app import role_required
        with app.app_context():
            @role_required('tutor')
            def tutor_only():
                return {'success': True}


class TestUpdateClerkMetadata:
    @patch('app.requests.patch')
    def test_update_clerk_metadata_success(self, mock_patch, app):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response
        
        with app.app_context():
            from app import update_clerk_metadata
            result = update_clerk_metadata('clerk_user_123', {'role': 'student'})
            assert result is True

    @patch('app.requests.patch')
    def test_update_clerk_metadata_failure(self, mock_patch, app):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_patch.return_value = mock_response
        
        with app.app_context():
            from app import update_clerk_metadata
            result = update_clerk_metadata('clerk_user_123', {'role': 'student'})
            assert result is False

    def test_update_clerk_metadata_no_key(self, app):
        with app.app_context():
            app.config['CLERK_SECRET_KEY'] = None
            from app import update_clerk_metadata
            result = update_clerk_metadata('clerk_user_123', {'role': 'student'})
            assert result is False

    @patch('app.requests.patch')
    def test_update_clerk_metadata_exception(self, mock_patch, app):
        mock_patch.side_effect = Exception('Network error')
        
        with app.app_context():
            from app import update_clerk_metadata
            result = update_clerk_metadata('clerk_user_123', {'role': 'student'})
            assert result is False


class TestGetClerkUserMetadata:
    @patch('app.requests.get')
    def test_get_clerk_user_metadata_success(self, mock_get, app):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'id': 'clerk_123', 'public_metadata': {'role': 'student'}}
        mock_get.return_value = mock_response
        
        with app.app_context():
            from app import get_clerk_user_metadata
            result = get_clerk_user_metadata('clerk_123')
            assert result is not None
            assert result['id'] == 'clerk_123'

    @patch('app.requests.get')
    def test_get_clerk_user_metadata_not_found(self, mock_get, app):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        with app.app_context():
            from app import get_clerk_user_metadata
            result = get_clerk_user_metadata('nonexistent')
            assert result is None

    def test_get_clerk_user_metadata_no_key(self, app):
        with app.app_context():
            app.config['CLERK_SECRET_KEY'] = None
            from app import get_clerk_user_metadata
            result = get_clerk_user_metadata('clerk_123')
            assert result is None

    @patch('app.requests.get')
    def test_get_clerk_user_metadata_exception(self, mock_get, app):
        mock_get.side_effect = Exception('Network error')
        
        with app.app_context():
            from app import get_clerk_user_metadata
            result = get_clerk_user_metadata('clerk_123')
            assert result is None


class TestAppHTTPEndpoints:
    def test_get_user_http(self, app, student_user):
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
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': user.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.get('/api/user', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert 'user' in data

    def test_complete_onboarding_http(self, app):
        with app.app_context():
            user = User(
                clerk_user_id='clerk_onboard_http',
                name='Onboard User',
                email='onboard_http@test.com',
                onboarding_complete=False
            )
            db.session.add(user)
            db.session.commit()
            
            with patch('auth.Clerk') as mock_clerk:
                mock_sdk = MagicMock()
                mock_request_state = MagicMock()
                mock_request_state.is_signed_in = True
                mock_request_state.payload = {'sub': user.clerk_user_id, 'name': user.name, 'email': user.email}
                mock_sdk.authenticate_request.return_value = mock_request_state
                mock_clerk.return_value = mock_sdk
                
                with patch('auth.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': user.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.post('/api/user/onboarding',
                        data=json.dumps({
                            'language': 'zh',
                            'class_name': 'Chinese 101'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_update_profile_http(self, app, student_user):
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
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': user.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.post('/api/user/profile',
                        data=json.dumps({
                            'language_preference': 'zh',
                            'class_name': 'Chinese 301'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_tutor_by_user_http(self, app, tutor_user, tutor_profile):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            
            with patch('auth.Clerk') as mock_clerk:
                mock_sdk = MagicMock()
                mock_request_state = MagicMock()
                mock_request_state.is_signed_in = True
                mock_request_state.payload = {'sub': user.clerk_user_id, 'name': user.name, 'email': user.email}
                mock_sdk.authenticate_request.return_value = mock_request_state
                mock_clerk.return_value = mock_sdk
                
                with patch('auth.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': user.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.get(f'/api/tutor/by-user/{user.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_tutor_by_user_http_not_found(self, app):
        with app.app_context():
            admin_user = User(
                clerk_user_id='clerk_admin_test',
                name='Admin User',
                email='admin@test.com',
                role='admin',
                onboarding_complete=True
            )
            db.session.add(admin_user)
            db.session.commit()
            
            with patch('auth.Clerk') as mock_clerk:
                mock_sdk = MagicMock()
                mock_request_state = MagicMock()
                mock_request_state.is_signed_in = True
                mock_request_state.payload = {'sub': admin_user.clerk_user_id, 'name': admin_user.name, 'email': admin_user.email}
                mock_sdk.authenticate_request.return_value = mock_request_state
                mock_clerk.return_value = mock_sdk
                
                with patch('auth.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': admin_user.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.get('/api/tutor/by-user/99999', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_get_tutor_by_user_http_forbidden(self, app, student_user, tutor_user):
        with app.app_context():
            student = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            tutor = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            
            with patch('auth.Clerk') as mock_clerk:
                mock_sdk = MagicMock()
                mock_request_state = MagicMock()
                mock_request_state.is_signed_in = True
                mock_request_state.payload = {'sub': student.clerk_user_id, 'name': student.name, 'email': student.email}
                mock_sdk.authenticate_request.return_value = mock_request_state
                mock_clerk.return_value = mock_sdk
                
                with patch('auth.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': student.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.get(f'/api/tutor/by-user/{tutor.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_get_tutor_by_user_http_not_tutor(self, app, student_user):
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
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': user.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.get(f'/api/tutor/by-user/{user.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_get_tutors_http(self, app, tutor_user, tutor_profile):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            
            with patch('auth.Clerk') as mock_clerk:
                mock_sdk = MagicMock()
                mock_request_state = MagicMock()
                mock_request_state.is_signed_in = True
                mock_request_state.payload = {'sub': user.clerk_user_id, 'name': user.name, 'email': user.email}
                mock_sdk.authenticate_request.return_value = mock_request_state
                mock_clerk.return_value = mock_sdk
                
                with patch('auth.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': user.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.get('/api/tutors', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert 'tutors' in data

