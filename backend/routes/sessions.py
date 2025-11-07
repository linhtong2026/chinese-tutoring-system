from flask import Blueprint, jsonify, request
from models import db, Session, User, Availability, Tutor
from auth import require_auth
from datetime import datetime

session_bp = Blueprint('session', __name__)


@session_bp.route("/api/sessions/book", methods=["POST"])
@require_auth
def book_session():
    data = request.get_json() or {}

    # Only students can book
    current_user: User = getattr(request, 'db_user', None)
    if not current_user or current_user.role != 'student':
        return jsonify({"error": "Forbidden"}), 403

    availability_id = data.get("availability_id")
    start_time_str = data.get("start_time")
    end_time_str = data.get("end_time")
    course = data.get("course")

    if not availability_id or not start_time_str or not end_time_str:
        return jsonify({"error": "availability_id, start_time, end_time are required"}), 400

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

    print(f"DEBUG: Booking request received")
    print(f"DEBUG: Availability ID: {availability_id}")
    print(f"DEBUG: Availability is_recurring: {availability.is_recurring}")
    print(f"DEBUG: Availability start_time: {availability.start_time}")
    print(f"DEBUG: Availability end_time: {availability.end_time}")
    print(f"DEBUG: Requested start_time: {start_time}")
    print(f"DEBUG: Requested end_time: {end_time}")

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
        if not (availability.start_time <= start_time and end_time <= availability.end_time):
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
        Session.end_time > start_time
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
        status='booked'
    )
    db.session.add(new_session)

    # For recurring availabilities, don't modify the availability - it represents a weekly pattern
    # For non-recurring (one-time) availabilities, adjust or remove them
    if not availability.is_recurring:
        av_start = availability.start_time
        av_end = availability.end_time

        left_remains = av_start < start_time
        right_remains = end_time < av_end

        if left_remains and right_remains:
            # Split into two availability blocks
            availability.end_time = start_time
            new_av = Availability(
                tutor_id=availability.tutor_id,
                day_of_week=availability.day_of_week,
                start_time=end_time,
                end_time=av_end,
                session_type=availability.session_type,
                is_recurring=availability.is_recurring
            )
            db.session.add(new_av)
        elif left_remains and not right_remains:
            # Keep left part
            availability.end_time = start_time
        elif right_remains and not left_remains:
            # Keep right part
            availability.start_time = end_time
        else:
            # Booking consumed the whole availability
            db.session.delete(availability)

    db.session.commit()
    return jsonify({"session": new_session.to_dict()}), 201


@session_bp.route("/api/tutor/sessions", methods=["GET"])
@require_auth
def tutor_list_sessions():
    current_user: User = getattr(request, 'db_user', None)
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    tutor_id = request.args.get("tutor_id")
    
    if current_user.role == 'tutor':
        q = Session.query.filter(Session.tutor_id == current_user.id)
    elif tutor_id:
        q = Session.query.filter(Session.tutor_id == tutor_id)
    else:
        return jsonify({"error": "tutor_id is required for non-tutor users"}), 400

    statuses = request.args.get("status")
    dt_from = request.args.get("from")
    dt_to = request.args.get("to")

    if statuses:
        allowed = [s.strip() for s in statuses.split(',') if s.strip()]
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

    sessions = q.order_by(Session.start_time.asc()).all()
    return jsonify({"sessions": [s.to_dict() for s in sessions]})


@session_bp.route("/api/student/sessions", methods=["GET"])
@require_auth
def student_my_sessions():
    current_user: User = getattr(request, 'db_user', None)
    if not current_user or current_user.role != 'student':
        return jsonify({"error": "Forbidden"}), 403

    q = Session.query.filter(Session.student_id == current_user.id)
    sessions = q.order_by(Session.start_time.asc()).all()
    return jsonify({"sessions": [s.to_dict() for s in sessions]})


@session_bp.route("/api/sessions", methods=["GET"])
@require_auth
def get_sessions():
    tutor_id = request.args.get("tutor_id")
    student_id = request.args.get("student_id")
    
    query = Session.query
    
    if tutor_id:
        query = query.filter_by(tutor_id=tutor_id)
    if student_id:
        query = query.filter_by(student_id=student_id)
    
    sessions = query.all()
    
    return jsonify({
        "success": True,
        "sessions": [s.to_dict() for s in sessions]
    })


@session_bp.route("/api/sessions/<int:session_id>", methods=["GET"])
@require_auth
def get_session(session_id):
    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify({
        "success": True,
        "session": session.to_dict()
    })


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
    current_user: User = getattr(request, 'db_user', None)
    if not current_user or current_user.role != 'student':
        return jsonify({"error": "Forbidden"}), 403

    session = Session.query.get(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404

    if session.status == 'booked':
        return jsonify({"error": "Session already booked"}), 409

    session.status = 'booked'
    session.student_id = current_user.id
    db.session.commit()

    return jsonify({"success": True, "session": session.to_dict()})

