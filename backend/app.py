from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models import db
from auth import require_auth
from routes.availability import availability_bp
from routes.sessions import session_bp
import requests
import os

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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
