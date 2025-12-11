import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User, Tutor, Availability, Session


class TestAvailabilityModel:
    def test_create_availability(self, app, tutor_profile):
        with app.app_context():
            av = Availability(
                tutor_id=tutor_profile.id,
                day_of_week=2,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 12, 0),
                session_type='online',
                is_recurring=True
            )
            db.session.add(av)
            db.session.commit()
            
            assert av.id is not None
            assert av.session_type == 'online'

    def test_get_availabilities(self, app, tutor_profile, availability):
        with app.app_context():
            avs = Availability.query.all()
            assert len(avs) >= 1


class TestAvailabilityHTTPEndpoints:
    def test_create_availability_http_success(self, app, tutor_user, tutor_profile):
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
                    response = client.post('/api/availability', 
                        data=json.dumps({
                            'day_of_week': 1,
                            'start_time': '2025-01-06T09:00:00',
                            'end_time': '2025-01-06T17:00:00',
                            'session_type': 'online',
                            'is_recurring': True
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 201

    def test_create_availability_http_missing_fields(self, app, tutor_user, tutor_profile):
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
                    response = client.post('/api/availability', 
                        data=json.dumps({'day_of_week': 1}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_create_availability_http_invalid_session_type(self, app, tutor_user, tutor_profile):
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
                    response = client.post('/api/availability', 
                        data=json.dumps({
                            'day_of_week': 1,
                            'start_time': '2025-01-06T09:00:00',
                            'end_time': '2025-01-06T17:00:00',
                            'session_type': 'invalid'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_create_availability_http_invalid_datetime(self, app, tutor_user, tutor_profile):
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
                    response = client.post('/api/availability', 
                        data=json.dumps({
                            'day_of_week': 1,
                            'start_time': 'invalid',
                            'end_time': 'invalid',
                            'session_type': 'online'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_create_availability_http_not_tutor(self, app, student_user):
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
                    response = client.post('/api/availability', 
                        data=json.dumps({
                            'day_of_week': 1,
                            'start_time': '2025-01-06T09:00:00',
                            'end_time': '2025-01-06T17:00:00',
                            'session_type': 'online'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_get_availability_http_all(self, app, tutor_user, tutor_profile, availability):
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
                    response = client.get('/api/availability', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_availability_http_by_user_id(self, app, tutor_user, tutor_profile, availability):
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
                    response = client.get(f'/api/availability?user_id={user.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_availability_http_by_user_id_not_found(self, app, tutor_user):
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
                    response = client.get('/api/availability?user_id=99999', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_get_availability_http_by_tutor_id(self, app, tutor_user, tutor_profile, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            tutor = Tutor.query.filter_by(user_id=user.id).first()
            
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
                    response = client.get(f'/api/availability?tutor_id={tutor.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_availability_http_by_tutor_id_not_found(self, app, tutor_user):
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
                    response = client.get('/api/availability?tutor_id=99999', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_update_availability_http_success(self, app, tutor_user, tutor_profile, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            av = Availability.query.first()
            
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
                    response = client.put(f'/api/availability/{av.id}',
                        data=json.dumps({'day_of_week': 3, 'session_type': 'in-person', 'is_recurring': False}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_update_availability_http_not_found(self, app, tutor_user):
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
                    response = client.put('/api/availability/99999',
                        data=json.dumps({'day_of_week': 3}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_update_availability_http_invalid_times(self, app, tutor_user, tutor_profile, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            av = Availability.query.first()
            
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
                    response = client.put(f'/api/availability/{av.id}',
                        data=json.dumps({'start_time': 'invalid'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_delete_availability_http_success(self, app, tutor_user, tutor_profile, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            av = Availability.query.first()
            
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
                    response = client.delete(f'/api/availability/{av.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_delete_availability_http_not_found(self, app, tutor_user):
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
                    response = client.delete('/api/availability/99999', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_create_availability_http_creates_tutor(self, app, tutor_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            Tutor.query.filter_by(user_id=user.id).delete()
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
                    response = client.post('/api/availability', 
                        data=json.dumps({
                            'day_of_week': 1,
                            'start_time': '2025-01-06T09:00:00',
                            'end_time': '2025-01-06T17:00:00',
                            'session_type': 'online'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 201

    def test_update_availability_http_end_time_only(self, app, tutor_user, tutor_profile, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            av = Availability.query.first()
            
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
                    response = client.put(f'/api/availability/{av.id}',
                        data=json.dumps({'end_time': '2025-01-06T18:00:00'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_all_availability_http(self, app, tutor_user, tutor_profile, availability):
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
                    response = client.get('/api/availability/all', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert 'availabilities' in data
                    assert len(data['availabilities']) > 0
                    assert 'tutor_name' in data['availabilities'][0]

    def test_update_availability_http_not_tutor(self, app, student_user, tutor_profile, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            av = Availability.query.first()
            
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
                    response = client.put(f'/api/availability/{av.id}',
                        data=json.dumps({'day_of_week': 3}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_update_availability_http_not_owner(self, app, tutor_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            
            other_user = User(clerk_user_id='clerk_other_tutor', name='Other Tutor', email='other@test.com', role='tutor')
            db.session.add(other_user)
            db.session.commit()
            
            other_tutor = Tutor(user_id=other_user.id)
            db.session.add(other_tutor)
            db.session.commit()
            
            av = Availability(
                tutor_id=other_tutor.id,
                day_of_week=2,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 12, 0),
                session_type='online',
                is_recurring=True
            )
            db.session.add(av)
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
                    response = client.put(f'/api/availability/{av.id}',
                        data=json.dumps({'day_of_week': 3}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_update_availability_http_invalid_session_type(self, app, tutor_user, tutor_profile, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            av = Availability.query.first()
            
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
                    response = client.put(f'/api/availability/{av.id}',
                        data=json.dumps({'session_type': 'invalid-type'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_update_availability_http_with_time_change_recurring(self, app, tutor_user, tutor_profile):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            tutor = Tutor.query.filter_by(user_id=user.id).first()
            
            av = Availability(
                tutor_id=tutor.id,
                day_of_week=3,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 12, 0),
                session_type='online',
                is_recurring=True
            )
            db.session.add(av)
            db.session.commit()
            
            session = Session(
                tutor_id=user.id,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 10, 0),
                session_type='online',
                status='available'
            )
            db.session.add(session)
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
                    response = client.put(f'/api/availability/{av.id}',
                        data=json.dumps({'start_time': '2025-01-08T10:00:00'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200
                    sessions_after = Session.query.filter_by(tutor_id=user.id, status='available').all()
                    assert len(sessions_after) == 0

    def test_update_availability_http_with_time_change_non_recurring(self, app, tutor_user, tutor_profile):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            tutor = Tutor.query.filter_by(user_id=user.id).first()
            
            av = Availability(
                tutor_id=tutor.id,
                day_of_week=2,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 12, 0),
                session_type='online',
                is_recurring=False
            )
            db.session.add(av)
            db.session.commit()
            
            session = Session(
                tutor_id=user.id,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 10, 0),
                session_type='online',
                status='available'
            )
            db.session.add(session)
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
                    response = client.put(f'/api/availability/{av.id}',
                        data=json.dumps({'start_time': '2025-01-08T10:00:00'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_delete_availability_http_not_tutor(self, app, student_user, tutor_profile, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            av = Availability.query.first()
            
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
                    response = client.delete(f'/api/availability/{av.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_delete_availability_http_not_owner(self, app, tutor_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            
            other_user = User(clerk_user_id='clerk_other_tutor2', name='Other Tutor', email='other2@test.com', role='tutor')
            db.session.add(other_user)
            db.session.commit()
            
            other_tutor = Tutor(user_id=other_user.id)
            db.session.add(other_tutor)
            db.session.commit()
            
            av = Availability(
                tutor_id=other_tutor.id,
                day_of_week=2,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 12, 0),
                session_type='online',
                is_recurring=True
            )
            db.session.add(av)
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
                    response = client.delete(f'/api/availability/{av.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_delete_availability_http_with_recurring_sessions(self, app, tutor_user, tutor_profile):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            tutor = Tutor.query.filter_by(user_id=user.id).first()
            
            av = Availability(
                tutor_id=tutor.id,
                day_of_week=3,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 12, 0),
                session_type='online',
                is_recurring=True
            )
            db.session.add(av)
            db.session.commit()
            
            session = Session(
                tutor_id=user.id,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 10, 0),
                session_type='online',
                status='available'
            )
            db.session.add(session)
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
                    response = client.delete(f'/api/availability/{av.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200
                    sessions_after = Session.query.filter_by(tutor_id=user.id, status='available').all()
                    assert len(sessions_after) == 0

    def test_delete_availability_http_with_non_recurring_sessions(self, app, tutor_user, tutor_profile):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            tutor = Tutor.query.filter_by(user_id=user.id).first()
            
            av = Availability(
                tutor_id=tutor.id,
                day_of_week=2,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 12, 0),
                session_type='online',
                is_recurring=False
            )
            db.session.add(av)
            db.session.commit()
            
            session = Session(
                tutor_id=user.id,
                start_time=datetime(2025, 1, 8, 9, 0),
                end_time=datetime(2025, 1, 8, 10, 0),
                session_type='online',
                status='available'
            )
            db.session.add(session)
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
                    response = client.delete(f'/api/availability/{av.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_delete_availability_http_tutor_user_not_found(self, app, tutor_user, tutor_profile, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            av = Availability.query.first()
            tutor = Tutor.query.filter_by(user_id=user.id).first()
            
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
                    
                    with patch('routes.availability.User') as mock_user_class:
                        mock_user_query = MagicMock()
                        mock_user_query.get.return_value = None
                        mock_user_class.query = mock_user_query
                        
                        client = app.test_client()
                        response = client.delete(f'/api/availability/{av.id}', headers={'Authorization': 'Bearer test_token'})
                        
                        assert response.status_code == 404
