from flask import Blueprint, jsonify, request
from models import User
from auth import require_auth
from services.matching_service import get_recommended_tutors

matching_bp = Blueprint("matching", __name__)


@matching_bp.route("/api/matching/recommend", methods=["GET"])
@require_auth
def recommend_tutors():
    current_user: User = request.db_user
    
    if current_user.role != "student":
        return jsonify({"error": "Only students can get tutor recommendations"}), 403
    
    recommendations = get_recommended_tutors(student_id=current_user.id)
    
    return jsonify({
        "success": True,
        "recommendations": recommendations
    })

