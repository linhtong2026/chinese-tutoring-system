from models import db, User, Tutor, Availability, Session, Feedback
from sqlalchemy import func


def calculate_tutor_match_scores(student_id):
    student = User.query.get(student_id)
    if not student:
        return []

    tutors = User.query.filter(User.role == 'tutor').all()
    
    tutor_scores = []
    
    for tutor in tutors:
        tutor_profile = Tutor.query.filter_by(user_id=tutor.id).first()
        if not tutor_profile:
            continue
        
        score = 0.0
        score_breakdown = {}
        
        previous_session_score = calculate_previous_session_score(student_id, tutor.id)
        score += previous_session_score
        score_breakdown['previous_sessions'] = previous_session_score
        
        rating_score = calculate_rating_score(tutor.id)
        score += rating_score
        score_breakdown['rating'] = rating_score
        
        availability_score = calculate_availability_score(tutor_profile.id)
        score += availability_score
        score_breakdown['availability'] = availability_score
        
        tutor_scores.append({
            'tutor_id': tutor.id,
            'tutor_name': tutor.name,
            'tutor_email': tutor.email,
            'total_score': round(score, 2),
            'score_breakdown': score_breakdown
        })
    
    tutor_scores.sort(key=lambda x: x['total_score'], reverse=True)
    
    return tutor_scores


def calculate_previous_session_score(student_id, tutor_id):
    WEIGHT = 50.0
    MAX_SESSIONS_FOR_FULL_SCORE = 5
    
    previous_sessions = Session.query.filter(
        Session.student_id == student_id,
        Session.tutor_id == tutor_id,
        Session.status == 'booked'
    ).count()
    
    if previous_sessions == 0:
        return 0.0
    
    session_factor = min(previous_sessions / MAX_SESSIONS_FOR_FULL_SCORE, 1.0)
    
    return WEIGHT * session_factor


def calculate_rating_score(tutor_id):
    WEIGHT = 35.0
    
    tutor_sessions = Session.query.filter(Session.tutor_id == tutor_id).all()
    session_ids = [s.id for s in tutor_sessions]
    
    if not session_ids:
        return WEIGHT * 0.5
    
    avg_rating = db.session.query(func.avg(Feedback.rating)).filter(
        Feedback.session_id.in_(session_ids)
    ).scalar()
    
    if avg_rating is None:
        return WEIGHT * 0.5
    
    normalized_rating = avg_rating / 5.0
    
    return WEIGHT * normalized_rating


def calculate_availability_score(tutor_profile_id):
    WEIGHT = 15.0
    
    availability_count = Availability.query.filter_by(tutor_id=tutor_profile_id).count()
    
    if availability_count == 0:
        return 0.0
    
    score_factor = min(availability_count / 5.0, 1.0)
    
    return WEIGHT * score_factor


def get_recommended_tutors(student_id):
    scores = calculate_tutor_match_scores(student_id)
    return scores

