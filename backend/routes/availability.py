from flask import Blueprint, jsonify, request
from models import db, Availability, Tutor, User
from auth import require_auth
from datetime import datetime
from sqlalchemy.orm import joinedload

availability_bp = Blueprint("availability", __name__)


@availability_bp.route("/api/availability", methods=["POST"])
@require_auth
def create_availability():
    data = request.get_json()
    db_user = request.db_user
    
    if db_user.role != "tutor":
        return jsonify({"error": "Forbidden"}), 403

    tutor = Tutor.query.filter_by(user_id=db_user.id).first()
    if not tutor:
        tutor = Tutor(user_id=db_user.id)
        db.session.add(tutor)
        db.session.flush()

    day_of_week = data.get("day_of_week")
    start_time_str = data.get("start_time")
    end_time_str = data.get("end_time")
    session_type = data.get("session_type")
    is_recurring = data.get("is_recurring", True)

    if day_of_week is None or not start_time_str or not end_time_str or not session_type:
        return jsonify({"error": "day_of_week, start_time, end_time, and session_type are required"}), 400

    if session_type not in ["online", "in-person"]:
        return jsonify({"error": "session_type must be 'online' or 'in-person'"}), 400

    try:
        start_time = datetime.fromisoformat(start_time_str)
        end_time = datetime.fromisoformat(end_time_str)
    except ValueError:
        return jsonify({"error": "Invalid datetime format"}), 400

    availability = Availability(
        tutor_id=tutor.id,
        day_of_week=day_of_week,
        start_time=start_time,
        end_time=end_time,
        session_type=session_type,
        is_recurring=is_recurring,
    )

    db.session.add(availability)
    db.session.commit()

    return jsonify({"success": True, "availability": availability.to_dict()}), 201


@availability_bp.route("/api/availability", methods=["GET"])
@require_auth
def get_availability():
    tutor_id = request.args.get("tutor_id")
    user_id = request.args.get("user_id")

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

    return jsonify({"success": True, "availabilities": [av.to_dict() for av in availabilities]})


@availability_bp.route("/api/availability/all", methods=["GET"])
@require_auth
def get_all_availability():
    availabilities = Availability.query.options(
        joinedload(Availability.tutor).joinedload(Tutor.user)
    ).all()
    
    result = []
    for av in availabilities:
        av_dict = av.to_dict()
        if av.tutor and av.tutor.user:
            av_dict['tutor_user_id'] = av.tutor.user_id
            av_dict['tutor_name'] = av.tutor.user.name
            av_dict['tutor_email'] = av.tutor.user.email
        result.append(av_dict)
    
    return jsonify({"success": True, "availabilities": result})


@availability_bp.route("/api/availability/<int:availability_id>", methods=["PUT"])
@require_auth
def update_availability(availability_id):
    availability = Availability.query.get(availability_id)
    if not availability:
        return jsonify({"error": "Availability not found"}), 404

    data = request.get_json()

    if "day_of_week" in data:
        availability.day_of_week = data["day_of_week"]
    if "session_type" in data:
        if data["session_type"] not in ["online", "in-person"]:
            return jsonify({"error": "session_type must be 'online' or 'in-person'"}), 400
        availability.session_type = data["session_type"]
    if "is_recurring" in data:
        availability.is_recurring = data["is_recurring"]

    if "start_time" in data or "end_time" in data:
        try:
            if "start_time" in data:
                availability.start_time = datetime.fromisoformat(data["start_time"])
            if "end_time" in data:
                availability.end_time = datetime.fromisoformat(data["end_time"])
        except ValueError:
            return jsonify({"error": "Invalid datetime format"}), 400

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
