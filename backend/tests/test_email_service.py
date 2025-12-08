import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFormatSessionType:
    def test_format_session_type_in_person(self, app):
        with app.app_context():
            from services.email_service import format_session_type
            result = format_session_type('in-person')
            assert result == 'In-Person'

    def test_format_session_type_online(self, app):
        with app.app_context():
            from services.email_service import format_session_type
            result = format_session_type('online')
            assert result == 'Online'

    def test_format_session_type_other(self, app):
        with app.app_context():
            from services.email_service import format_session_type
            result = format_session_type('tutoring')
            assert result == 'Tutoring'

    def test_format_session_type_none(self, app):
        with app.app_context():
            from services.email_service import format_session_type
            result = format_session_type(None)
            assert result == 'Online'


class TestGenerateIcsEvent:
    def test_generate_ics_event_string_times(self, app):
        with app.app_context():
            from services.email_service import generate_ics_event
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': '2025-01-06T10:00:00+00:00',
                'end_time': '2025-01-06T11:00:00+00:00',
                'session_type': 'online'
            }
            result = generate_ics_event(session_data, 'Test Tutor', 'Test Student')
            assert result is not None
            assert b'VCALENDAR' in result

    def test_generate_ics_event_datetime_times(self, app):
        with app.app_context():
            from services.email_service import generate_ics_event
            session_data = {
                'id': 2,
                'course': 'Chinese 201',
                'start_time': datetime(2025, 1, 6, 10, 0),
                'end_time': datetime(2025, 1, 6, 11, 0),
                'session_type': 'in-person'
            }
            result = generate_ics_event(session_data, 'Test Tutor', 'Test Student')
            assert result is not None
            assert b'VCALENDAR' in result

    def test_generate_ics_event_with_z_suffix(self, app):
        with app.app_context():
            from services.email_service import generate_ics_event
            session_data = {
                'id': 3,
                'course': 'Chinese 301',
                'start_time': '2025-01-06T10:00:00Z',
                'end_time': '2025-01-06T11:00:00Z',
                'session_type': 'online'
            }
            result = generate_ics_event(session_data, 'Test Tutor', 'Test Student')
            assert result is not None


class TestSendBookingConfirmation:
    def test_send_booking_confirmation_no_api_key(self, app):
        with app.app_context():
            app.config['RESEND_API_KEY'] = None
            from services.email_service import send_booking_confirmation
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': '2025-01-06T10:00:00+00:00',
                'end_time': '2025-01-06T11:00:00+00:00',
                'session_type': 'online'
            }
            result = send_booking_confirmation(
                'student@test.com',
                'Test Student',
                'Test Tutor',
                session_data
            )
            assert result is False

    @patch('services.email_service.resend')
    def test_send_booking_confirmation_success(self, mock_resend, app):
        mock_resend.Emails.send.return_value = {'id': 'email_123'}
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            from services.email_service import send_booking_confirmation
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': '2025-01-06T10:00:00+00:00',
                'end_time': '2025-01-06T11:00:00+00:00',
                'session_type': 'online'
            }
            result = send_booking_confirmation(
                'student@test.com',
                'Test Student',
                'Test Tutor',
                session_data
            )
            assert result is True

    @patch('services.email_service.resend')
    def test_send_booking_confirmation_with_datetime(self, mock_resend, app):
        mock_resend.Emails.send.return_value = {'id': 'email_123'}
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            from services.email_service import send_booking_confirmation
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': datetime(2025, 1, 6, 10, 0),
                'end_time': datetime(2025, 1, 6, 11, 0),
                'session_type': 'in-person'
            }
            result = send_booking_confirmation(
                'student@test.com',
                'Test Student',
                'Test Tutor',
                session_data
            )
            assert result is True

    @patch('services.email_service.resend')
    def test_send_booking_confirmation_exception(self, mock_resend, app):
        mock_resend.Emails.send.side_effect = Exception('Email error')
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            from services.email_service import send_booking_confirmation
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': '2025-01-06T10:00:00+00:00',
                'end_time': '2025-01-06T11:00:00+00:00',
                'session_type': 'online'
            }
            result = send_booking_confirmation(
                'student@test.com',
                'Test Student',
                'Test Tutor',
                session_data
            )
            assert result is False


class TestSendTutorNotification:
    def test_send_tutor_notification_no_api_key(self, app):
        with app.app_context():
            app.config['RESEND_API_KEY'] = None
            from services.email_service import send_tutor_notification
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': '2025-01-06T10:00:00+00:00',
                'end_time': '2025-01-06T11:00:00+00:00',
                'session_type': 'online'
            }
            result = send_tutor_notification(
                'tutor@test.com',
                'Test Tutor',
                'Test Student',
                session_data
            )
            assert result is False

    @patch('services.email_service.resend')
    def test_send_tutor_notification_success(self, mock_resend, app):
        mock_resend.Emails.send.return_value = {'id': 'email_123'}
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            from services.email_service import send_tutor_notification
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': '2025-01-06T10:00:00+00:00',
                'end_time': '2025-01-06T11:00:00+00:00',
                'session_type': 'online'
            }
            result = send_tutor_notification(
                'tutor@test.com',
                'Test Tutor',
                'Test Student',
                session_data
            )
            assert result is True

    @patch('services.email_service.resend')
    def test_send_tutor_notification_with_datetime(self, mock_resend, app):
        mock_resend.Emails.send.return_value = {'id': 'email_123'}
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            from services.email_service import send_tutor_notification
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': datetime(2025, 1, 6, 10, 0),
                'end_time': datetime(2025, 1, 6, 11, 0),
                'session_type': 'in-person'
            }
            result = send_tutor_notification(
                'tutor@test.com',
                'Test Tutor',
                'Test Student',
                session_data
            )
            assert result is True

    @patch('services.email_service.resend')
    def test_send_tutor_notification_exception(self, mock_resend, app):
        mock_resend.Emails.send.side_effect = Exception('Email error')
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            from services.email_service import send_tutor_notification
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': '2025-01-06T10:00:00+00:00',
                'end_time': '2025-01-06T11:00:00+00:00',
                'session_type': 'online'
            }
            result = send_tutor_notification(
                'tutor@test.com',
                'Test Tutor',
                'Test Student',
                session_data
            )
            assert result is False


class TestSendFeedbackRequest:
    def test_send_feedback_request_no_api_key(self, app):
        with app.app_context():
            app.config['RESEND_API_KEY'] = None
            from services.email_service import send_feedback_request
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': '2025-01-06T10:00:00+00:00',
                'end_time': '2025-01-06T11:00:00+00:00',
                'session_type': 'online'
            }
            result = send_feedback_request(
                'student@test.com',
                'Test Student',
                'Test Tutor',
                session_data
            )
            assert result is False

    @patch('services.email_service.resend')
    def test_send_feedback_request_success(self, mock_resend, app):
        mock_resend.Emails.send.return_value = {'id': 'email_123'}
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            app.config['FRONTEND_URL'] = 'http://localhost:5173'
            from services.email_service import send_feedback_request
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': '2025-01-06T10:00:00+00:00',
                'end_time': '2025-01-06T11:00:00+00:00',
                'session_type': 'online'
            }
            result = send_feedback_request(
                'student@test.com',
                'Test Student',
                'Test Tutor',
                session_data
            )
            assert result is True

    @patch('services.email_service.resend')
    def test_send_feedback_request_with_datetime(self, mock_resend, app):
        mock_resend.Emails.send.return_value = {'id': 'email_123'}
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            app.config['FRONTEND_URL'] = 'http://localhost:5173'
            from services.email_service import send_feedback_request
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': datetime(2025, 1, 6, 10, 0),
                'end_time': datetime(2025, 1, 6, 11, 0),
                'session_type': 'in-person'
            }
            result = send_feedback_request(
                'student@test.com',
                'Test Student',
                'Test Tutor',
                session_data
            )
            assert result is True

    @patch('services.email_service.resend')
    def test_send_feedback_request_exception(self, mock_resend, app):
        mock_resend.Emails.send.side_effect = Exception('Email error')
        
        with app.app_context():
            app.config['RESEND_API_KEY'] = 'test_key'
            app.config['RESEND_FROM_EMAIL'] = 'from@test.com'
            from services.email_service import send_feedback_request
            session_data = {
                'id': 1,
                'course': 'Chinese 101',
                'start_time': '2025-01-06T10:00:00+00:00',
                'end_time': '2025-01-06T11:00:00+00:00',
                'session_type': 'online'
            }
            result = send_feedback_request(
                'student@test.com',
                'Test Student',
                'Test Tutor',
                session_data
            )
            assert result is False

