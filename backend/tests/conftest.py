import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from models import db, User, Tutor, Availability, Session, SessionNote, Feedback
from config import Config
from auth import require_auth


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    CLERK_SECRET_KEY = 'test_clerk_secret'
    RESEND_API_KEY = 'test_resend_key'
    RESEND_FROM_EMAIL = 'test@example.com'
    FRONTEND_URL = 'http://localhost:5173'


def create_test_app():
    app = Flask(__name__)
    app.config.from_object(TestConfig)
    
    db.init_app(app)
    
    from routes.availability import availability_bp
    from routes.sessions import session_bp
    from routes.matching import matching_bp
    from routes.invitations import invitations_bp
    
    app.register_blueprint(availability_bp)
    app.register_blueprint(session_bp)
    app.register_blueprint(matching_bp)
    app.register_blueprint(invitations_bp)
    
    from zoneinfo import ZoneInfo
    NY_TZ = ZoneInfo("America/New_York")
    UTC = ZoneInfo("UTC")
    
    def to_client_iso(dt):
        return dt.astimezone(NY_TZ).isoformat() if dt else None
    
    def session_to_dict(s, include_people=True):
        data = s.to_dict()
        data["start_time"] = to_client_iso(s.start_time)
        data["end_time"] = to_client_iso(s.end_time)
        if include_people:
            data["tutor"] = {
                "id": s.tutor_id,
                "name": s.tutor_user.name if s.tutor_user else None,
                "email": s.tutor_user.email if s.tutor_user else None,
            }
            data["student"] = (
                {
                    "id": s.student_id,
                    "name": s.student_user.name if s.student_user else None,
                    "email": s.student_user.email if s.student_user else None,
                }
                if s.student_id
                else None
            )
        data["booked"] = s.status == "booked"
        return data
    
    @app.route("/api/health")
    def health():
        return {"status": "ok"}
    
    @app.route("/api/user")
    @require_auth
    def get_user():
        from flask import request
        db_user = request.db_user
        return jsonify({"user": db_user.to_dict(), "onboarding_complete": db_user.onboarding_complete})
    
    @app.route("/api/user/onboarding", methods=["POST"])
    @require_auth
    def complete_onboarding():
        from flask import request
        data = request.get_json()
        db_user = request.db_user
        
        language = data.get("language", "en")
        class_name = data.get("class_name")
        
        db_user.role = "student"
        db_user.class_name = class_name
        db_user.language_preference = language
        db_user.onboarding_complete = True
        db.session.commit()
        
        return jsonify({"success": True, "user": db_user.to_dict()})
    
    @app.route("/api/user/profile", methods=["POST"])
    @require_auth
    def update_profile():
        from flask import request
        data = request.get_json()
        db_user = request.db_user
        
        if "language_preference" in data:
            db_user.language_preference = data["language_preference"]
        if "class_name" in data:
            db_user.class_name = data["class_name"]
        
        db.session.commit()
        return jsonify({"success": True, "user": db_user.to_dict()})
    
    @app.route("/api/tutor/by-user/<int:user_id>")
    @require_auth
    def get_tutor_by_user(user_id):
        from flask import request
        db_user = request.db_user
        
        if db_user.id != user_id and db_user.role != "admin":
            return jsonify({"error": "Forbidden"}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        tutor = Tutor.query.filter_by(user_id=user_id).first()
        if not tutor:
            if user.role == "tutor":
                tutor = Tutor(user_id=user_id)
                db.session.add(tutor)
                db.session.commit()
            else:
                return jsonify({"error": "User is not a tutor"}), 400
        
        return jsonify({"tutor": tutor.to_dict()})
    
    @app.route("/api/tutors")
    @require_auth
    def get_tutors():
        tutors = Tutor.query.all()
        tutors_data = []
        
        for tutor in tutors:
            tutor_dict = tutor.to_dict()
            if tutor.user:
                tutor_dict["user"] = {
                    "id": tutor.user.id,
                    "name": tutor.user.name,
                    "email": tutor.user.email,
                    "class_name": tutor.user.class_name,
                }
            tutors_data.append(tutor_dict)
        
        return jsonify({"success": True, "tutors": tutors_data})
    
    return app


def mock_require_auth(user):
    def decorator(f):
        from functools import wraps
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import request
            request.db_user = user
            request.clerk_user = {'sub': user.clerk_user_id, 'name': user.name, 'email': user.email}
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@pytest.fixture
def app():
    test_app = create_test_app()
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db_session(app):
    with app.app_context():
        yield db.session


@pytest.fixture
def student_user(app):
    with app.app_context():
        user = User(
            clerk_user_id='clerk_test_student',
            name='Test Student',
            email='student@test.com',
            role='student',
            class_name='Chinese 101',
            language_preference='en',
            onboarding_complete=True
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def tutor_user(app):
    with app.app_context():
        user = User(
            clerk_user_id='clerk_test_tutor',
            name='Test Tutor',
            email='tutor@test.com',
            role='tutor',
            language_preference='en',
            onboarding_complete=True
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def tutor_profile(app, tutor_user):
    with app.app_context():
        tutor = Tutor(
            user_id=tutor_user.id,
            specialization='Chinese Grammar',
            availability_notes='Available weekdays'
        )
        db.session.add(tutor)
        db.session.commit()
        db.session.refresh(tutor)
        return tutor


@pytest.fixture
def professor_user(app):
    with app.app_context():
        user = User(
            clerk_user_id='clerk_test_professor',
            name='Test Professor',
            email='professor@test.com',
            role='professor',
            language_preference='en',
            onboarding_complete=True
        )
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def availability(app, tutor_profile):
    with app.app_context():
        av = Availability(
            tutor_id=tutor_profile.id,
            day_of_week=1,
            start_time=datetime(2025, 1, 6, 9, 0),
            end_time=datetime(2025, 1, 6, 17, 0),
            session_type='online',
            is_recurring=True
        )
        db.session.add(av)
        db.session.commit()
        db.session.refresh(av)
        return av


@pytest.fixture
def session_obj(app, tutor_user, student_user):
    with app.app_context():
        session = Session(
            tutor_id=tutor_user.id,
            student_id=student_user.id,
            course='Chinese 101',
            session_type='online',
            start_time=datetime(2025, 1, 6, 10, 0),
            end_time=datetime(2025, 1, 6, 11, 0),
            status='booked'
        )
        db.session.add(session)
        db.session.commit()
        db.session.refresh(session)
        return session


@pytest.fixture
def available_session(app, tutor_user):
    with app.app_context():
        session = Session(
            tutor_id=tutor_user.id,
            student_id=None,
            course='Chinese 101',
            session_type='online',
            start_time=datetime(2025, 1, 7, 10, 0),
            end_time=datetime(2025, 1, 7, 11, 0),
            status='available'
        )
        db.session.add(session)
        db.session.commit()
        db.session.refresh(session)
        return session


@pytest.fixture
def session_note(app, session_obj, tutor_user):
    with app.app_context():
        note = SessionNote(
            session_id=session_obj.id,
            tutor_id=tutor_user.id,
            attendance_status='present',
            notes='Great session',
            student_feedback='Student did well'
        )
        db.session.add(note)
        db.session.commit()
        db.session.refresh(note)
        return note


@pytest.fixture
def feedback(app, session_obj, student_user):
    with app.app_context():
        fb = Feedback(
            session_id=session_obj.id,
            student_id=student_user.id,
            rating=5.0,
            comment='Excellent tutor!'
        )
        db.session.add(fb)
        db.session.commit()
        db.session.refresh(fb)
        return fb


@pytest.fixture
def mock_resend():
    with patch('services.email_service.resend') as mock:
        mock.Emails.send.return_value = {'id': 'test_email_id'}
        yield mock


@pytest.fixture
def auth_headers():
    return {'Authorization': 'Bearer test_token'}


def setup_auth_mock(app, user):
    import auth
    original_require_auth = auth.require_auth
    
    def patched_require_auth(f):
        from functools import wraps
        @wraps(f)
        def decorated(*args, **kwargs):
            from flask import request
            request.db_user = user
            request.clerk_user = {'sub': user.clerk_user_id, 'name': user.name, 'email': user.email}
            return f(*args, **kwargs)
        return decorated
    
    return patch.object(auth, 'require_auth', patched_require_auth)


@pytest.fixture
def auth_client(app, student_user):
    with app.app_context():
        user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
        
        with patch('auth.Clerk') as mock_clerk:
            mock_sdk = MagicMock()
            mock_request_state = MagicMock()
            mock_request_state.is_signed_in = True
            mock_request_state.payload = {
                'sub': user.clerk_user_id,
                'name': user.name,
                'email': user.email
            }
            mock_sdk.authenticate_request.return_value = mock_request_state
            mock_clerk.return_value = mock_sdk
            
            with patch('auth.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'first_name': 'Test',
                    'last_name': 'Student',
                    'full_name': user.name,
                    'primary_email_address_id': 'email_123',
                    'email_addresses': [{'id': 'email_123', 'email_address': user.email}]
                }
                mock_get.return_value = mock_response
                
                yield app.test_client()


@pytest.fixture
def tutor_auth_client(app, tutor_user):
    with app.app_context():
        user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
        
        with patch('auth.Clerk') as mock_clerk:
            mock_sdk = MagicMock()
            mock_request_state = MagicMock()
            mock_request_state.is_signed_in = True
            mock_request_state.payload = {
                'sub': user.clerk_user_id,
                'name': user.name,
                'email': user.email
            }
            mock_sdk.authenticate_request.return_value = mock_request_state
            mock_clerk.return_value = mock_sdk
            
            with patch('auth.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'first_name': 'Test',
                    'last_name': 'Tutor',
                    'full_name': user.name,
                    'primary_email_address_id': 'email_123',
                    'email_addresses': [{'id': 'email_123', 'email_address': user.email}]
                }
                mock_get.return_value = mock_response
                
                yield app.test_client()


@pytest.fixture
def professor_auth_client(app, professor_user):
    with app.app_context():
        user = User.query.filter_by(clerk_user_id='clerk_test_professor').first()
        
        with patch('auth.Clerk') as mock_clerk:
            mock_sdk = MagicMock()
            mock_request_state = MagicMock()
            mock_request_state.is_signed_in = True
            mock_request_state.payload = {
                'sub': user.clerk_user_id,
                'name': user.name,
                'email': user.email
            }
            mock_sdk.authenticate_request.return_value = mock_request_state
            mock_clerk.return_value = mock_sdk
            
            with patch('auth.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'first_name': 'Test',
                    'last_name': 'Professor',
                    'full_name': user.name,
                    'primary_email_address_id': 'email_123',
                    'email_addresses': [{'id': 'email_123', 'email_address': user.email}]
                }
                mock_get.return_value = mock_response
                
                yield app.test_client()

