from flask import Blueprint, jsonify, request
from models import db, Availability, Tutor
from auth import require_auth
from datetime import datetime
from zoneinfo import ZoneInfo

availability_bp = Blueprint("availability", __name__)

NY_TZ = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def parse_client_dt(s: str) -> datetime:
    """Accept ISO from client. If naive, treat as UTC (client already sends in desired timezone). Store UTC."""
    if not s:
        raise ValueError("Missing datetime")
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        # Frontend sends naive time in the timezone they want (NYC), but we treat it as UTC to avoid double conversion
        # When we convert back to NYC for display, it will show the same time
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def to_client_iso(dt: datetime) -> str:
    """Return UTC datetime as ISO string (no timezone conversion - client expects UTC time)."""
    return dt.isoformat() if dt else None


@availability_bp.route("/api/availability", methods=["POST"])
@require_auth
def create_availability():
    data = request.get_json()

    # Create availability for the authenticated tutor user.
    db_user = getattr(request, "db_user", None)
    if not db_user:
        return jsonify({"error": "Unauthorized"}), 401
    if db_user.role != "tutor":
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

    if (
        day_of_week is None
        or not start_time_str
        or not end_time_str
        or not session_type
    ):
        return (
            jsonify(
                {
                    "error": "day_of_week, start_time, end_time, and session_type are required"
                }
            ),
            400,
        )

    if session_type not in ["online", "in-person"]:
        return jsonify({"error": "session_type must be 'online' or 'in-person'"}), 400

    try:
        # Debug: log what we receive
        print(f"Received start_time_str: {start_time_str}")
        print(f"Received end_time_str: {end_time_str}")

        start_time = parse_client_dt(start_time_str)
        end_time = parse_client_dt(end_time_str)

        # Debug: log what we're saving
        print(f"Parsed start_time (UTC): {start_time}")
        print(f"Parsed end_time (UTC): {end_time}")
        print(f"Start time hour (UTC): {start_time.hour}")
        print(f"End time hour (UTC): {end_time.hour}")
    except ValueError as e:
        return jsonify({"error": f"Invalid datetime format: {str(e)}"}), 400

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

    # Convert UTC times to NYC timezone for client
    result = availability.to_dict()
    if result.get("start_time"):
        result["start_time"] = to_client_iso(availability.start_time)
    if result.get("end_time"):
        result["end_time"] = to_client_iso(availability.end_time)

    return jsonify({"success": True, "availability": result}), 201


@availability_bp.route("/api/availability", methods=["GET"])
@require_auth
def get_availability():
    tutor_id = request.args.get("tutor_id")  # legacy: Tutor.id
    user_id = request.args.get("user_id")  # preferred: Users.id

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

    # Convert UTC times to NYC timezone for client
    result = []
    for av in availabilities:
        av_dict = av.to_dict()
        # Convert UTC datetimes to NYC timezone
        if av.start_time:
            av_dict["start_time"] = to_client_iso(av.start_time)
        if av.end_time:
            av_dict["end_time"] = to_client_iso(av.end_time)
        result.append(av_dict)

    return jsonify({"success": True, "availabilities": result})


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
            availability.start_time = parse_client_dt(data["start_time"])
        except ValueError as e:
            return (
                jsonify({"error": f"Invalid datetime format for start_time: {str(e)}"}),
                400,
            )

    if "end_time" in data:
        try:
            availability.end_time = parse_client_dt(data["end_time"])
        except ValueError as e:
            return (
                jsonify({"error": f"Invalid datetime format for end_time: {str(e)}"}),
                400,
            )

    if "session_type" in data:
        if data["session_type"] not in ["online", "in-person"]:
            return (
                jsonify({"error": "session_type must be 'online' or 'in-person'"}),
                400,
            )
        availability.session_type = data["session_type"]

    if "is_recurring" in data:
        availability.is_recurring = data["is_recurring"]

    db.session.commit()

    # Convert UTC times to NYC timezone for client
    result = availability.to_dict()
    if result.get("start_time"):
        result["start_time"] = to_client_iso(availability.start_time)
    if result.get("end_time"):
        result["end_time"] = to_client_iso(availability.end_time)

    return jsonify({"success": True, "availability": result})


@availability_bp.route("/api/availability/<int:availability_id>", methods=["DELETE"])
@require_auth
def delete_availability(availability_id):
    availability = Availability.query.get(availability_id)
    if not availability:
        return jsonify({"error": "Availability not found"}), 404

    db.session.delete(availability)
    db.session.commit()

    return jsonify({"success": True, "message": "Availability deleted"})
