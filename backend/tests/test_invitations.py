import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User, Invitation


class TestInvitationModel:
    def test_invitation_creation(self, app, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='newtutor@test.com',
                role='tutor',
                invited_by=professor_user.id
            )
            db.session.add(invitation)
            db.session.commit()
            
            assert invitation.id is not None
            assert invitation.email == 'newtutor@test.com'
            assert invitation.role == 'tutor'
            assert invitation.status == 'pending'
            assert invitation.token is not None
            assert len(invitation.token) == 36
            assert invitation.expires_at is not None

    def test_invitation_to_dict(self, app, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id
            )
            db.session.add(invitation)
            db.session.commit()
            
            inv_dict = invitation.to_dict()
            
            assert inv_dict['id'] == invitation.id
            assert inv_dict['email'] == 'test@test.com'
            assert inv_dict['role'] == 'tutor'
            assert inv_dict['token'] == invitation.token
            assert inv_dict['invited_by'] == professor_user.id
            assert inv_dict['status'] == 'pending'
            assert 'created_at' in inv_dict
            assert 'expires_at' in inv_dict

    def test_invitation_is_expired_false(self, app, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id,
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
            db.session.add(invitation)
            db.session.commit()
            
            assert invitation.is_expired() is False

    def test_invitation_is_expired_true(self, app, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id,
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(invitation)
            db.session.commit()
            
            assert invitation.is_expired() is True

    def test_invitation_is_valid_true(self, app, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id,
                status='pending',
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
            db.session.add(invitation)
            db.session.commit()
            
            assert invitation.is_valid() is True

    def test_invitation_is_valid_false_accepted(self, app, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id,
                status='accepted',
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
            db.session.add(invitation)
            db.session.commit()
            
            assert invitation.is_valid() is False

    def test_invitation_is_valid_false_expired(self, app, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id,
                status='pending',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(invitation)
            db.session.commit()
            
            assert invitation.is_valid() is False

    def test_invitation_relationship_with_inviter(self, app, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id
            )
            db.session.add(invitation)
            db.session.commit()
            
            assert invitation.inviter is not None
            assert invitation.inviter.id == professor_user.id
            assert invitation.inviter.name == professor_user.name


class TestValidateEmail:
    def test_validate_email_valid(self, app):
        with app.app_context():
            from routes.invitations import validate_email
            
            assert validate_email('test@example.com') is True
            assert validate_email('user.name@example.com') is True
            assert validate_email('user+tag@example.co.uk') is True
            assert validate_email('firstname-lastname@example-domain.com') is True

    def test_validate_email_invalid(self, app):
        with app.app_context():
            from routes.invitations import validate_email
            
            assert validate_email('invalid') is False
            assert validate_email('invalid@') is False
            assert validate_email('@example.com') is False
            assert validate_email('invalid@.com') is False
            assert validate_email('') is False


class TestSendInvitation:
    def test_send_invitation_success(self, app, professor_auth_client, mock_resend):
        with app.app_context():
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': 'newtutor@test.com',
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert 'invitation' in data
            assert data['invitation']['email'] == 'newtutor@test.com'
            assert data['invitation']['role'] == 'tutor'
            assert data['invitation']['status'] == 'pending'
            
            invitation = Invitation.query.filter_by(email='newtutor@test.com').first()
            assert invitation is not None

    def test_send_invitation_forbidden_non_professor(self, app, tutor_auth_client):
        with app.app_context():
            response = tutor_auth_client.post(
                '/api/invitations',
                json={
                    'email': 'newtutor@test.com',
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 403
            data = response.get_json()
            assert data['error'] == 'Forbidden'

    def test_send_invitation_forbidden_student(self, app, auth_client):
        with app.app_context():
            response = auth_client.post(
                '/api/invitations',
                json={
                    'email': 'newtutor@test.com',
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 403

    def test_send_invitation_missing_email(self, app, professor_auth_client):
        with app.app_context():
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'email and role are required' in data['error']

    def test_send_invitation_missing_role(self, app, professor_auth_client):
        with app.app_context():
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': 'newtutor@test.com'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'email and role are required' in data['error']

    def test_send_invitation_invalid_email(self, app, professor_auth_client):
        with app.app_context():
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': 'invalid-email',
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert 'Invalid email format' in data['error']

    def test_send_invitation_invalid_role(self, app, professor_auth_client):
        with app.app_context():
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': 'newuser@test.com',
                    'role': 'admin'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 400
            data = response.get_json()
            assert "role must be 'tutor' or 'professor'" in data['error']

    def test_send_invitation_existing_user(self, app, professor_auth_client, tutor_user):
        with app.app_context():
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': tutor_user.email,
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 409
            data = response.get_json()
            assert 'User with this email already exists' in data['error']

    def test_send_invitation_pending_exists(self, app, professor_auth_client, professor_user):
        with app.app_context():
            existing_invitation = Invitation(
                email='pending@test.com',
                role='tutor',
                invited_by=professor_user.id,
                status='pending',
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
            db.session.add(existing_invitation)
            db.session.commit()
            
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': 'pending@test.com',
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 409
            data = response.get_json()
            assert 'A pending invitation already exists' in data['error']

    def test_send_invitation_expired_allows_new(self, app, professor_auth_client, professor_user, mock_resend):
        with app.app_context():
            expired_invitation = Invitation(
                email='expired@test.com',
                role='tutor',
                invited_by=professor_user.id,
                status='pending',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(expired_invitation)
            db.session.commit()
            
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': 'expired@test.com',
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True

    def test_send_invitation_accepted_allows_new(self, app, professor_auth_client, professor_user, mock_resend):
        with app.app_context():
            accepted_invitation = Invitation(
                email='accepted@test.com',
                role='tutor',
                invited_by=professor_user.id,
                status='accepted',
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
            db.session.add(accepted_invitation)
            db.session.commit()
            
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': 'accepted@test.com',
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True

    @patch('services.email_service.resend')
    def test_send_invitation_email_failure(self, mock_resend_module, app, professor_auth_client):
        mock_resend_module.Emails.send.side_effect = Exception('Email error')
        
        with app.app_context():
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': 'newtutor@test.com',
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 201
            data = response.get_json()
            assert 'warning' in data
            assert 'email failed to send' in data['warning']
            assert 'invitation' in data

    def test_send_invitation_empty_email(self, app, professor_auth_client):
        with app.app_context():
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': '   ',
                    'role': 'tutor'
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 400

    def test_send_invitation_empty_role(self, app, professor_auth_client):
        with app.app_context():
            response = professor_auth_client.post(
                '/api/invitations',
                json={
                    'email': 'test@test.com',
                    'role': '   '
                },
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 400


class TestGetInvitations:
    def test_get_invitations_success(self, app, professor_auth_client, professor_user):
        with app.app_context():
            invitation1 = Invitation(
                email='tutor1@test.com',
                role='tutor',
                invited_by=professor_user.id
            )
            invitation2 = Invitation(
                email='tutor2@test.com',
                role='professor',
                invited_by=professor_user.id
            )
            db.session.add_all([invitation1, invitation2])
            db.session.commit()
            
            response = professor_auth_client.get(
                '/api/invitations',
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert len(data['invitations']) >= 2
            
            emails = [inv['email'] for inv in data['invitations']]
            assert 'tutor1@test.com' in emails
            assert 'tutor2@test.com' in emails

    def test_get_invitations_includes_inviter_name(self, app, professor_auth_client, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id
            )
            db.session.add(invitation)
            db.session.commit()
            
            response = professor_auth_client.get(
                '/api/invitations',
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            test_invitation = next(
                (inv for inv in data['invitations'] if inv['email'] == 'test@test.com'),
                None
            )
            assert test_invitation is not None
            assert 'invited_by_name' in test_invitation
            assert test_invitation['invited_by_name'] == professor_user.name

    def test_get_invitations_forbidden_non_professor(self, app, tutor_auth_client):
        with app.app_context():
            response = tutor_auth_client.get(
                '/api/invitations',
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 403
            data = response.get_json()
            assert data['error'] == 'Forbidden'

    def test_get_invitations_forbidden_student(self, app, auth_client):
        with app.app_context():
            response = auth_client.get(
                '/api/invitations',
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 403

    def test_get_invitations_empty_list(self, app, professor_auth_client):
        with app.app_context():
            response = professor_auth_client.get(
                '/api/invitations',
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['invitations'], list)

    def test_get_invitations_ordered_by_created_at(self, app, professor_auth_client, professor_user):
        with app.app_context():
            invitation1 = Invitation(
                email='old@test.com',
                role='tutor',
                invited_by=professor_user.id,
                created_at=datetime.utcnow() - timedelta(days=2)
            )
            invitation2 = Invitation(
                email='new@test.com',
                role='tutor',
                invited_by=professor_user.id,
                created_at=datetime.utcnow()
            )
            db.session.add_all([invitation1, invitation2])
            db.session.commit()
            
            response = professor_auth_client.get(
                '/api/invitations',
                headers={'Authorization': 'Bearer test_token'}
            )
            
            assert response.status_code == 200
            data = response.get_json()
            
            if len(data['invitations']) >= 2:
                assert data['invitations'][0]['email'] == 'new@test.com'


class TestCheckInvitation:
    def test_check_invitation_valid(self, app, client, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id,
                status='pending',
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
            db.session.add(invitation)
            db.session.commit()
            token = invitation.token
            
            response = client.get(f'/api/invitations/check/{token}')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['invitation']['email'] == 'test@test.com'
            assert data['invitation']['role'] == 'tutor'

    def test_check_invitation_not_found(self, app, client):
        with app.app_context():
            response = client.get('/api/invitations/check/nonexistent-token')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'Invitation not found' in data['error']

    def test_check_invitation_already_accepted(self, app, client, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id,
                status='accepted',
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
            db.session.add(invitation)
            db.session.commit()
            token = invitation.token
            
            response = client.get(f'/api/invitations/check/{token}')
            
            assert response.status_code == 410
            data = response.get_json()
            assert 'already accepted' in data['error']

    def test_check_invitation_expired(self, app, client, professor_user):
        with app.app_context():
            invitation = Invitation(
                email='test@test.com',
                role='tutor',
                invited_by=professor_user.id,
                status='pending',
                expires_at=datetime.utcnow() - timedelta(days=1)
            )
            db.session.add(invitation)
            db.session.commit()
            token = invitation.token
            
            response = client.get(f'/api/invitations/check/{token}')
            
            assert response.status_code == 410
            data = response.get_json()
            assert 'expired' in data['error']


class TestSendInvitationEmail:
    @patch('services.email_service.resend')
    def test_send_invitation_email_success(self, mock_resend, app):
        mock_resend.Emails.send.return_value = {'id': 'email_123'}
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            app.config['FRONTEND_URL'] = 'http://localhost:5173'
            
            from services.email_service import send_invitation_email
            
            result = send_invitation_email(
                'newtutor@test.com',
                'tutor',
                'test-token-123',
                'Professor Smith'
            )
            
            assert result is True
            mock_resend.Emails.send.assert_called_once()
            call_args = mock_resend.Emails.send.call_args[0][0]
            assert call_args['to'] == ['newtutor@test.com']
            assert 'test-token-123' in call_args['html']
            assert 'Professor Smith' in call_args['html']

    def test_send_invitation_email_no_api_key(self, app):
        with app.app_context():
            app.config['RESEND_API_KEY'] = None
            
            from services.email_service import send_invitation_email
            
            result = send_invitation_email(
                'newtutor@test.com',
                'tutor',
                'test-token-123',
                'Professor Smith'
            )
            
            assert result is False

    @patch('services.email_service.resend')
    def test_send_invitation_email_professor_role(self, mock_resend, app):
        mock_resend.Emails.send.return_value = {'id': 'email_123'}
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            
            from services.email_service import send_invitation_email
            
            result = send_invitation_email(
                'newprof@test.com',
                'professor',
                'test-token-123',
                'Admin User'
            )
            
            assert result is True
            call_args = mock_resend.Emails.send.call_args[0][0]
            assert 'Professor' in call_args['html']
            assert 'Professor' in call_args['subject']

    @patch('services.email_service.resend')
    def test_send_invitation_email_exception(self, mock_resend, app):
        mock_resend.Emails.send.side_effect = Exception('Email error')
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            
            from services.email_service import send_invitation_email
            
            result = send_invitation_email(
                'newtutor@test.com',
                'tutor',
                'test-token-123',
                'Professor Smith'
            )
            
            assert result is False
