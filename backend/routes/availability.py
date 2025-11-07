from flask import Blueprint, jsonify, request
from models import db, Availability, Tutor
from auth import require_auth
from datetime import datetime

availability_bp = Blueprint('availability', __name__)


@availability_bp.route("/api/availability", methods=["POST"])
@require_auth
def create_availability():
    data = request.get_json()
    
    # Create availability for the authenticated tutor user.
    db_user = getattr(request, 'db_user', None)
    if not db_user:
        return jsonify({"error": "Unauthorized"}), 401
    if db_user.role != 'tutor':
        return jsonify({"error": "Forbidden"}), 403
    
    # Ensure a Tutor profile exists for this user (1:1); create if missing.
    tutor = Tutor.query.filter_by(user_id=db_user.id).first()
    if not tutor:
        tutor = Tutor(user_id=db_user.id)
        db.session.add(tutor)
        db.session.flush()  # obtain tutor.id without committing yet
    
    day_of_week = data.get("day_of_week")
    start_time_str = data.get("start_time")
    end_time_str = data.get("end_time")
    session_type = data.get("session_type")
    is_recurring = data.get("is_recurring", True)
    
    if day_of_week is None or not start_time_str or not end_time_str or not session_type:
        return jsonify({"error": "day_of_week, start_time, end_time, and session_type are required"}), 400
    
    if session_type not in ['online', 'in-person']:
        return jsonify({"error": "session_type must be 'online' or 'in-person'"}), 400
    
    try:
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400
    
    availability = Availability(
        tutor_id=tutor.id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        session_type=session_type,
        is_recurring=is_recurring
    )
    
    db.session.add(availability)
    db.session.commit()
    
    return jsonify({"success": True, "availability": availability.to_dict()}), 201


@availability_bp.route("/api/availability", methods=["GET"])
# @require_auth
def get_availability():
    tutor_id = request.args.get("tutor_id")  # legacy: Tutor.id
    user_id = request.args.get("user_id")    # preferred: Users.id
    
    if user_id:
        tutor = Tutor.query.filter_by(user_id=user_id).first()
        if not tutor:
            return jsonify({"error": "Tutor not found"}), 404
        availabilities = tutor.availabilities.all()
    elif tutor_id:
        tutor = Tutor.query.get(tutor_id)
        if not tutor:
            return jsonify({"error": "Tutor not found"}), 404
        availabilities = tutor.availabilities.all()
    else:
        availabilities = Availability.query.all()
    
    return jsonify({
        "success": True,
        "availabilities": [av.to_dict() for av in availabilities]
    })


@availability_bp.route("/api/availability/<int:availability_id>", methods=["PUT"])
@require_auth
def update_availability(availability_id):
    availability = Availability.query.get(availability_id)
    if not availability:
        return jsonify({"error": "Availability not found"}), 404
    
    data = request.get_json()
    
    if "tutor_id" in data:
        tutor = Tutor.query.get(data["tutor_id"])
        if not tutor:
            return jsonify({"error": "Tutor not found"}), 404
        availability.tutor_id = data["tutor_id"]
    
    if "day_of_week" in data:
        availability.day_of_week = data["day_of_week"]
    
    if "start_time" in data:
        try:
            availability.start_time = datetime.fromisoformat(data["start_time"].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "Invalid datetime format for start_time"}), 400
    
    if "end_time" in data:
        try:
            availability.end_time = datetime.fromisoformat(data["end_time"].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "Invalid datetime format for end_time"}), 400
    
    if "session_type" in data:
        if data["session_type"] not in ['online', 'in-person']:
            return jsonify({"error": "session_type must be 'online' or 'in-person'"}), 400
        availability.session_type = data["session_type"]
    
    if "is_recurring" in data:
        availability.is_recurring = data["is_recurring"]
    
    db.session.commit()
    
    return jsonify({"success": True, "availability": availability.to_dict()})


@availability_bp.route("/api/availability/<int:availability_id>", methods=["DELETE"])
@require_auth
def delete_availability(availability_id):
    availability = Availability.query.get(availability_id)
    if not availability:
        return jsonify({"error": "Availability not found"}), 404
    
    db.session.delete(availability)
    db.session.commit()
    
    return jsonify({"success": True, "message": "Availability deleted"})

