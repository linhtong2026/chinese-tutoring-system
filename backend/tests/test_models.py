import pytest
from datetime import datetime
from models import db, User, Tutor, Availability, Session, SessionNote, Feedback


class TestUserModel:
    def test_create_user(self, app):
        with app.app_context():
            user = User(
                clerk_user_id='test_clerk_123',
                name='John Doe',
                email='john@example.com',
                role='student',
                class_name='Chinese 101',
                language_preference='en',
                onboarding_complete=False
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.clerk_user_id == 'test_clerk_123'
            assert user.name == 'John Doe'
            assert user.email == 'john@example.com'
            assert user.role == 'student'
            assert user.class_name == 'Chinese 101'
            assert user.language_preference == 'en'
            assert user.onboarding_complete is False
            assert user.created_at is not None

    def test_user_to_dict(self, app):
        with app.app_context():
            user = User(
                clerk_user_id='test_clerk_456',
                name='Jane Doe',
                email='jane@example.com',
                role='tutor',
                language_preference='zh',
                onboarding_complete=True
            )
            db.session.add(user)
            db.session.commit()
            
            user_dict = user.to_dict()
            
            assert user_dict['id'] == user.id
            assert user_dict['clerk_user_id'] == 'test_clerk_456'
            assert user_dict['name'] == 'Jane Doe'
            assert user_dict['email'] == 'jane@example.com'
            assert user_dict['role'] == 'tutor'
            assert user_dict['language_preference'] == 'zh'
            assert user_dict['onboarding_complete'] is True
            assert 'created_at' in user_dict

    def test_get_or_create_from_clerk_new_user(self, app):
        with app.app_context():
            user = User.get_or_create_from_clerk(
                clerk_user_id='new_clerk_id',
                name='New User',
                email='new@example.com'
            )
            
            assert user.id is not None
            assert user.clerk_user_id == 'new_clerk_id'
            assert user.name == 'New User'
            assert user.email == 'new@example.com'

    def test_get_or_create_from_clerk_existing_user(self, app):
        with app.app_context():
            user1 = User(
                clerk_user_id='existing_clerk_id',
                name='Existing User',
                email='existing@example.com'
            )
            db.session.add(user1)
            db.session.commit()
            
            user2 = User.get_or_create_from_clerk(
                clerk_user_id='existing_clerk_id',
                name='Updated Name',
                email='updated@example.com'
            )
            
            assert user1.id == user2.id
            assert user2.name == 'Updated Name'
            assert user2.email == 'updated@example.com'

    def test_get_or_create_from_clerk_no_update_if_empty(self, app):
        with app.app_context():
            user1 = User(
                clerk_user_id='clerk_no_update',
                name='Original Name',
                email='original@example.com'
            )
            db.session.add(user1)
            db.session.commit()
            
            user2 = User.get_or_create_from_clerk(
                clerk_user_id='clerk_no_update',
                name='',
                email=''
            )
            
            assert user2.name == 'Original Name'
            assert user2.email == 'original@example.com'

    def test_user_to_dict_with_none_created_at(self, app):
        with app.app_context():
            user = User(
                clerk_user_id='test_none_date',
                name='Test',
                email='test@example.com'
            )
            user.created_at = None
            
            user_dict = user.to_dict()
            assert user_dict['created_at'] is None


class TestTutorModel:
    def test_create_tutor(self, app, tutor_user):
        with app.app_context():
            tutor = Tutor(
                user_id=tutor_user.id,
                specialization='Chinese Literature',
                availability_notes='Available Mon-Fri'
            )
            db.session.add(tutor)
            db.session.commit()
            
            assert tutor.id is not None
            assert tutor.user_id == tutor_user.id
            assert tutor.specialization == 'Chinese Literature'
            assert tutor.availability_notes == 'Available Mon-Fri'

    def test_tutor_to_dict(self, app, tutor_user):
        with app.app_context():
            tutor = Tutor(
                user_id=tutor_user.id,
                specialization='Grammar',
                availability_notes='Weekends only'
            )
            db.session.add(tutor)
            db.session.commit()
            
            tutor_dict = tutor.to_dict()
            
            assert tutor_dict['id'] == tutor.id
            assert tutor_dict['user_id'] == tutor_user.id
            assert tutor_dict['specialization'] == 'Grammar'
            assert tutor_dict['availability_notes'] == 'Weekends only'
            assert 'created_at' in tutor_dict

    def test_tutor_to_dict_with_none_created_at(self, app, tutor_user):
        with app.app_context():
            tutor = Tutor(user_id=tutor_user.id)
            tutor.created_at = None
            
            tutor_dict = tutor.to_dict()
            assert tutor_dict['created_at'] is None

    def test_tutor_user_relationship(self, app, tutor_user):
        with app.app_context():
            tutor = Tutor(user_id=tutor_user.id)
            db.session.add(tutor)
            db.session.commit()
            
            retrieved_tutor = Tutor.query.filter_by(user_id=tutor_user.id).first()
            assert retrieved_tutor.user.name == tutor_user.name


class TestAvailabilityModel:
    def test_create_availability(self, app, tutor_profile):
        with app.app_context():
            av = Availability(
                tutor_id=tutor_profile.id,
                day_of_week=0,
                start_time=datetime(2025, 1, 6, 9, 0),
                end_time=datetime(2025, 1, 6, 12, 0),
                session_type='online',
                is_recurring=True
            )
            db.session.add(av)
            db.session.commit()
            
            assert av.id is not None
            assert av.tutor_id == tutor_profile.id
            assert av.day_of_week == 0
            assert av.session_type == 'online'
            assert av.is_recurring is True

    def test_availability_to_dict(self, app, tutor_profile):
        with app.app_context():
            av = Availability(
                tutor_id=tutor_profile.id,
                day_of_week=2,
                start_time=datetime(2025, 1, 8, 14, 0),
                end_time=datetime(2025, 1, 8, 16, 0),
                session_type='in-person',
                is_recurring=False
            )
            db.session.add(av)
            db.session.commit()
            
            av_dict = av.to_dict()
            
            assert av_dict['id'] == av.id
            assert av_dict['tutor_id'] == tutor_profile.id
            assert av_dict['day_of_week'] == 2
            assert av_dict['session_type'] == 'in-person'
            assert av_dict['is_recurring'] is False
            assert 'start_time' in av_dict
            assert 'end_time' in av_dict

    def test_availability_to_dict_with_none_times(self, app, tutor_profile):
        with app.app_context():
            av = Availability(
                tutor_id=tutor_profile.id,
                day_of_week=0,
                start_time=datetime(2025, 1, 6, 9, 0),
                end_time=datetime(2025, 1, 6, 12, 0),
                session_type='online'
            )
            av.start_time = None
            av.end_time = None
            av.created_at = None
            
            av_dict = av.to_dict()
            assert av_dict['start_time'] is None
            assert av_dict['end_time'] is None
            assert av_dict['created_at'] is None


class TestSessionModel:
    def test_create_session(self, app, tutor_user, student_user):
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 201',
                session_type='online',
                start_time=datetime(2025, 1, 7, 10, 0),
                end_time=datetime(2025, 1, 7, 11, 0),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            assert session.id is not None
            assert session.tutor_id == tutor_user.id
            assert session.student_id == student_user.id
            assert session.course == 'Chinese 201'
            assert session.status == 'booked'

    def test_session_to_dict(self, app, tutor_user, student_user):
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 301',
                session_type='in-person',
                start_time=datetime(2025, 1, 8, 14, 0),
                end_time=datetime(2025, 1, 8, 15, 0),
                status='available'
            )
            db.session.add(session)
            db.session.commit()
            
            session_dict = session.to_dict()
            
            assert session_dict['id'] == session.id
            assert session_dict['tutor_id'] == tutor_user.id
            assert session_dict['student_id'] == student_user.id
            assert session_dict['course'] == 'Chinese 301'
            assert session_dict['session_type'] == 'in-person'
            assert session_dict['status'] == 'available'
            assert 'start_time' in session_dict
            assert 'end_time' in session_dict

    def test_session_to_dict_with_none_times(self, app, tutor_user):
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 7, 10, 0),
                end_time=datetime(2025, 1, 7, 11, 0)
            )
            session.start_time = None
            session.end_time = None
            session.created_at = None
            session.updated_at = None
            
            session_dict = session.to_dict()
            assert session_dict['start_time'] is None
            assert session_dict['end_time'] is None
            assert session_dict['created_at'] is None
            assert session_dict['updated_at'] is None

    def test_session_without_student(self, app, tutor_user):
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
            
            session_dict = session.to_dict()
            assert session_dict['student_id'] is None
            assert session_dict['student_name'] is None


class TestSessionNoteModel:
    def test_create_session_note(self, app, session_obj, tutor_user):
        with app.app_context():
            note = SessionNote(
                session_id=session_obj.id,
                tutor_id=tutor_user.id,
                attendance_status='present',
                notes='Student did well',
                student_feedback='Keep up the good work'
            )
            db.session.add(note)
            db.session.commit()
            
            assert note.id is not None
            assert note.session_id == session_obj.id
            assert note.tutor_id == tutor_user.id
            assert note.attendance_status == 'present'
            assert note.notes == 'Student did well'

    def test_session_note_to_dict(self, app, session_obj, tutor_user):
        with app.app_context():
            note = SessionNote(
                session_id=session_obj.id,
                tutor_id=tutor_user.id,
                attendance_status='absent',
                notes='Student was absent',
                student_feedback='N/A'
            )
            db.session.add(note)
            db.session.commit()
            
            note_dict = note.to_dict()
            
            assert note_dict['id'] == note.id
            assert note_dict['session_id'] == session_obj.id
            assert note_dict['tutor_id'] == tutor_user.id
            assert note_dict['attendance_status'] == 'absent'
            assert note_dict['notes'] == 'Student was absent'
            assert note_dict['student_feedback'] == 'N/A'

    def test_session_note_to_dict_with_none_times(self, app, session_obj, tutor_user):
        with app.app_context():
            note = SessionNote(
                session_id=session_obj.id,
                tutor_id=tutor_user.id,
                attendance_status='present'
            )
            note.created_at = None
            note.updated_at = None
            
            note_dict = note.to_dict()
            assert note_dict['created_at'] is None
            assert note_dict['updated_at'] is None


class TestFeedbackModel:
    def test_create_feedback(self, app, session_obj, student_user):
        with app.app_context():
            feedback = Feedback(
                session_id=session_obj.id,
                student_id=student_user.id,
                rating=4.5,
                comment='Great session!'
            )
            db.session.add(feedback)
            db.session.commit()
            
            assert feedback.id is not None
            assert feedback.session_id == session_obj.id
            assert feedback.student_id == student_user.id
            assert feedback.rating == 4.5
            assert feedback.comment == 'Great session!'

    def test_feedback_to_dict(self, app, session_obj, student_user):
        with app.app_context():
            feedback = Feedback(
                session_id=session_obj.id,
                student_id=student_user.id,
                rating=3.0,
                comment='Average session'
            )
            db.session.add(feedback)
            db.session.commit()
            
            feedback_dict = feedback.to_dict()
            
            assert feedback_dict['id'] == feedback.id
            assert feedback_dict['session_id'] == session_obj.id
            assert feedback_dict['student_id'] == student_user.id
            assert feedback_dict['rating'] == 3.0
            assert feedback_dict['comment'] == 'Average session'

    def test_feedback_to_dict_with_none_times(self, app, session_obj, student_user):
        with app.app_context():
            feedback = Feedback(
                session_id=session_obj.id,
                student_id=student_user.id,
                rating=5.0
            )
            feedback.created_at = None
            feedback.updated_at = None
            
            feedback_dict = feedback.to_dict()
            assert feedback_dict['created_at'] is None
            assert feedback_dict['updated_at'] is None

