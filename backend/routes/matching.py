from flask import Blueprint, jsonify, request
from models import User
from auth import require_auth
from services.matching_service import get_recommended_tutors, calculate_tutor_match_scores

matching_bp = Blueprint("matching", __name__)


@matching_bp.route("/api/matching/recommend", methods=["GET"])
@require_auth
def recommend_tutors():
    current_user: User = request.db_user
    
    if current_user.role != "student":
        return jsonify({"error": "Only students can get tutor recommendations"}), 403
    
    preferred_day = request.args.get("day")
    preferred_time = request.args.get("time")
    preferred_session_type = request.args.get("session_type")
    limit = request.args.get("limit", 5, type=int)
    
    if preferred_day is not None:
        try:
            preferred_day = int(preferred_day)
        except ValueError:
            return jsonify({"error": "day must be an integer (0-6)"}), 400
    
    if preferred_session_type and preferred_session_type not in ["online", "in-person"]:
        return jsonify({"error": "session_type must be 'online' or 'in-person'"}), 400
    
    recommendations = get_recommended_tutors(
        student_id=current_user.id,
        preferred_day=preferred_day,
        preferred_time=preferred_time,
        preferred_session_type=preferred_session_type,
        limit=limit
    )
    
    return jsonify({
        "success": True,
        "recommendations": recommendations,
        "filters_applied": {
            "preferred_day": preferred_day,
            "preferred_time": preferred_time,
            "preferred_session_type": preferred_session_type
        }
    })


@matching_bp.route("/api/matching/scores", methods=["GET"])
@require_auth
def get_all_tutor_scores():
    current_user: User = request.db_user
    
    if current_user.role != "student":
        return jsonify({"error": "Only students can get tutor scores"}), 403
    
    preferred_day = request.args.get("day")
    preferred_time = request.args.get("time")
    preferred_session_type = request.args.get("session_type")
    
    if preferred_day is not None:
        try:
            preferred_day = int(preferred_day)
        except ValueError:
            return jsonify({"error": "day must be an integer (0-6)"}), 400
    
    scores = calculate_tutor_match_scores(
        student_id=current_user.id,
        preferred_day=preferred_day,
        preferred_time=preferred_time,
        preferred_session_type=preferred_session_type
    )
    
    return jsonify({
        "success": True,
        "tutor_scores": scores
    })

