import pytest
from unittest.mock import patch
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User, Tutor, Session, Feedback, Availability


class TestMatchingRecommendEndpoint:
    def test_recommend_tutors_unauthorized(self, client):
        response = client.get('/api/matching/recommend')
        assert response.status_code == 401

    def test_recommend_tutors_non_student(self, app, tutor_auth_client, tutor_user):
        with app.app_context():
            response = tutor_auth_client.get('/api/matching/recommend')
            assert response.status_code == 403
            data = response.get_json()
            assert data['error'] == 'Only students can get tutor recommendations'

    def test_recommend_tutors_student_no_tutors(self, app, auth_client, student_user):
        with app.app_context():
            response = auth_client.get('/api/matching/recommend')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['recommendations'] == []

    def test_recommend_tutors_with_available_tutors(self, app, auth_client, student_user, tutor_user, tutor_profile):
        with app.app_context():
            response = auth_client.get('/api/matching/recommend')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['recommendations'], list)
            assert len(data['recommendations']) == 1
            assert data['recommendations'][0]['tutor_id'] == tutor_user.id
            assert data['recommendations'][0]['tutor_name'] == tutor_user.name
            assert data['recommendations'][0]['tutor_email'] == tutor_user.email
            assert 'total_score' in data['recommendations'][0]
            assert 'score_breakdown' in data['recommendations'][0]

    def test_recommend_tutors_multiple_tutors(self, app, auth_client, student_user, tutor_user, tutor_profile):
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
            
            response = auth_client.get('/api/matching/recommend')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert len(data['recommendations']) == 2

    def test_recommend_tutors_with_previous_sessions(self, app, auth_client, student_user, tutor_user, tutor_profile):
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
            
            response = auth_client.get('/api/matching/recommend')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert len(data['recommendations']) == 1
            recommendation = data['recommendations'][0]
            assert recommendation['tutor_id'] == tutor_user.id
            assert recommendation['score_breakdown']['previous_sessions'] > 0

    def test_recommend_tutors_with_ratings(self, app, auth_client, student_user, tutor_user, tutor_profile):
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
                comment='Excellent tutor!'
            )
            db.session.add(feedback)
            db.session.commit()
            
            response = auth_client.get('/api/matching/recommend')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            recommendation = data['recommendations'][0]
            assert recommendation['score_breakdown']['rating'] > 0

    def test_recommend_tutors_with_availability(self, app, auth_client, student_user, tutor_user, tutor_profile):
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
            
            response = auth_client.get('/api/matching/recommend')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            recommendation = data['recommendations'][0]
            assert recommendation['score_breakdown']['availability'] > 0

    def test_recommend_tutors_score_ordering(self, app, auth_client, student_user, tutor_user, tutor_profile):
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
            
            response = auth_client.get('/api/matching/recommend')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert len(data['recommendations']) == 2
            
            first_score = data['recommendations'][0]['total_score']
            second_score = data['recommendations'][1]['total_score']
            assert first_score >= second_score

    def test_recommend_tutors_tutor_without_profile_excluded(self, app, auth_client, student_user):
        with app.app_context():
            tutor_without_profile = User(
                clerk_user_id='clerk_test_tutor_no_profile',
                name='Tutor No Profile',
                email='tutor_no_profile@test.com',
                role='tutor',
                language_preference='en',
                onboarding_complete=True
            )
            db.session.add(tutor_without_profile)
            db.session.commit()
            
            response = auth_client.get('/api/matching/recommend')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert len(data['recommendations']) == 0

    def test_recommend_tutors_professor_forbidden(self, app, professor_auth_client, professor_user):
        with app.app_context():
            response = professor_auth_client.get('/api/matching/recommend')
            assert response.status_code == 403
            data = response.get_json()
            assert data['error'] == 'Only students can get tutor recommendations'

