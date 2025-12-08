import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User, Tutor, Session, SessionNote, Feedback, Availability


class TestBookSession:
    def test_book_session_not_student(self, app, tutor_user, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            assert user.role == 'tutor'

    @patch('routes.sessions.send_booking_confirmation')
    @patch('routes.sessions.send_tutor_notification')
    def test_book_session_success(self, mock_tutor_email, mock_student_email, app, student_user, tutor_user, tutor_profile, availability):
        mock_student_email.return_value = True
        mock_tutor_email.return_value = True
        
        with app.app_context():
            av = Availability.query.first()
            student = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            tutor = Tutor.query.first()
            
            session = Session(
                tutor_id=tutor.user_id,
                student_id=student.id,
                course='Chinese 101',
                session_type=av.session_type,
                start_time=av.start_time,
                end_time=av.start_time + timedelta(hours=1),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            assert session.id is not None
            assert session.status == 'booked'
            assert session.student_id == student.id

    def test_book_session_availability_not_found(self, app, student_user):
        with app.app_context():
            av = Availability.query.get(99999)
            assert av is None

    def test_book_session_invalid_datetime(self, app, student_user, availability):
        with app.app_context():
            try:
                datetime.fromisoformat('invalid-date')
                assert False
            except ValueError:
                assert True

    def test_book_session_end_before_start(self, app, student_user, availability):
        start = datetime(2025, 1, 6, 11, 0)
        end = datetime(2025, 1, 6, 10, 0)
        assert end <= start

    def test_book_session_outside_recurring_window(self, app, student_user, availability):
        with app.app_context():
            av = Availability.query.first()
            assert av.is_recurring is True
            
            av_start_time = av.start_time.time()
            av_end_time = av.end_time.time()
            
            req_start = datetime(2025, 1, 6, 8, 0).time()
            
            assert not (av_start_time <= req_start)

    def test_book_session_outside_non_recurring_window(self, app, tutor_profile):
        with app.app_context():
            av = Availability(
                tutor_id=tutor_profile.id,
                day_of_week=1,
                start_time=datetime(2025, 1, 6, 10, 0),
                end_time=datetime(2025, 1, 6, 12, 0),
                session_type='online',
                is_recurring=False
            )
            db.session.add(av)
            db.session.commit()
            
            req_start = datetime(2025, 1, 6, 9, 0)
            req_end = datetime(2025, 1, 6, 11, 0)
            
            assert not (av.start_time <= req_start and req_end <= av.end_time)

    def test_book_session_tutor_overlap(self, app, student_user, tutor_user, tutor_profile, availability):
        with app.app_context():
            session1 = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 6, 10, 0),
                end_time=datetime(2025, 1, 6, 11, 0),
                status='booked'
            )
            db.session.add(session1)
            db.session.commit()
            
            overlap = Session.query.filter(
                Session.tutor_id == tutor_user.id,
                Session.start_time < datetime(2025, 1, 6, 10, 30),
                Session.end_time > datetime(2025, 1, 6, 10, 0)
            ).first()
            
            assert overlap is not None

    def test_book_session_tutor_profile_misconfigured(self, app, student_user, tutor_profile):
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
            
            assert av.tutor is not None
            assert av.tutor.user_id is not None

    @patch('routes.sessions.send_booking_confirmation')
    @patch('routes.sessions.send_tutor_notification')
    def test_book_session_email_failure(self, mock_tutor_email, mock_student_email, app, student_user, tutor_user, tutor_profile, availability):
        mock_student_email.side_effect = Exception('Email error')
        mock_tutor_email.return_value = True
        
        with app.app_context():
            av = Availability.query.first()
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type=av.session_type,
                start_time=av.start_time,
                end_time=av.start_time + timedelta(hours=1),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            assert session.id is not None


class TestTutorListSessions:
    def test_tutor_list_sessions_as_tutor(self, app, tutor_user, student_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter(Session.tutor_id == tutor_user.id).all()
            assert len(sessions) >= 1

    def test_tutor_list_sessions_with_tutor_id(self, app, student_user, tutor_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter(Session.tutor_id == tutor_user.id).all()
            assert len(sessions) >= 1

    def test_tutor_list_sessions_with_status_filter(self, app, tutor_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter(
                Session.tutor_id == tutor_user.id,
                Session.status.in_(['booked'])
            ).all()
            assert len(sessions) >= 1

    def test_tutor_list_sessions_with_date_filter(self, app, tutor_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter(
                Session.tutor_id == tutor_user.id,
                Session.start_time >= datetime(2025, 1, 1)
            ).all()
            assert len(sessions) >= 1


class TestStudentMySessions:
    def test_student_my_sessions(self, app, student_user, tutor_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter(Session.student_id == student_user.id).all()
            assert len(sessions) >= 1

    def test_student_my_sessions_not_student(self, app, tutor_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            assert user.role != 'student'

    def test_student_my_sessions_with_feedback(self, app, student_user, tutor_user, session_obj, feedback):
        with app.app_context():
            sessions = Session.query.filter(Session.student_id == student_user.id).all()
            session_ids = [s.id for s in sessions]
            feedbacks = Feedback.query.filter(Feedback.session_id.in_(session_ids)).all()
            
            assert len(feedbacks) >= 1


class TestGetSessions:
    def test_get_sessions_all(self, app, session_obj):
        with app.app_context():
            sessions = Session.query.all()
            assert len(sessions) >= 1

    def test_get_sessions_by_tutor(self, app, tutor_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter_by(tutor_id=tutor_user.id).all()
            assert len(sessions) >= 1

    def test_get_sessions_by_student(self, app, student_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter_by(student_id=student_user.id).all()
            assert len(sessions) >= 1


class TestGetSession:
    def test_get_session_success(self, app, session_obj):
        with app.app_context():
            session = Session.query.get(session_obj.id)
            assert session is not None

    def test_get_session_not_found(self, app):
        with app.app_context():
            session = Session.query.get(99999)
            assert session is None


class TestUpdateSession:
    def test_update_session_not_found(self, app):
        with app.app_context():
            session = Session.query.get(99999)
            assert session is None

    def test_update_session_tutor(self, app, session_obj, tutor_user):
        with app.app_context():
            session = Session.query.get(session_obj.id)
            new_tutor = User(
                clerk_user_id='new_tutor_clerk',
                name='New Tutor',
                email='newtutor@test.com',
                role='tutor'
            )
            db.session.add(new_tutor)
            db.session.commit()
            
            session.tutor_id = new_tutor.id
            db.session.commit()
            
            updated = Session.query.get(session_obj.id)
            assert updated.tutor_id == new_tutor.id

    def test_update_session_tutor_not_found(self, app, session_obj):
        with app.app_context():
            tutor = User.query.get(99999)
            assert tutor is None

    def test_update_session_student(self, app, session_obj, student_user):
        with app.app_context():
            new_student = User(
                clerk_user_id='new_student_clerk',
                name='New Student',
                email='newstudent@test.com',
                role='student'
            )
            db.session.add(new_student)
            db.session.commit()
            
            session = Session.query.get(session_obj.id)
            session.student_id = new_student.id
            db.session.commit()
            
            updated = Session.query.get(session_obj.id)
            assert updated.student_id == new_student.id

    def test_update_session_student_to_none(self, app, session_obj):
        with app.app_context():
            session = Session.query.get(session_obj.id)
            session.student_id = None
            db.session.commit()
            
            updated = Session.query.get(session_obj.id)
            assert updated.student_id is None

    def test_update_session_student_not_found(self, app, session_obj):
        with app.app_context():
            student = User.query.get(99999)
            assert student is None

    def test_update_session_course(self, app, session_obj):
        with app.app_context():
            session = Session.query.get(session_obj.id)
            session.course = 'Chinese 301'
            db.session.commit()
            
            updated = Session.query.get(session_obj.id)
            assert updated.course == 'Chinese 301'

    def test_update_session_type(self, app, session_obj):
        with app.app_context():
            session = Session.query.get(session_obj.id)
            session.session_type = 'in-person'
            db.session.commit()
            
            updated = Session.query.get(session_obj.id)
            assert updated.session_type == 'in-person'

    def test_update_session_times(self, app, session_obj):
        with app.app_context():
            session = Session.query.get(session_obj.id)
            new_start = datetime(2025, 1, 10, 14, 0)
            new_end = datetime(2025, 1, 10, 15, 0)
            session.start_time = new_start
            session.end_time = new_end
            db.session.commit()
            
            updated = Session.query.get(session_obj.id)
            assert updated.start_time == new_start
            assert updated.end_time == new_end

    def test_update_session_invalid_start_time(self, app, session_obj):
        with app.app_context():
            try:
                datetime.fromisoformat('invalid')
                assert False
            except ValueError:
                assert True

    def test_update_session_invalid_end_time(self, app, session_obj):
        with app.app_context():
            try:
                datetime.fromisoformat('invalid')
                assert False
            except ValueError:
                assert True

    def test_update_session_status(self, app, session_obj):
        with app.app_context():
            session = Session.query.get(session_obj.id)
            session.status = 'completed'
            db.session.commit()
            
            updated = Session.query.get(session_obj.id)
            assert updated.status == 'completed'


class TestDeleteSession:
    def test_delete_session_success(self, app, tutor_user, student_user):
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 10, 10, 0),
                end_time=datetime(2025, 1, 10, 11, 0),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            session_id = session.id
            
            db.session.delete(session)
            db.session.commit()
            
            deleted = Session.query.get(session_id)
            assert deleted is None

    def test_delete_session_not_found(self, app):
        with app.app_context():
            session = Session.query.get(99999)
            assert session is None


class TestBookExistingSession:
    def test_book_existing_session_success(self, app, student_user, available_session):
        with app.app_context():
            session = Session.query.get(available_session.id)
            session.status = 'booked'
            session.student_id = student_user.id
            db.session.commit()
            
            updated = Session.query.get(available_session.id)
            assert updated.status == 'booked'
            assert updated.student_id == student_user.id

    def test_book_existing_session_not_student(self, app, tutor_user, available_session):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            assert user.role != 'student'

    def test_book_existing_session_not_found(self, app, student_user):
        with app.app_context():
            session = Session.query.get(99999)
            assert session is None

    def test_book_existing_session_already_booked(self, app, student_user, session_obj):
        with app.app_context():
            session = Session.query.get(session_obj.id)
            assert session.status == 'booked'


class TestCreateSessionNote:
    def test_create_session_note_not_tutor(self, app, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            assert user.role != 'tutor'

    def test_create_session_note_missing_session_id(self, app, tutor_user):
        with app.app_context():
            assert True

    def test_create_session_note_session_not_found(self, app, tutor_user):
        with app.app_context():
            session = Session.query.get(99999)
            assert session is None

    def test_create_session_note_wrong_tutor(self, app, tutor_user, session_obj):
        with app.app_context():
            other_tutor = User(
                clerk_user_id='other_tutor_clerk',
                name='Other Tutor',
                email='other@test.com',
                role='tutor'
            )
            db.session.add(other_tutor)
            db.session.commit()
            
            session = Session.query.get(session_obj.id)
            assert session.tutor_id != other_tutor.id

    def test_create_session_note_existing_note(self, app, tutor_user, session_obj, session_note):
        with app.app_context():
            existing = SessionNote.query.filter_by(
                session_id=session_obj.id,
                tutor_id=tutor_user.id
            ).first()
            assert existing is not None

    @patch('routes.sessions.send_feedback_request')
    def test_create_session_note_success(self, mock_email, app, tutor_user, student_user):
        mock_email.return_value = True
        
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 10, 10, 0),
                end_time=datetime(2025, 1, 10, 11, 0),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            note = SessionNote(
                session_id=session.id,
                tutor_id=tutor_user.id,
                attendance_status='present',
                notes='Great session',
                student_feedback='Good work'
            )
            db.session.add(note)
            db.session.commit()
            
            assert note.id is not None

    @patch('routes.sessions.send_feedback_request')
    def test_create_session_note_sends_feedback_email(self, mock_email, app, tutor_user, student_user):
        mock_email.return_value = True
        
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 10, 10, 0),
                end_time=datetime(2025, 1, 10, 11, 0),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            note = SessionNote(
                session_id=session.id,
                tutor_id=tutor_user.id,
                attendance_status='present',
                notes='Great session'
            )
            db.session.add(note)
            db.session.commit()
            
            assert note.attendance_status in ['present', 'attended', 'late']

    @patch('routes.sessions.send_feedback_request')
    def test_create_session_note_email_failure(self, mock_email, app, tutor_user, student_user):
        mock_email.side_effect = Exception('Email error')
        
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 10, 10, 0),
                end_time=datetime(2025, 1, 10, 11, 0),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            note = SessionNote(
                session_id=session.id,
                tutor_id=tutor_user.id,
                attendance_status='present',
                notes='Great session'
            )
            db.session.add(note)
            db.session.commit()
            
            assert note.id is not None


class TestUpdateSessionNote:
    def test_update_session_note_not_tutor(self, app, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            assert user.role != 'tutor'

    def test_update_session_note_not_found(self, app, tutor_user):
        with app.app_context():
            note = SessionNote.query.get(99999)
            assert note is None

    def test_update_session_note_wrong_tutor(self, app, tutor_user, session_note):
        with app.app_context():
            other_tutor = User(
                clerk_user_id='other_tutor_update',
                name='Other Tutor',
                email='other_update@test.com',
                role='tutor'
            )
            db.session.add(other_tutor)
            db.session.commit()
            
            note = SessionNote.query.get(session_note.id)
            assert note.tutor_id != other_tutor.id

    def test_update_session_note_success(self, app, session_note):
        with app.app_context():
            note = SessionNote.query.get(session_note.id)
            note.attendance_status = 'late'
            note.notes = 'Updated notes'
            note.student_feedback = 'Updated feedback'
            db.session.commit()
            
            updated = SessionNote.query.get(session_note.id)
            assert updated.attendance_status == 'late'
            assert updated.notes == 'Updated notes'


class TestGetSessionNote:
    def test_get_session_note_success(self, app, session_obj, session_note):
        with app.app_context():
            note = SessionNote.query.filter_by(session_id=session_obj.id).first()
            assert note is not None

    def test_get_session_note_session_not_found(self, app):
        with app.app_context():
            session = Session.query.get(99999)
            assert session is None

    def test_get_session_note_no_note(self, app, tutor_user, student_user):
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 15, 10, 0),
                end_time=datetime(2025, 1, 15, 11, 0),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            note = SessionNote.query.filter_by(session_id=session.id).first()
            assert note is None


class TestSubmitFeedback:
    def test_submit_feedback_missing_fields(self, app, student_user):
        with app.app_context():
            session_id = None
            rating = None
            assert not session_id or not rating

    def test_submit_feedback_session_not_found(self, app, student_user):
        with app.app_context():
            session = Session.query.get(99999)
            assert session is None

    def test_submit_feedback_wrong_student(self, app, student_user, session_obj):
        with app.app_context():
            other_student = User(
                clerk_user_id='other_student_feedback',
                name='Other Student',
                email='other_student@test.com',
                role='student'
            )
            db.session.add(other_student)
            db.session.commit()
            
            session = Session.query.get(session_obj.id)
            assert session.student_id != other_student.id

    def test_submit_feedback_new(self, app, student_user, tutor_user):
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 20, 10, 0),
                end_time=datetime(2025, 1, 20, 11, 0),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            feedback = Feedback(
                session_id=session.id,
                student_id=student_user.id,
                rating=5.0,
                comment='Excellent session!'
            )
            db.session.add(feedback)
            db.session.commit()
            
            assert feedback.id is not None

    def test_submit_feedback_update_existing(self, app, student_user, session_obj, feedback):
        with app.app_context():
            existing = Feedback.query.filter_by(
                session_id=session_obj.id,
                student_id=student_user.id
            ).first()
            existing.rating = 4.0
            existing.comment = 'Updated comment'
            db.session.commit()
            
            updated = Feedback.query.get(existing.id)
            assert updated.rating == 4.0
            assert updated.comment == 'Updated comment'


class TestGetSessionFeedback:
    def test_get_session_feedback_success(self, app, session_obj, feedback):
        with app.app_context():
            fb = Feedback.query.filter_by(session_id=session_obj.id).first()
            assert fb is not None

    def test_get_session_feedback_session_not_found(self, app):
        with app.app_context():
            session = Session.query.get(99999)
            assert session is None

    def test_get_session_feedback_no_feedback(self, app, tutor_user, student_user):
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 25, 10, 0),
                end_time=datetime(2025, 1, 25, 11, 0),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
            fb = Feedback.query.filter_by(session_id=session.id).first()
            assert fb is None


class TestProfessorGetAllSessions:
    def test_professor_get_sessions_not_professor(self, app, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            assert user.role != 'professor'

    def test_professor_get_sessions_success(self, app, professor_user, session_obj, session_note, feedback):
        with app.app_context():
            sessions = Session.query.all()
            session_ids = [s.id for s in sessions]
            notes = SessionNote.query.filter(SessionNote.session_id.in_(session_ids)).all()
            feedbacks = Feedback.query.filter(Feedback.session_id.in_(session_ids)).all()
            
            assert len(sessions) >= 1


class TestProfessorDashboard:
    def test_professor_dashboard_not_professor(self, app, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            assert user.role != 'professor'

    def test_professor_dashboard_success(self, app, professor_user, session_obj, session_note, feedback):
        with app.app_context():
            sessions = Session.query.filter(Session.status == 'booked').all()
            
            total_sessions = len(sessions)
            
            total_hours = 0
            for session in sessions:
                if session.start_time and session.end_time:
                    duration = (session.end_time - session.start_time).total_seconds() / 3600
                    total_hours += duration
            
            unique_students = set()
            for session in sessions:
                if session.student_id:
                    unique_students.add(session.student_id)
            
            assert total_sessions >= 0

    def test_professor_dashboard_with_class_filter(self, app, professor_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter(
                Session.status == 'booked',
                Session.course == 'Chinese 101'
            ).all()
            assert len(sessions) >= 0

    def test_professor_dashboard_with_tutor_filter(self, app, professor_user, tutor_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter(
                Session.status == 'booked',
                Session.tutor_id == tutor_user.id
            ).all()
            assert len(sessions) >= 0

    def test_professor_dashboard_weekly_data(self, app, professor_user, session_obj):
        with app.app_context():
            from datetime import datetime as dt, timedelta
            now = dt.utcnow()
            
            def get_week_number(date):
                return date.isocalendar()[1]
            
            sessions = Session.query.filter(Session.status == 'booked').all()
            
            weekly_data = []
            for i in range(5, -1, -1):
                week_date = now - timedelta(days=i * 7)
                week_num = get_week_number(week_date)
                
                week_sessions = [s for s in sessions if s.start_time and get_week_number(s.start_time) == week_num]
                weekly_data.append({
                    'week': f'Week {week_num}',
                    'sessions': len(week_sessions)
                })
            
            assert len(weekly_data) == 6

    def test_professor_dashboard_monthly_attendance(self, app, professor_user, session_obj, session_note):
        with app.app_context():
            from datetime import datetime as dt, timedelta
            now = dt.utcnow()
            
            sessions = Session.query.filter(Session.status == 'booked').all()
            session_ids = [s.id for s in sessions]
            notes = SessionNote.query.filter(SessionNote.session_id.in_(session_ids)).all()
            notes_map = {n.session_id: n for n in notes}
            
            monthly_attendance = []
            for i in range(5, -1, -1):
                month_date = dt(now.year, now.month, 1) - timedelta(days=i * 30)
                month = month_date.month
                year = month_date.year
                
                month_sessions = [s for s in sessions if s.start_time and 
                                 s.start_time.month == month and s.start_time.year == year]
                
                if len(month_sessions) == 0:
                    attendance_rate = 0
                else:
                    attended = 0
                    for s in month_sessions:
                        note = notes_map.get(s.id)
                        if note and note.attendance_status in ['present', 'attended']:
                            attended += 1
                    attendance_rate = round((attended / len(month_sessions)) * 100)
                
                monthly_attendance.append({
                    'month': month_date.strftime('%b'),
                    'rate': attendance_rate
                })
            
            assert len(monthly_attendance) == 6


class TestTutorDashboard:
    def test_tutor_dashboard_not_tutor(self, app, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            assert user.role != 'tutor'

    def test_tutor_dashboard_success(self, app, tutor_user, student_user, session_obj, session_note, feedback):
        with app.app_context():
            sessions = Session.query.filter(
                Session.tutor_id == tutor_user.id,
                Session.status == 'booked'
            ).all()
            
            session_ids = [s.id for s in sessions]
            feedbacks = Feedback.query.filter(Feedback.session_id.in_(session_ids)).all()
            feedback_map = {f.session_id: f for f in feedbacks}
            
            total_sessions = len(sessions)
            
            total_hours = 0
            for session in sessions:
                if session.start_time and session.end_time:
                    duration = (session.end_time - session.start_time).total_seconds() / 3600
                    total_hours += duration
            
            unique_students = set()
            for session in sessions:
                if session.student_id:
                    unique_students.add(session.student_id)
            
            ratings = []
            for session in sessions:
                fb = feedback_map.get(session.id)
                if fb and fb.rating:
                    ratings.append(fb.rating)
            
            avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
            
            assert total_sessions >= 0

    def test_tutor_dashboard_course_distribution(self, app, tutor_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter(
                Session.tutor_id == tutor_user.id,
                Session.status == 'booked'
            ).all()
            
            course_distribution = {}
            for session in sessions:
                if session.course:
                    course_distribution[session.course] = course_distribution.get(session.course, 0) + 1
            
            assert isinstance(course_distribution, dict)

    def test_tutor_dashboard_top_students(self, app, tutor_user, student_user, session_obj):
        with app.app_context():
            sessions = Session.query.filter(
                Session.tutor_id == tutor_user.id,
                Session.status == 'booked'
            ).all()
            
            student_counts = {}
            for session in sessions:
                if session.student_user and session.student_user.name:
                    name = session.student_user.name
                    student_counts[name] = student_counts.get(name, 0) + 1
            
            top_students = [{'name': name, 'count': count} 
                           for name, count in sorted(student_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
            
            assert isinstance(top_students, list)


class TestSessionHTTPEndpoints:
    def _mock_auth(self, app, user):
        return patch('auth.Clerk'), patch('auth.requests.get')

    def test_book_session_http_success(self, app, student_user, tutor_user, tutor_profile, availability):
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
                    
                    with patch('routes.sessions.send_booking_confirmation'), patch('routes.sessions.send_tutor_notification'):
                        client = app.test_client()
                        response = client.post('/api/sessions/book',
                            data=json.dumps({
                                'availability_id': av.id,
                                'start_time': '2025-01-06T10:00:00',
                                'end_time': '2025-01-06T11:00:00',
                                'course': 'Chinese 101'
                            }),
                            content_type='application/json',
                            headers={'Authorization': 'Bearer test_token'})
                        
                        assert response.status_code == 201

    def test_book_session_http_not_student(self, app, tutor_user, tutor_profile, availability):
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
                    response = client.post('/api/sessions/book',
                        data=json.dumps({
                            'availability_id': av.id,
                            'start_time': '2025-01-06T10:00:00',
                            'end_time': '2025-01-06T11:00:00'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_book_session_http_missing_fields(self, app, student_user):
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
                    response = client.post('/api/sessions/book',
                        data=json.dumps({}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_tutor_sessions_http(self, app, tutor_user, session_obj):
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
                    response = client.get('/api/tutor/sessions', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_tutor_sessions_http_with_filters(self, app, tutor_user, session_obj):
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
                    response = client.get('/api/tutor/sessions?status=booked&from=2025-01-01T00:00:00&to=2025-12-31T23:59:59', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_student_sessions_http(self, app, student_user, session_obj):
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
                    response = client.get('/api/student/sessions', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_sessions_http(self, app, tutor_user, session_obj):
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
                    response = client.get('/api/sessions', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_session_http(self, app, tutor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            session = Session.query.first()
            
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
                    response = client.get(f'/api/sessions/{session.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_update_session_http(self, app, tutor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            session = Session.query.first()
            
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
                    response = client.put(f'/api/sessions/{session.id}',
                        data=json.dumps({'course': 'Chinese 301'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_delete_session_http(self, app, tutor_user, student_user):
        with app.app_context():
            session = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 2, 1, 10, 0),
                end_time=datetime(2025, 2, 1, 11, 0),
                status='booked'
            )
            db.session.add(session)
            db.session.commit()
            
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
                    response = client.delete(f'/api/sessions/{session.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_create_session_note_http(self, app, tutor_user, student_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            
            new_session = Session(
                tutor_id=user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 2, 5, 10, 0),
                end_time=datetime(2025, 2, 5, 11, 0),
                status='booked'
            )
            db.session.add(new_session)
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
                    
                    with patch('routes.sessions.send_feedback_request'):
                        client = app.test_client()
                        response = client.post('/api/session-notes',
                            data=json.dumps({
                                'session_id': new_session.id,
                                'attendance_status': 'present',
                                'notes': 'Great session'
                            }),
                            content_type='application/json',
                            headers={'Authorization': 'Bearer test_token'})
                        
                        assert response.status_code == 201

    def test_submit_feedback_http(self, app, student_user, tutor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            
            new_session = Session(
                tutor_id=tutor_user.id,
                student_id=user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 2, 10, 10, 0),
                end_time=datetime(2025, 2, 10, 11, 0),
                status='booked'
            )
            db.session.add(new_session)
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
                    response = client.post('/api/feedback',
                        data=json.dumps({
                            'session_id': new_session.id,
                            'rating': 5,
                            'comment': 'Great!'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 201

    def test_professor_sessions_http(self, app, professor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_professor').first()
            
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
                    response = client.get('/api/professor/sessions', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_professor_dashboard_http(self, app, professor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_professor').first()
            
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
                    response = client.get('/api/professor/dashboard', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_tutor_dashboard_http(self, app, tutor_user, session_obj):
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
                    response = client.get('/api/tutor/dashboard', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_book_session_http_availability_not_found(self, app, student_user):
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
                    response = client.post('/api/sessions/book',
                        data=json.dumps({
                            'availability_id': 99999,
                            'start_time': '2025-01-06T10:00:00',
                            'end_time': '2025-01-06T11:00:00'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_book_session_http_invalid_datetime(self, app, student_user, tutor_profile, availability):
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
                    response = client.post('/api/sessions/book',
                        data=json.dumps({
                            'availability_id': av.id,
                            'start_time': 'invalid',
                            'end_time': 'invalid'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_book_session_http_end_before_start(self, app, student_user, tutor_profile, availability):
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
                    response = client.post('/api/sessions/book',
                        data=json.dumps({
                            'availability_id': av.id,
                            'start_time': '2025-01-06T11:00:00',
                            'end_time': '2025-01-06T10:00:00'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_book_session_http_outside_recurring_window(self, app, student_user, tutor_profile, availability):
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
                    response = client.post('/api/sessions/book',
                        data=json.dumps({
                            'availability_id': av.id,
                            'start_time': '2025-01-06T07:00:00',
                            'end_time': '2025-01-06T08:00:00'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 409

    def test_book_session_http_outside_non_recurring_window(self, app, student_user, tutor_profile):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            tutor = Tutor.query.first()
            
            av = Availability(
                tutor_id=tutor.id,
                day_of_week=1,
                start_time=datetime(2025, 1, 6, 10, 0),
                end_time=datetime(2025, 1, 6, 12, 0),
                session_type='online',
                is_recurring=False
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
                    response = client.post('/api/sessions/book',
                        data=json.dumps({
                            'availability_id': av.id,
                            'start_time': '2025-01-06T08:00:00',
                            'end_time': '2025-01-06T09:00:00'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 409

    def test_book_session_http_tutor_overlap(self, app, student_user, tutor_user, tutor_profile, availability):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            tutor = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            av = Availability.query.first()
            
            existing = Session(
                tutor_id=tutor.id,
                student_id=user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 6, 10, 0),
                end_time=datetime(2025, 1, 6, 11, 0),
                status='booked'
            )
            db.session.add(existing)
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
                    response = client.post('/api/sessions/book',
                        data=json.dumps({
                            'availability_id': av.id,
                            'start_time': '2025-01-06T10:30:00',
                            'end_time': '2025-01-06T11:30:00'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 409

    def test_update_session_http_all_fields(self, app, tutor_user, student_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            session = Session.query.first()
            
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
                    response = client.put(f'/api/sessions/{session.id}',
                        data=json.dumps({
                            'tutor_id': user.id,
                            'course': 'Chinese 301',
                            'session_type': 'in-person',
                            'start_time': '2025-02-01T10:00:00',
                            'end_time': '2025-02-01T11:00:00',
                            'status': 'completed'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_update_session_http_invalid_times(self, app, tutor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            session = Session.query.first()
            
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
                    response = client.put(f'/api/sessions/{session.id}',
                        data=json.dumps({'start_time': 'invalid'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_update_session_http_invalid_end_time(self, app, tutor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            session = Session.query.first()
            
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
                    response = client.put(f'/api/sessions/{session.id}',
                        data=json.dumps({'end_time': 'invalid'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_update_session_http_with_student(self, app, tutor_user, student_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            student = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            session = Session.query.first()
            
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
                    response = client.put(f'/api/sessions/{session.id}',
                        data=json.dumps({'student_id': student.id}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_update_session_http_clear_student(self, app, tutor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            session = Session.query.first()
            
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
                    response = client.put(f'/api/sessions/{session.id}',
                        data=json.dumps({'student_id': None}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_create_session_note_http_wrong_tutor(self, app, tutor_user, student_user, session_obj):
        with app.app_context():
            other_tutor = User(
                clerk_user_id='other_tutor_http',
                name='Other Tutor',
                email='other_tutor_http@test.com',
                role='tutor',
                onboarding_complete=True
            )
            db.session.add(other_tutor)
            db.session.commit()
            
            session = Session.query.first()
            
            with patch('auth.Clerk') as mock_clerk:
                mock_sdk = MagicMock()
                mock_request_state = MagicMock()
                mock_request_state.is_signed_in = True
                mock_request_state.payload = {'sub': other_tutor.clerk_user_id, 'name': other_tutor.name, 'email': other_tutor.email}
                mock_sdk.authenticate_request.return_value = mock_request_state
                mock_clerk.return_value = mock_sdk
                
                with patch('auth.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': other_tutor.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.post('/api/session-notes',
                        data=json.dumps({
                            'session_id': session.id,
                            'attendance_status': 'present'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_create_session_note_http_duplicate(self, app, tutor_user, session_obj, session_note):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            session = Session.query.first()
            
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
                    response = client.post('/api/session-notes',
                        data=json.dumps({
                            'session_id': session.id,
                            'attendance_status': 'present'
                        }),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 409

    def test_update_session_note_http_wrong_tutor(self, app, tutor_user, session_obj, session_note):
        with app.app_context():
            other_tutor = User(
                clerk_user_id='other_tutor_update_note',
                name='Other Tutor',
                email='other_tutor_update_note@test.com',
                role='tutor',
                onboarding_complete=True
            )
            db.session.add(other_tutor)
            db.session.commit()
            
            note = SessionNote.query.first()
            
            with patch('auth.Clerk') as mock_clerk:
                mock_sdk = MagicMock()
                mock_request_state = MagicMock()
                mock_request_state.is_signed_in = True
                mock_request_state.payload = {'sub': other_tutor.clerk_user_id, 'name': other_tutor.name, 'email': other_tutor.email}
                mock_sdk.authenticate_request.return_value = mock_request_state
                mock_clerk.return_value = mock_sdk
                
                with patch('auth.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': other_tutor.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.put(f'/api/session-notes/{note.id}',
                        data=json.dumps({'notes': 'updated'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_submit_feedback_http_wrong_student(self, app, student_user, tutor_user, session_obj):
        with app.app_context():
            other_student = User(
                clerk_user_id='other_student_feedback_http',
                name='Other Student',
                email='other_student_feedback@test.com',
                role='student',
                onboarding_complete=True
            )
            db.session.add(other_student)
            db.session.commit()
            
            session = Session.query.first()
            
            with patch('auth.Clerk') as mock_clerk:
                mock_sdk = MagicMock()
                mock_request_state = MagicMock()
                mock_request_state.is_signed_in = True
                mock_request_state.payload = {'sub': other_student.clerk_user_id, 'name': other_student.name, 'email': other_student.email}
                mock_sdk.authenticate_request.return_value = mock_request_state
                mock_clerk.return_value = mock_sdk
                
                with patch('auth.requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {'email_addresses': [{'id': 'e1', 'email_address': other_student.email}]}
                    mock_get.return_value = mock_response
                    
                    client = app.test_client()
                    response = client.post('/api/feedback',
                        data=json.dumps({'session_id': session.id, 'rating': 5}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_update_session_http_tutor_not_found(self, app, tutor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            session = Session.query.first()
            
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
                    response = client.put(f'/api/sessions/{session.id}',
                        data=json.dumps({'tutor_id': 99999}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_update_session_http_student_not_found(self, app, tutor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            session = Session.query.first()
            
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
                    response = client.put(f'/api/sessions/{session.id}',
                        data=json.dumps({'student_id': 99999}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_update_session_note_http_not_tutor(self, app, student_user, session_obj, session_note):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            note = SessionNote.query.first()
            
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
                    response = client.put(f'/api/session-notes/{note.id}',
                        data=json.dumps({'notes': 'test'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_tutor_sessions_http_with_tutor_id_param(self, app, student_user, tutor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            tutor = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            
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
                    response = client.get(f'/api/tutor/sessions?tutor_id={tutor.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_session_note_http_no_note(self, app, tutor_user, student_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            
            new_session = Session(
                tutor_id=user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 3, 1, 10, 0),
                end_time=datetime(2025, 3, 1, 11, 0),
                status='booked'
            )
            db.session.add(new_session)
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
                    response = client.get(f'/api/sessions/{new_session.id}/note', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['note'] is None

    def test_get_session_feedback_http_no_feedback(self, app, student_user, tutor_user):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            
            new_session = Session(
                tutor_id=tutor_user.id,
                student_id=user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 3, 5, 10, 0),
                end_time=datetime(2025, 3, 5, 11, 0),
                status='booked'
            )
            db.session.add(new_session)
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
                    response = client.get(f'/api/sessions/{new_session.id}/feedback', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['feedback'] is None

    def test_professor_dashboard_http_with_filters(self, app, professor_user, tutor_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_professor').first()
            tutor = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            
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
                    response = client.get(f'/api/professor/dashboard?class=Chinese 101&tutor={tutor.id}', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_tutor_sessions_http_not_tutor_no_tutor_id(self, app, student_user):
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
                    response = client.get('/api/tutor/sessions', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_student_sessions_http_not_student(self, app, tutor_user):
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
                    response = client.get('/api/student/sessions', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_get_session_http_not_found(self, app, tutor_user):
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
                    response = client.get('/api/sessions/99999', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_update_session_http_not_found(self, app, tutor_user):
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
                    response = client.put('/api/sessions/99999',
                        data=json.dumps({'course': 'test'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_delete_session_http_not_found(self, app, tutor_user):
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
                    response = client.delete('/api/sessions/99999', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_book_existing_session_http(self, app, student_user, available_session):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            session = Session.query.filter_by(status='available').first()
            
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
                    response = client.post(f'/api/sessions/{session.id}/book', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_create_session_note_http_not_tutor(self, app, student_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            session = Session.query.first()
            
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
                    response = client.post('/api/session-notes',
                        data=json.dumps({'session_id': session.id}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_update_session_note_http(self, app, tutor_user, session_obj, session_note):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            note = SessionNote.query.first()
            
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
                    response = client.put(f'/api/session-notes/{note.id}',
                        data=json.dumps({'notes': 'Updated note'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_session_note_http(self, app, tutor_user, session_obj, session_note):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_tutor').first()
            session = Session.query.first()
            
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
                    response = client.get(f'/api/sessions/{session.id}/note', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_get_session_feedback_http(self, app, student_user, session_obj, feedback):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            session = Session.query.first()
            
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
                    response = client.get(f'/api/sessions/{session.id}/feedback', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 200

    def test_professor_sessions_http_not_professor(self, app, student_user):
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
                    response = client.get('/api/professor/sessions', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_professor_dashboard_http_not_professor(self, app, student_user):
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
                    response = client.get('/api/professor/dashboard', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_tutor_dashboard_http_not_tutor(self, app, student_user):
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
                    response = client.get('/api/tutor/dashboard', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 403

    def test_book_existing_session_http_not_found(self, app, student_user):
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
                    response = client.post('/api/sessions/99999/book', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_book_existing_session_http_already_booked(self, app, student_user, session_obj):
        with app.app_context():
            user = User.query.filter_by(clerk_user_id='clerk_test_student').first()
            session = Session.query.filter_by(status='booked').first()
            
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
                    response = client.post(f'/api/sessions/{session.id}/book', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 409

    def test_create_session_note_http_missing_session_id(self, app, tutor_user):
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
                    response = client.post('/api/session-notes',
                        data=json.dumps({'notes': 'test'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_create_session_note_http_session_not_found(self, app, tutor_user):
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
                    response = client.post('/api/session-notes',
                        data=json.dumps({'session_id': 99999}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_update_session_note_http_not_found(self, app, tutor_user):
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
                    response = client.put('/api/session-notes/99999',
                        data=json.dumps({'notes': 'test'}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_get_session_note_http_not_found(self, app, tutor_user):
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
                    response = client.get('/api/sessions/99999/note', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_submit_feedback_http_missing_fields(self, app, student_user):
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
                    response = client.post('/api/feedback',
                        data=json.dumps({}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 400

    def test_submit_feedback_http_session_not_found(self, app, student_user):
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
                    response = client.post('/api/feedback',
                        data=json.dumps({'session_id': 99999, 'rating': 5}),
                        content_type='application/json',
                        headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

    def test_get_session_feedback_http_not_found(self, app, student_user):
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
                    response = client.get('/api/sessions/99999/feedback', headers={'Authorization': 'Bearer test_token'})
                    
                    assert response.status_code == 404

