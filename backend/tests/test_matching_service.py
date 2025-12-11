import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User, Tutor, Session, Feedback, Availability
from services.matching_service import (
    calculate_tutor_match_scores,
    calculate_previous_session_score,
    calculate_rating_score,
    calculate_availability_score,
    get_recommended_tutors
)


class TestCalculatePreviousSessionScore:
    def test_no_previous_sessions(self, app, student_user, tutor_user):
        with app.app_context():
            score = calculate_previous_session_score(student_user.id, tutor_user.id)
            assert score == 0.0

    def test_one_previous_session(self, app, student_user, tutor_user):
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
            
            score = calculate_previous_session_score(student_user.id, tutor_user.id)
            assert score > 0.0
            assert score == 50.0 * (1 / 5)

    def test_five_previous_sessions(self, app, student_user, tutor_user):
        with app.app_context():
            for i in range(5):
                session = Session(
                    tutor_id=tutor_user.id,
                    student_id=student_user.id,
                    course='Chinese 101',
                    session_type='online',
                    start_time=datetime(2025, 1, 6 + i, 10, 0),
                    end_time=datetime(2025, 1, 6 + i, 11, 0),
                    status='booked'
                )
                db.session.add(session)
            db.session.commit()
            
            score = calculate_previous_session_score(student_user.id, tutor_user.id)
            assert score == 50.0

    def test_more_than_five_sessions(self, app, student_user, tutor_user):
        with app.app_context():
            for i in range(10):
                session = Session(
                    tutor_id=tutor_user.id,
                    student_id=student_user.id,
                    course='Chinese 101',
                    session_type='online',
                    start_time=datetime(2025, 1, 6 + i, 10, 0),
                    end_time=datetime(2025, 1, 6 + i, 11, 0),
                    status='booked'
                )
                db.session.add(session)
            db.session.commit()
            
            score = calculate_previous_session_score(student_user.id, tutor_user.id)
            assert score == 50.0

    def test_only_booked_sessions_count(self, app, student_user, tutor_user):
        with app.app_context():
            session_booked = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 6, 10, 0),
                end_time=datetime(2025, 1, 6, 11, 0),
                status='booked'
            )
            session_available = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 7, 10, 0),
                end_time=datetime(2025, 1, 7, 11, 0),
                status='available'
            )
            db.session.add(session_booked)
            db.session.add(session_available)
            db.session.commit()
            
            score = calculate_previous_session_score(student_user.id, tutor_user.id)
            assert score == 50.0 * (1 / 5)


class TestCalculateRatingScore:
    def test_no_sessions(self, app, tutor_user):
        with app.app_context():
            score = calculate_rating_score(tutor_user.id)
            assert score == 35.0 * 0.5

    def test_sessions_no_feedback(self, app, tutor_user, student_user):
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
            
            score = calculate_rating_score(tutor_user.id)
            assert score == 35.0 * 0.5

    def test_perfect_rating(self, app, tutor_user, student_user):
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
            
            feedback = Feedback(
                session_id=session.id,
                student_id=student_user.id,
                rating=5.0,
                comment='Perfect!'
            )
            db.session.add(feedback)
            db.session.commit()
            
            score = calculate_rating_score(tutor_user.id)
            assert score == 35.0

    def test_average_rating(self, app, tutor_user, student_user):
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
            session2 = Session(
                tutor_id=tutor_user.id,
                student_id=student_user.id,
                course='Chinese 101',
                session_type='online',
                start_time=datetime(2025, 1, 7, 10, 0),
                end_time=datetime(2025, 1, 7, 11, 0),
                status='booked'
            )
            db.session.add(session1)
            db.session.add(session2)
            db.session.commit()
            
            feedback1 = Feedback(
                session_id=session1.id,
                student_id=student_user.id,
                rating=5.0,
                comment='Great!'
            )
            feedback2 = Feedback(
                session_id=session2.id,
                student_id=student_user.id,
                rating=3.0,
                comment='Good'
            )
            db.session.add(feedback1)
            db.session.add(feedback2)
            db.session.commit()
            
            score = calculate_rating_score(tutor_user.id)
            expected_score = 35.0 * (4.0 / 5.0)
            assert score == expected_score

    def test_low_rating(self, app, tutor_user, student_user):
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
            
            feedback = Feedback(
                session_id=session.id,
                student_id=student_user.id,
                rating=1.0,
                comment='Not great'
            )
            db.session.add(feedback)
            db.session.commit()
            
            score = calculate_rating_score(tutor_user.id)
            assert score == 35.0 * (1.0 / 5.0)


class TestCalculateAvailabilityScore:
    def test_no_availability(self, app, tutor_profile):
        with app.app_context():
            score = calculate_availability_score(tutor_profile.id)
            assert score == 0.0

    def test_one_availability(self, app, tutor_profile):
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
            
            score = calculate_availability_score(tutor_profile.id)
            assert score == 15.0 * (1 / 5.0)

    def test_five_availabilities(self, app, tutor_profile):
        with app.app_context():
            for i in range(5):
                av = Availability(
                    tutor_id=tutor_profile.id,
                    day_of_week=i,
                    start_time=datetime(2025, 1, 6, 9, 0),
                    end_time=datetime(2025, 1, 6, 17, 0),
                    session_type='online',
                    is_recurring=True
                )
                db.session.add(av)
            db.session.commit()
            
            score = calculate_availability_score(tutor_profile.id)
            assert score == 15.0

    def test_more_than_five_availabilities(self, app, tutor_profile):
        with app.app_context():
            for i in range(10):
                av = Availability(
                    tutor_id=tutor_profile.id,
                    day_of_week=i % 7,
                    start_time=datetime(2025, 1, 6, 9 + (i % 8), 0),
                    end_time=datetime(2025, 1, 6, 10 + (i % 8), 0),
                    session_type='online',
                    is_recurring=True
                )
                db.session.add(av)
            db.session.commit()
            
            score = calculate_availability_score(tutor_profile.id)
            assert score == 15.0


class TestCalculateTutorMatchScores:
    def test_no_tutors(self, app, student_user):
        with app.app_context():
            scores = calculate_tutor_match_scores(student_user.id)
            assert scores == []

    def test_invalid_student(self, app):
        with app.app_context():
            scores = calculate_tutor_match_scores(99999)
            assert scores == []

    def test_single_tutor(self, app, student_user, tutor_user, tutor_profile):
        with app.app_context():
            scores = calculate_tutor_match_scores(student_user.id)
            assert len(scores) == 1
            assert scores[0]['tutor_id'] == tutor_user.id
            assert scores[0]['tutor_name'] == tutor_user.name
            assert scores[0]['tutor_email'] == tutor_user.email
            assert 'total_score' in scores[0]
            assert 'score_breakdown' in scores[0]
            assert 'previous_sessions' in scores[0]['score_breakdown']
            assert 'rating' in scores[0]['score_breakdown']
            assert 'availability' in scores[0]['score_breakdown']

    def test_multiple_tutors_sorted(self, app, student_user, tutor_user, tutor_profile):
        with app.app_context():
            tutor2 = User(
                clerk_user_id='clerk_test_tutor2',
                name='Test Tutor 2',
                email='tutor2@test.com',
                role='tutor',
                language_preference='en',
                onboarding_complete=True
            )
            db.session.add(tutor2)
            db.session.commit()
            
            tutor_profile2 = Tutor(
                user_id=tutor2.id,
                specialization='Chinese Conversation',
                availability_notes='Available weekends'
            )
            db.session.add(tutor_profile2)
            db.session.commit()
            
            for i in range(3):
                session = Session(
                    tutor_id=tutor_user.id,
                    student_id=student_user.id,
                    course='Chinese 101',
                    session_type='online',
                    start_time=datetime(2025, 1, 6 + i, 10, 0),
                    end_time=datetime(2025, 1, 6 + i, 11, 0),
                    status='booked'
                )
                db.session.add(session)
            db.session.commit()
            
            scores = calculate_tutor_match_scores(student_user.id)
            assert len(scores) == 2
            assert scores[0]['total_score'] >= scores[1]['total_score']
            assert scores[0]['tutor_id'] == tutor_user.id

    def test_tutor_without_profile_excluded(self, app, student_user):
        with app.app_context():
            tutor_no_profile = User(
                clerk_user_id='clerk_test_tutor_no_profile',
                name='Tutor No Profile',
                email='tutor_no_profile@test.com',
                role='tutor',
                language_preference='en',
                onboarding_complete=True
            )
            db.session.add(tutor_no_profile)
            db.session.commit()
            
            scores = calculate_tutor_match_scores(student_user.id)
            assert len(scores) == 0

    def test_score_breakdown_correct(self, app, student_user, tutor_user, tutor_profile):
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
            
            feedback = Feedback(
                session_id=session.id,
                student_id=student_user.id,
                rating=5.0,
                comment='Excellent!'
            )
            db.session.add(feedback)
            db.session.commit()
            
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
            
            scores = calculate_tutor_match_scores(student_user.id)
            assert len(scores) == 1
            breakdown = scores[0]['score_breakdown']
            assert breakdown['previous_sessions'] > 0
            assert breakdown['rating'] > 0
            assert breakdown['availability'] > 0
            
            total = breakdown['previous_sessions'] + breakdown['rating'] + breakdown['availability']
            assert round(total, 2) == scores[0]['total_score']


class TestGetRecommendedTutors:
    def test_get_recommended_tutors(self, app, student_user, tutor_user, tutor_profile):
        with app.app_context():
            recommendations = get_recommended_tutors(student_user.id)
            assert isinstance(recommendations, list)
            assert len(recommendations) == 1
            assert recommendations[0]['tutor_id'] == tutor_user.id

    def test_get_recommended_tutors_no_student(self, app):
        with app.app_context():
            recommendations = get_recommended_tutors(99999)
            assert recommendations == []

    def test_get_recommended_tutors_returns_sorted(self, app, student_user, tutor_user, tutor_profile):
        with app.app_context():
            tutor2 = User(
                clerk_user_id='clerk_test_tutor2',
                name='Test Tutor 2',
                email='tutor2@test.com',
                role='tutor',
                language_preference='en',
                onboarding_complete=True
            )
            db.session.add(tutor2)
            db.session.commit()
            
            tutor_profile2 = Tutor(
                user_id=tutor2.id,
                specialization='Chinese Conversation',
                availability_notes='Available weekends'
            )
            db.session.add(tutor_profile2)
            db.session.commit()
            
            for i in range(5):
                av = Availability(
                    tutor_id=tutor_profile2.id,
                    day_of_week=i,
                    start_time=datetime(2025, 1, 6, 9, 0),
                    end_time=datetime(2025, 1, 6, 17, 0),
                    session_type='online',
                    is_recurring=True
                )
                db.session.add(av)
            db.session.commit()
            
            recommendations = get_recommended_tutors(student_user.id)
            assert len(recommendations) == 2
            assert recommendations[0]['total_score'] >= recommendations[1]['total_score']

