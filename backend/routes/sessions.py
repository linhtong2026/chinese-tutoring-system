from flask import Blueprint, jsonify, request
from models import db, Session, User
from auth import require_auth
from datetime import datetime

session_bp = Blueprint('session', __name__)


@session_bp.route("/api/sessions", methods=["POST"])
@require_auth
def create_session():
    data = request.get_json()
    
    tutor_id = data.get("tutor_id")
    if not tutor_id:
        return jsonify({"error": "tutor_id is required"}), 400
    
    tutor = User.query.get(tutor_id)
    if not tutor:
        return jsonify({"error": "Tutor not found"}), 404
    
    student_id = data.get("student_id")
    course = data.get("course")
    session_type = data.get("session_type")
    start_time_str = data.get("start_time")
    end_time_str = data.get("end_time")
    status = data.get("status", "available")
    
    if not session_type or not start_time_str or not end_time_str:
        return jsonify({"error": "session_type, start_time, and end_time are required"}), 400
    
    if student_id:
        student = User.query.get(student_id)
        if not student:
            return jsonify({"error": "Student not found"}), 404
    
    try:
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400
    
    if end_time <= start_time:
        return jsonify({"error": "end_time must be after start_time"}), 400
    
    overlapping_session = Session.query.filter(
        Session.tutor_id == tutor_id,
        Session.start_time < end_time,
        Session.end_time > start_time
    ).first()
    
    if overlapping_session:
        return jsonify({
            "error": "Tutor already has a session at this time",
            "conflicting_session_id": overlapping_session.id
        }), 409
    
    session = Session(
        tutor_id=tutor_id,
        student_id=student_id,
        course=course,
        session_type=session_type,
        start_time=start_time,
        end_time=end_time,
        status=status
    )
    
    db.session.add(session)
    db.session.commit()
    
    return jsonify({"success": True, "session": session.to_dict()}), 201


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
            session.start_time = datetime.fromisoformat(data["start_time"].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "Invalid datetime format for start_time"}), 400
    
    if "end_time" in data:
        try:
            session.end_time = datetime.fromisoformat(data["end_time"].replace('Z', '+00:00'))
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

