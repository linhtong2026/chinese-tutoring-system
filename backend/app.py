from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models import db, Tutor
from auth import require_auth
from routes.availability import availability_bp
from routes.sessions import session_bp
import requests
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import and_
from models import db, User, Session, Feedback

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db.init_app(app)

app.register_blueprint(availability_bp)
app.register_blueprint(session_bp)


def update_clerk_metadata(clerk_user_id, metadata):
    secret_key = app.config.get("CLERK_SECRET_KEY")
    if not secret_key:
        return False

    try:
        url = f"https://api.clerk.dev/v1/users/{clerk_user_id}/metadata"
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        }
        response = requests.patch(
            url, json={"public_metadata": metadata}, headers=headers
        )
        return response.status_code == 200
    except Exception:
        return False

NY_TZ = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")

def parse_client_dt(s: str) -> datetime:
    """Accept ISO from client (naive => America/New_York). Store UTC."""
    if not s:
        raise ValueError("Missing datetime")
    dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=NY_TZ)
    return dt.astimezone(UTC)

def to_client_iso(dt: datetime) -> str:
    return dt.astimezone(NY_TZ).isoformat() if dt else None

def role_required(role: str):
    from functools import wraps
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            db_user: User = getattr(request, "db_user", None)
            if not db_user:
                return jsonify({"error": "Unauthorized"}), 401
            if db_user.role != role:
                return jsonify({"error": "Forbidden"}), 403
            return fn(*args, **kwargs)
        return wrapped
    return decorator

def session_to_dict(s: Session, include_people=True):
    data = s.to_dict()
    data["start_time"] = to_client_iso(s.start_time)
    data["end_time"] = to_client_iso(s.end_time)
    if include_people:
        data["tutor"] = {
            "id": s.tutor_id,
            "name": s.tutor_user.name if s.tutor_user else None,
            "email": s.tutor_user.email if s.tutor_user else None,
        }
        data["student"] = (
            {
                "id": s.student_id,
                "name": s.student_user.name if s.student_user else None,
                "email": s.student_user.email if s.student_user else None,
            } if s.student_id else None
        )
    data["booked"] = (s.status == "booked")
    return data

def tutor_overlap_exists(tutor_id: int, start_utc: datetime, end_utc: datetime, exclude_id: int = None) -> bool:
    q = Session.query.filter(
        Session.tutor_id == tutor_id,
        Session.status.in_(["available", "booked"]),
        and_(Session.start_time < end_utc, Session.end_time > start_utc)
    )
    if exclude_id:
        q = q.filter(Session.id != exclude_id)
    return db.session.query(q.exists()).scalar()


@app.route('/api/health')
def health():
    return {'status': 'ok'}

@app.route("/api/health")
def health():
    return {"status": "ok"}


def get_clerk_user_metadata(clerk_user_id):
    """Fetch user metadata from Clerk API"""
    secret_key = app.config.get("CLERK_SECRET_KEY")
    if not secret_key:
        return None

    try:
        url = f"https://api.clerk.dev/v1/users/{clerk_user_id}"
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


@app.route("/api/user")
@require_auth
def get_user():
    db_user = request.db_user
    clerk_user_id = request.clerk_user.get("sub")

    # Sync role from Clerk metadata
    clerk_user = get_clerk_user_metadata(clerk_user_id)
    if clerk_user and "public_metadata" in clerk_user:
        clerk_role = clerk_user["public_metadata"].get("role")
        if clerk_role and clerk_role != db_user.role:
            db_user.role = clerk_role
            db.session.commit()

    return jsonify(
        {"user": db_user.to_dict(), "onboarding_complete": db_user.onboarding_complete}
    )


@app.route("/api/user/onboarding", methods=["POST"])
@require_auth
def complete_onboarding():
    data = request.get_json()
    db_user = request.db_user
    clerk_user_id = request.clerk_user.get("sub")

    language = data.get("language", "en")
    class_name = data.get("class_name")

    db_user.role = "student"
    db_user.class_name = class_name
    db_user.language_preference = language
    db_user.onboarding_complete = True
    db.session.commit()

    update_clerk_metadata(clerk_user_id, {"role": "student"})

    return jsonify({"success": True, "user": db_user.to_dict()})


@app.route("/api/user/profile", methods=["POST"])
@require_auth
def update_profile():
    data = request.get_json()
    db_user = request.db_user

    if "language_preference" in data:
        db_user.language_preference = data["language_preference"]
    if "class_name" in data:
        db_user.class_name = data["class_name"]

    db.session.commit()

    return jsonify({"success": True, "user": db_user.to_dict()})



@app.route("/api/tutor/sessions", methods=["GET"])
@require_auth
@role_required("tutor")
def tutor_list_sessions():
    user: User = request.db_user
    dt_from = request.args.get("from")
    dt_to = request.args.get("to")
    statuses = request.args.get("status")  # e.g. "available,booked"

    q = Session.query.filter(Session.tutor_id == user.id)
    if statuses:
        allowed = [s.strip() for s in statuses.split(",") if s.strip()]
        q = q.filter(Session.status.in_(allowed))
    if dt_from:
        q = q.filter(Session.start_time >= parse_client_dt(dt_from))
    if dt_to:
        q = q.filter(Session.end_time <= parse_client_dt(dt_to))

    sessions = q.order_by(Session.start_time.asc()).all()
    return jsonify({"sessions": [session_to_dict(s) for s in sessions]})

@app.route("/api/tutor/sessions", methods=["POST"])
@require_auth
@role_required("tutor")
def tutor_create_session():
    user: User = request.db_user
    data = request.get_json() or {}
    required = ["start_time", "end_time", "session_type"]
    if any(k not in data for k in required):
        return jsonify({"error": f"Required: {', '.join(required)}"}), 400

    start_utc = parse_client_dt(data["start_time"])
    end_utc = parse_client_dt(data["end_time"])
    if end_utc <= start_utc:
        return jsonify({"error": "end_time must be after start_time"}), 400

    if tutor_overlap_exists(user.id, start_utc, end_utc):
        return jsonify({"error": "Overlaps an existing session"}), 409

    s = Session(
        tutor_id=user.id,
        student_id=None,
        course=data.get("course"),
        session_type=data["session_type"],
        start_time=start_utc,
        end_time=end_utc,
        status="available",
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({"session": session_to_dict(s)}), 201

@app.route("/api/tutor/sessions/<int:session_id>", methods=["PATCH"])
@require_auth
@role_required("tutor")
def tutor_update_session(session_id):
    user: User = request.db_user
    s: Session = Session.query.get(session_id)
    if not s or s.tutor_id != user.id:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json() or {}

    new_start = data.get("start_time")
    new_end = data.get("end_time")
    if new_start or new_end:
        start_utc = parse_client_dt(new_start) if new_start else s.start_time
        end_utc = parse_client_dt(new_end) if new_end else s.end_time
        if end_utc <= start_utc:
            return jsonify({"error": "end_time must be after start_time"}), 400
        if tutor_overlap_exists(user.id, start_utc, end_utc, exclude_id=s.id):
            return jsonify({"error": "Overlaps an existing session"}), 409
        s.start_time = start_utc
        s.end_time = end_utc

    if "course" in data: s.course = data["course"]
    if "session_type" in data: s.session_type = data["session_type"]
    if "status" in data:
        if data["status"] not in ["available", "booked", "completed", "canceled"]:
            return jsonify({"error": "Invalid status"}), 400
        s.status = data["status"]
        if s.status != "booked":
            s.student_id = None  # re-open slot if not booked

    db.session.commit()
    return jsonify({"session": session_to_dict(s)})

@app.route("/api/tutor/sessions/<int:session_id>", methods=["DELETE"])
@require_auth
@role_required("tutor")
def tutor_delete_session(session_id):
    user: User = request.db_user
    s: Session = Session.query.get(session_id)
    if not s or s.tutor_id != user.id:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(s)
    db.session.commit()
    return jsonify({"success": True})

@app.route("/api/student/sessions", methods=["GET"])
@require_auth
@role_required("student")
def student_my_sessions():
    user: User = request.db_user
    now_utc = datetime.now(tz=UTC)
    sessions = (Session.query
        .filter(
            Session.student_id == user.id,
            Session.start_time >= now_utc,
            Session.status.in_(["available", "booked", "completed"])
        )
        .order_by(Session.start_time.asc())
        .all())
    return jsonify({"sessions": [session_to_dict(s) for s in sessions]})

@app.route("/api/sessions/available", methods=["GET"])
@require_auth
def list_available_sessions():
    tutor_ids = request.args.get("tutor_ids")  # "7,9"
    dt_from = request.args.get("from")
    dt_to = request.args.get("to")

    q = Session.query.filter(Session.status == "available")

    if tutor_ids:
        ids = [int(x) for x in tutor_ids.split(",") if x.strip().isdigit()]
        if ids:
            q = q.filter(Session.tutor_id.in_(ids))

    if dt_from:
        q = q.filter(Session.start_time >= parse_client_dt(dt_from))
    if dt_to:
        q = q.filter(Session.end_time <= parse_client_dt(dt_to))

    sessions = q.order_by(Session.start_time.asc()).all()
    return jsonify({"sessions": [session_to_dict(s) for s in sessions]})

@app.route("/api/sessions/book", methods=["POST"])
@require_auth
@role_required("student")
def book_session():
    user: User = request.db_user
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id is required"}), 400

    s: Session = Session.query.get(session_id)
    if not s or s.status != "available":
        return jsonify({"error": "Session not available"}), 409

    s.student_id = user.id
    s.status = "booked"
    db.session.commit()
    return jsonify({"session": session_to_dict(s)})

@app.route("/api/sessions/<int:session_id>", methods=["PATCH"])
@require_auth
@role_required("student")
def student_update_session(session_id):
    user: User = request.db_user
    s: Session = Session.query.get(session_id)
    if not s or s.student_id != user.id:
        return jsonify({"error": "Not found or not yours"}), 404

    data = request.get_json() or {}
    if data.get("action") == "cancel":
        s.student_id = None
        s.status = "available"
        db.session.commit()
        return jsonify({"session": session_to_dict(s)})

    return jsonify({"error": "Unsupported update"}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
