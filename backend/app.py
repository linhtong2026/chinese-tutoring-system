from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models import (
    db,
    User,
    Tutor,
    Session,
    Feedback,
    Availability,
    SessionNote,
)
from auth import require_auth
from routes.availability import availability_bp
from routes.sessions import session_bp
from routes.matching import matching_bp
import requests
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import and_

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db.init_app(app)


# Initialize database tables on startup
def init_db():
    with app.app_context():
        db.create_all()
        from seed_data import seed_database
        seed_database()


# Call init_db when app starts
init_db()

app.register_blueprint(availability_bp)
app.register_blueprint(session_bp)
app.register_blueprint(matching_bp)


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
            }
            if s.student_id
            else None
        )
    data["booked"] = s.status == "booked"
    return data


def tutor_overlap_exists(
    tutor_id: int, start_utc: datetime, end_utc: datetime, exclude_id: int = None
) -> bool:
    q = Session.query.filter(
        Session.tutor_id == tutor_id,
        Session.status.in_(["available", "booked"]),
        and_(Session.start_time < end_utc, Session.end_time > start_utc),
    )
    if exclude_id:
        q = q.filter(Session.id != exclude_id)
    return db.session.query(q.exists()).scalar()


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
            # If role changed to tutor, ensure Tutor record exists
            if clerk_role == "tutor":
                tutor = Tutor.query.filter_by(user_id=db_user.id).first()
                if not tutor:
                    tutor = Tutor(user_id=db_user.id)
                    db.session.add(tutor)
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
    clerk_name = request.clerk_user.get("name", "")
    clerk_email = request.clerk_user.get("email", "")

    language = data.get("language", "en")
    class_name = data.get("class_name")

    if clerk_name:
        db_user.name = clerk_name
    if clerk_email:
        db_user.email = clerk_email
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


@app.route("/api/tutor/by-user/<int:user_id>")
@require_auth
def get_tutor_by_user(user_id):
    """Get or create Tutor record for a user"""
    db_user = request.db_user

    if db_user.id != user_id and db_user.role != "admin":
        return jsonify({"error": "Forbidden"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    tutor = Tutor.query.filter_by(user_id=user_id).first()
    if not tutor:
        if user.role == "tutor":
            tutor = Tutor(user_id=user_id)
            db.session.add(tutor)
            db.session.commit()
        else:
            return jsonify({"error": "User is not a tutor"}), 400

    return jsonify({"tutor": tutor.to_dict()})


@app.route("/api/tutors")
@require_auth
def get_tutors():
    """Get all tutors with their user information"""
    tutors = Tutor.query.all()
    tutors_data = []

    for tutor in tutors:
        tutor_dict = tutor.to_dict()
        if tutor.user:
            tutor_dict["user"] = {
                "id": tutor.user.id,
                "name": tutor.user.name,
                "email": tutor.user.email,
                "class_name": tutor.user.class_name,
            }
        tutors_data.append(tutor_dict)

    return jsonify({"success": True, "tutors": tutors_data})


if __name__ == "__main__":
    app.run(debug=True, port=5001)