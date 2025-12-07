from flask import Blueprint, jsonify, request
from models import db, Session, User, Availability, Tutor, SessionNote, Feedback
from auth import require_auth
from datetime import datetime
from sqlalchemy.orm import joinedload, subqueryload
from services.email_service import send_booking_confirmation, send_tutor_notification, send_feedback_request
import time

session_bp = Blueprint("session", __name__)


@session_bp.route("/api/sessions/book", methods=["POST"])
@require_auth
def book_session():
    data = request.get_json() or {}

    # Only students can book
    current_user: User = getattr(request, "db_user", None)
    if not current_user or current_user.role != "student":
        return jsonify({"error": "Forbidden"}), 403

    availability_id = data.get("availability_id")
    start_time_str = data.get("start_time")
    end_time_str = data.get("end_time")
    course = data.get("course")

    if not availability_id or not start_time_str or not end_time_str:
        return (
            jsonify({"error": "availability_id, start_time, end_time are required"}),
            400,
        )

    availability = Availability.query.get(availability_id)
    if not availability:
        return jsonify({"error": "Availability not found"}), 404

    try:
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400

    if end_time <= start_time:
        return jsonify({"error": "end_time must be after start_time"}), 400

    if availability.is_recurring:
        av_start_time = availability.start_time.time()
        av_end_time = availability.end_time.time()
        req_start_time = start_time.time()
        req_end_time = end_time.time()

        print(f"DEBUG: Recurring availability - comparing times only")
        print(f"DEBUG: Availability time window: {av_start_time} to {av_end_time}")
        print(f"DEBUG: Requested time window: {req_start_time} to {req_end_time}")

        if not (av_start_time <= req_start_time and req_end_time <= av_end_time):
            return jsonify({"error": "Requested time outside availability window"}), 409
    else:
        if not (
            availability.start_time <= start_time and end_time <= availability.end_time
        ):
            return jsonify({"error": "Requested time outside availability window"}), 409

    # Find the tutor's user_id from Availability -> Tutor -> User
    tutor_profile: Tutor = availability.tutor
    if not tutor_profile or not tutor_profile.user_id:
        return jsonify({"error": "Tutor profile misconfigured"}), 500
    tutor_user_id = tutor_profile.user_id

    # Ensure no overlapping session exists for the tutor in that window
    overlap = Session.query.filter(
        Session.tutor_id == tutor_user_id,
        Session.start_time < end_time,
        Session.end_time > start_time,
    ).first()
    if overlap:
        return jsonify({"error": "Tutor already has a session at this time"}), 409

    # Create the session (only created when a student books)
    new_session = Session(
        tutor_id=tutor_user_id,
        student_id=current_user.id,
        course=course,
        session_type=availability.session_type,
        start_time=start_time,
        end_time=end_time,
        status="booked",
    )
    db.session.add(new_session)

    db.session.commit()

    tutor_user = User.query.get(tutor_user_id)
    session_data = new_session.to_dict()
    
    try:
        send_booking_confirmation(
            student_email=current_user.email,
            student_name=current_user.name,
            tutor_name=tutor_user.name if tutor_user else "Tutor",
            session_data=session_data
        )
        
        if tutor_user:
            send_tutor_notification(
                tutor_email=tutor_user.email,
                tutor_name=tutor_user.name,
                student_name=current_user.name,
                session_data=session_data
            )
    except Exception as e:
        print(f"Error sending booking emails: {e}")

    return jsonify({"session": new_session.to_dict()}), 201


@session_bp.route("/api/tutor/sessions", methods=["GET"])
@require_auth
def tutor_list_sessions():
    route_start = time.time()
    print(f"[TIMING] /api/tutor/sessions - Route started")
    
    current_user: User = getattr(request, "db_user", None)
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    tutor_id = request.args.get("tutor_id")

    if current_user.role == "tutor":
        q = Session.query.options(joinedload(Session.student_user)).filter(Session.tutor_id == current_user.id)
    elif tutor_id:
        q = Session.query.options(joinedload(Session.student_user)).filter(Session.tutor_id == tutor_id)
    else:
        return jsonify({"error": "tutor_id is required for non-tutor users"}), 400

    statuses = request.args.get("status")
    dt_from = request.args.get("from")
    dt_to = request.args.get("to")

    if statuses:
        allowed = [s.strip() for s in statuses.split(",") if s.strip()]
        if allowed:
            q = q.filter(Session.status.in_(allowed))

    def parse_dt(s):
        try:
            return datetime.fromisoformat(s) if s else None
        except Exception:
            return None

    p_from = parse_dt(dt_from)
    p_to = parse_dt(dt_to)
    if p_from:
        q = q.filter(Session.start_time >= p_from)
    if p_to:
        q = q.filter(Session.end_time <= p_to)

    query_start = time.time()
    sessions = q.order_by(Session.start_time.asc()).all()
    print(f"[TIMING] /api/tutor/sessions - Session query (with eager load): {(time.time() - query_start)*1000:.2f}ms ({len(sessions)} sessions)")
    
    serialize_start = time.time()
    result = [s.to_dict() for s in sessions]
    print(f"[TIMING] /api/tutor/sessions - Serialization: {(time.time() - serialize_start)*1000:.2f}ms")
    
    print(f"[TIMING] /api/tutor/sessions - Total route time: {(time.time() - route_start)*1000:.2f}ms")
    return jsonify({"sessions": result})


@session_bp.route("/api/student/sessions", methods=["GET"])
@require_auth
def student_my_sessions():
    current_user: User = getattr(request, "db_user", None)
    if not current_user or current_user.role != "student":
        return jsonify({"error": "Forbidden"}), 403

    sessions = Session.query.options(
        joinedload(Session.student_user),
        joinedload(Session.tutor_user)
    ).filter(Session.student_id == current_user.id).order_by(Session.start_time.asc()).all()
    
    session_ids = [s.id for s in sessions]
    feedbacks = Feedback.query.filter(Feedback.session_id.in_(session_ids)).all() if session_ids else []
    feedback_map = {f.session_id: f for f in feedbacks}
    
    sessions_data = []
    for session in sessions:
        session_dict = session.to_dict()
        if session.tutor_user:
            session_dict['tutor_name'] = session.tutor_user.name
        feedback = feedback_map.get(session.id)
        session_dict['feedback'] = feedback.to_dict() if feedback else None
        sessions_data.append(session_dict)
    
    return jsonify({"sessions": sessions_data})


@session_bp.route("/api/sessions", methods=["GET"])
@require_auth
def get_sessions():
    tutor_id = request.args.get("tutor_id")
    student_id = request.args.get("student_id")

    query = Session.query.options(joinedload(Session.student_user))

    if tutor_id:
        query = query.filter_by(tutor_id=tutor_id)
    if student_id:
        query = query.filter_by(student_id=student_id)

    sessions = query.all()

    return jsonify({"success": True, "sessions": [s.to_dict() for s in sessions]})


@session_bp.route("/api/sessions/<int:session_id>", methods=["GET"])
@require_auth
def get_session(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    return jsonify({"success": True, "session": session.to_dict()})


@session_bp.route("/api/sessions/<int:session_id>", methods=["PUT"])
@require_auth
def update_session(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()

    if "tutor_id" in data:
        tutor = User.query.get(data["tutor_id"])
        if not tutor:
            return jsonify({"error": "Tutor not found"}), 404
        session.tutor_id = data["tutor_id"]

    if "student_id" in data:
        if data["student_id"]:
            student = User.query.get(data["student_id"])
            if not student:
                return jsonify({"error": "Student not found"}), 404
        session.student_id = data["student_id"]

    if "course" in data:
        session.course = data["course"]

    if "session_type" in data:
        session.session_type = data["session_type"]

    if "start_time" in data:
        try:
            session.start_time = datetime.fromisoformat(data["start_time"])
        except ValueError:
            return jsonify({"error": "Invalid datetime format for start_time"}), 400

    if "end_time" in data:
        try:
            session.end_time = datetime.fromisoformat(data["end_time"])
        except ValueError:
            return jsonify({"error": "Invalid datetime format for end_time"}), 400

    if "status" in data:
        session.status = data["status"]

    db.session.commit()

    return jsonify({"success": True, "session": session.to_dict()})


@session_bp.route("/api/sessions/<int:session_id>", methods=["DELETE"])
@require_auth
def delete_session(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    db.session.delete(session)
    db.session.commit()

    return jsonify({"success": True, "message": "Session deleted"})


@session_bp.route("/api/sessions/<int:session_id>/book", methods=["POST"])
@require_auth
def book_existing_session(session_id):
    current_user: User = getattr(request, "db_user", None)
    if not current_user or current_user.role != "student":
        return jsonify({"error": "Forbidden"}), 403

    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    if session.status == "booked":
        return jsonify({"error": "Session already booked"}), 409

    session.status = "booked"
    session.student_id = current_user.id
    db.session.commit()

    return jsonify({"success": True, "session": session.to_dict()})


@session_bp.route("/api/session-notes", methods=["POST"])
@require_auth
def create_session_note():
    current_user: User = getattr(request, "db_user", None)
    if not current_user or current_user.role != "tutor":
        return jsonify({"error": "Forbidden"}), 403

    data = request.get_json()
    session_id = data.get("session_id")
    attendance_status = data.get("attendance_status")
    notes = data.get("notes")
    student_feedback = data.get("student_feedback")

    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    if session.tutor_id != current_user.id:
        return jsonify({"error": "You can only add notes to your own sessions"}), 403

    existing_note = SessionNote.query.filter_by(
        session_id=session_id, tutor_id=current_user.id
    ).first()

    if existing_note:
        return jsonify({"error": "Note already exists for this session"}), 409

    new_note = SessionNote(
        session_id=session_id,
        tutor_id=current_user.id,
        attendance_status=attendance_status,
        notes=notes,
        student_feedback=student_feedback,
    )
    db.session.add(new_note)
    db.session.commit()

    if attendance_status in ['present', 'attended', 'late']:
        student = User.query.get(session.student_id)
        if student:
            try:
                send_feedback_request(
                    student_email=student.email,
                    student_name=student.name,
                    tutor_name=current_user.name,
                    session_data=session.to_dict()
                )
            except Exception as e:
                print(f"Error sending feedback request email: {e}")

    return jsonify({"success": True, "note": new_note.to_dict()}), 201


@session_bp.route("/api/session-notes/<int:note_id>", methods=["PUT"])
@require_auth
def update_session_note(note_id):
    current_user: User = getattr(request, "db_user", None)
    if not current_user or current_user.role != "tutor":
        return jsonify({"error": "Forbidden"}), 403

    note = SessionNote.query.get(note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404

    if note.tutor_id != current_user.id:
        return jsonify({"error": "You can only update your own notes"}), 403

    data = request.get_json()

    if "attendance_status" in data:
        note.attendance_status = data["attendance_status"]

    if "notes" in data:
        note.notes = data["notes"]

    if "student_feedback" in data:
        note.student_feedback = data["student_feedback"]

    db.session.commit()

    return jsonify({"success": True, "note": note.to_dict()})


@session_bp.route("/api/sessions/<int:session_id>/note", methods=["GET"])
@require_auth
def get_session_note(session_id):
    current_user: User = getattr(request, "db_user", None)
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    note = SessionNote.query.filter_by(session_id=session_id).first()

    if not note:
        return jsonify({"success": True, "note": None})

    return jsonify({"success": True, "note": note.to_dict()})


@session_bp.route("/api/feedback", methods=["POST"])
@require_auth
def submit_feedback():
    current_user: User = getattr(request, "db_user", None)
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    session_id = data.get("session_id")
    rating = data.get("rating")
    comment = data.get("comment")

    if not session_id or not rating:
        return jsonify({"error": "session_id and rating are required"}), 400

    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    if session.student_id != current_user.id:
        return jsonify({"error": "You can only submit feedback for your own sessions"}), 403

    existing_feedback = Feedback.query.filter_by(
        session_id=session_id, student_id=current_user.id
    ).first()

    if existing_feedback:
        existing_feedback.rating = rating
        existing_feedback.comment = comment
        db.session.commit()
        return jsonify({"success": True, "feedback": existing_feedback.to_dict()})

    new_feedback = Feedback(
        session_id=session_id,
        student_id=current_user.id,
        rating=rating,
        comment=comment
    )
    db.session.add(new_feedback)
    db.session.commit()

    return jsonify({"success": True, "feedback": new_feedback.to_dict()}), 201


@session_bp.route("/api/sessions/<int:session_id>/feedback", methods=["GET"])
@require_auth
def get_session_feedback(session_id):
    current_user: User = getattr(request, "db_user", None)
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    feedback = Feedback.query.filter_by(session_id=session_id).first()

    if not feedback:
        return jsonify({"success": True, "feedback": None})

    return jsonify({"success": True, "feedback": feedback.to_dict()})


@session_bp.route("/api/professor/sessions", methods=["GET"])
@require_auth
def professor_get_all_sessions():
    current_user: User = getattr(request, 'db_user', None)
    if not current_user or current_user.role != 'professor':
        return jsonify({"error": "Forbidden"}), 403

    sessions = Session.query.options(
        joinedload(Session.tutor_user),
        joinedload(Session.student_user)
    ).order_by(Session.start_time.desc()).all()
    
    session_ids = [s.id for s in sessions]
    notes = SessionNote.query.filter(SessionNote.session_id.in_(session_ids)).all() if session_ids else []
    notes_map = {n.session_id: n for n in notes}
    feedbacks = Feedback.query.filter(Feedback.session_id.in_(session_ids)).all() if session_ids else []
    feedback_map = {f.session_id: f for f in feedbacks}
    
    sessions_data = []
    for session in sessions:
        session_dict = session.to_dict()
        
        if session.tutor_user:
            session_dict['tutor_name'] = session.tutor_user.name
        
        if session.student_user:
            session_dict['student_name'] = session.student_user.name
        
        note = notes_map.get(session.id)
        session_dict['note'] = note.to_dict() if note else None
        
        feedback = feedback_map.get(session.id)
        session_dict['feedback'] = feedback.to_dict() if feedback else None
        
        sessions_data.append(session_dict)
    
    return jsonify({"success": True, "sessions": sessions_data})


@session_bp.route("/api/professor/dashboard", methods=["GET"])
@require_auth
def professor_get_dashboard():
    current_user: User = getattr(request, 'db_user', None)
    if not current_user or current_user.role != 'professor':
        return jsonify({"error": "Forbidden"}), 403

    class_filter = request.args.get('class')
    tutor_filter = request.args.get('tutor')

    query = Session.query.options(
        joinedload(Session.student_user),
        joinedload(Session.tutor_user)
    ).filter(Session.status == 'booked')
    
    if class_filter:
        query = query.filter(Session.course == class_filter)
    if tutor_filter:
        query = query.filter(Session.tutor_id == int(tutor_filter))
    
    sessions = query.all()
    
    session_ids = [s.id for s in sessions]
    feedbacks = Feedback.query.filter(Feedback.session_id.in_(session_ids)).all() if session_ids else []
    feedback_map = {f.session_id: f for f in feedbacks}
    notes = SessionNote.query.filter(SessionNote.session_id.in_(session_ids)).all() if session_ids else []
    notes_map = {n.session_id: n for n in notes}

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
    active_students = len(unique_students)
    
    ratings = []
    for session in sessions:
        feedback = feedback_map.get(session.id)
        if feedback and feedback.rating:
            ratings.append(feedback.rating)
    
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
    
    def get_week_number(date):
        return date.isocalendar()[1]
    
    from datetime import datetime as dt, timedelta
    now = dt.utcnow()
    
    weekly_data = []
    for i in range(5, -1, -1):
        week_date = now - timedelta(days=i * 7)
        week_num = get_week_number(week_date)
        
        week_sessions = [s for s in sessions if s.start_time and get_week_number(s.start_time) == week_num]
        week_hours = sum([(s.end_time - s.start_time).total_seconds() / 3600 
                         for s in week_sessions if s.start_time and s.end_time])
        
        weekly_data.append({
            'week': f'Week {week_num}',
            'sessions': len(week_sessions),
            'hours': round(week_hours, 1)
        })
    
    monthly_attendance = []
    for i in range(5, -1, -1):
        month_date = dt(now.year, now.month, 1) - timedelta(days=i * 30)
        month = month_date.month
        year = month_date.year
        month_label = month_date.strftime('%b')
        
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
            'month': month_label,
            'rate': attendance_rate
        })
    
    course_distribution = {}
    for session in sessions:
        if session.course:
            course_distribution[session.course] = course_distribution.get(session.course, 0) + 1
    
    student_counts = {}
    for session in sessions:
        if session.student_user and session.student_user.name:
            name = session.student_user.name
            student_counts[name] = student_counts.get(name, 0) + 1
    
    top_students = [{'name': name, 'count': count} 
                   for name, count in sorted(student_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    all_sessions = Session.query.options(
        joinedload(Session.tutor_user)
    ).filter(Session.status == 'booked').all()
    
    unique_classes = set()
    for s in all_sessions:
        if s.course:
            unique_classes.add(s.course)
    
    unique_tutors = {}
    for s in all_sessions:
        if s.tutor_id and s.tutor_user:
            unique_tutors[s.tutor_id] = s.tutor_user.name
    
    return jsonify({
        "success": True,
        "stats": {
            "total_sessions": total_sessions,
            "total_hours": round(total_hours, 1),
            "active_students": active_students,
            "avg_rating": avg_rating
        },
        "weekly_data": weekly_data,
        "monthly_attendance": monthly_attendance,
        "course_distribution": course_distribution,
        "top_students": top_students,
        "filters": {
            "classes": sorted(list(unique_classes)),
            "tutors": [{"id": tid, "name": name} for tid, name in sorted(unique_tutors.items(), key=lambda x: x[1])]
        }
    })


@session_bp.route("/api/tutor/dashboard", methods=["GET"])
@require_auth
def tutor_get_dashboard():
    route_start = time.time()
    print(f"[TIMING] /api/tutor/dashboard - Route started")
    
    current_user: User = getattr(request, 'db_user', None)
    if not current_user or current_user.role != 'tutor':
        return jsonify({"error": "Forbidden"}), 403

    query_start = time.time()
    sessions = Session.query.options(
        joinedload(Session.student_user)
    ).filter(
        Session.tutor_id == current_user.id,
        Session.status == 'booked'
    ).all()
    print(f"[TIMING] /api/tutor/dashboard - Session query (with eager load): {(time.time() - query_start)*1000:.2f}ms ({len(sessions)} sessions)")

    session_ids = [s.id for s in sessions]
    
    batch_start = time.time()
    feedbacks = Feedback.query.filter(Feedback.session_id.in_(session_ids)).all() if session_ids else []
    feedback_map = {f.session_id: f for f in feedbacks}
    notes = SessionNote.query.filter(SessionNote.session_id.in_(session_ids)).all() if session_ids else []
    notes_map = {n.session_id: n for n in notes}
    print(f"[TIMING] /api/tutor/dashboard - Batch queries (Feedback + Notes): {(time.time() - batch_start)*1000:.2f}ms (2 queries)")

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
    active_students = len(unique_students)
    
    ratings = []
    for session in sessions:
        feedback = feedback_map.get(session.id)
        if feedback and feedback.rating:
            ratings.append(feedback.rating)
    
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
    
    def get_week_number(date):
        return date.isocalendar()[1]
    
    from datetime import datetime as dt, timedelta
    now = dt.utcnow()
    
    weekly_data = []
    for i in range(5, -1, -1):
        week_date = now - timedelta(days=i * 7)
        week_num = get_week_number(week_date)
        
        week_sessions = [s for s in sessions if s.start_time and get_week_number(s.start_time) == week_num]
        week_hours = sum([(s.end_time - s.start_time).total_seconds() / 3600 
                         for s in week_sessions if s.start_time and s.end_time])
        
        weekly_data.append({
            'week': f'Week {week_num}',
            'sessions': len(week_sessions),
            'hours': round(week_hours, 1)
        })
    
    monthly_attendance = []
    for i in range(5, -1, -1):
        month_date = dt(now.year, now.month, 1) - timedelta(days=i * 30)
        month = month_date.month
        year = month_date.year
        month_label = month_date.strftime('%b')
        
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
            'month': month_label,
            'rate': attendance_rate
        })
    
    course_distribution = {}
    for session in sessions:
        if session.course:
            course_distribution[session.course] = course_distribution.get(session.course, 0) + 1
    
    student_counts = {}
    for session in sessions:
        if session.student_user and session.student_user.name:
            name = session.student_user.name
            student_counts[name] = student_counts.get(name, 0) + 1
    
    top_students = [{'name': name, 'count': count} 
                   for name, count in sorted(student_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

    print(f"[TIMING] /api/tutor/dashboard - Total route time: {(time.time() - route_start)*1000:.2f}ms")
    return jsonify({
        "success": True,
        "stats": {
            "total_sessions": total_sessions,
            "total_hours": round(total_hours, 1),
            "active_students": active_students,
            "avg_rating": avg_rating
        },
        "weekly_data": weekly_data,
        "monthly_attendance": monthly_attendance,
        "course_distribution": course_distribution,
        "top_students": top_students
    })

