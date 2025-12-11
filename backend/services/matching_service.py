from models import db, User, Tutor, Availability, Session, Feedback
from datetime import datetime
from sqlalchemy import func


def calculate_tutor_match_scores(student_id, preferred_day=None, preferred_time=None, preferred_session_type=None):
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
        
        schedule_score = calculate_schedule_score(
            tutor_profile.id, 
            preferred_day, 
            preferred_time
        )
        score += schedule_score
        score_breakdown['schedule_compatibility'] = schedule_score
        
        session_type_score = calculate_session_type_score(
            tutor_profile.id, 
            preferred_session_type
        )
        score += session_type_score
        score_breakdown['session_type_match'] = session_type_score
        
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
    WEIGHT = 40.0
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
    WEIGHT = 25.0
    
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


def calculate_schedule_score(tutor_profile_id, preferred_day, preferred_time):
    WEIGHT = 20.0
    
    availabilities = Availability.query.filter_by(tutor_id=tutor_profile_id).all()
    
    if not availabilities:
        return 0.0
    
    if preferred_day is None and preferred_time is None:
        return WEIGHT * 0.5
    
    best_match = 0.0
    
    for av in availabilities:
        match = 0.0
        
        if preferred_day is not None and av.day_of_week == preferred_day:
            match += 0.5
        
        if preferred_time is not None:
            try:
                if isinstance(preferred_time, str):
                    pref_time = datetime.strptime(preferred_time, "%H:%M").time()
                else:
                    pref_time = preferred_time
                
                av_start = av.start_time.time()
                av_end = av.end_time.time()
                
                if av_start <= pref_time <= av_end:
                    match += 0.5
            except (ValueError, AttributeError):
                pass
        
        best_match = max(best_match, match)
    
    return WEIGHT * best_match


def calculate_session_type_score(tutor_profile_id, preferred_session_type):
    WEIGHT = 15.0
    
    if not preferred_session_type:
        return WEIGHT * 0.5
    
    matching_availability = Availability.query.filter_by(
        tutor_id=tutor_profile_id,
        session_type=preferred_session_type
    ).first()
    
    if matching_availability:
        return WEIGHT
    
    return 0.0


def get_recommended_tutors(student_id, preferred_day=None, preferred_time=None, preferred_session_type=None, limit=5):
    scores = calculate_tutor_match_scores(
        student_id,
        preferred_day,
        preferred_time,
        preferred_session_type
    )
    
    return scores[:limit]

