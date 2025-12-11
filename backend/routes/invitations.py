from flask import Blueprint, jsonify, request
from models import db, Invitation, User, Tutor
from auth import require_auth
from services.email_service import send_invitation_email
import re

invitations_bp = Blueprint("invitations", __name__)


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


@invitations_bp.route("/api/invitations", methods=["POST"])
@require_auth
def send_invitation():
    current_user: User = request.db_user
    
    if current_user.role != "professor":
        return jsonify({"error": "Forbidden"}), 403
    
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    role = data.get("role", "").strip()
    
    if not email or not role:
        return jsonify({"error": "email and role are required"}), 400
    
    if not validate_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    if role not in ["tutor", "professor"]:
        return jsonify({"error": "role must be 'tutor' or 'professor'"}), 400
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User with this email already exists"}), 409
    
    pending_invitation = Invitation.query.filter_by(
        email=email, 
        status='pending'
    ).first()
    
    if pending_invitation and pending_invitation.is_valid():
        return jsonify({"error": "A pending invitation already exists for this email"}), 409
    
    invitation = Invitation(
        email=email,
        role=role,
        invited_by=current_user.id
    )
    db.session.add(invitation)
    db.session.commit()
    
    success = send_invitation_email(
        email=email,
        role=role,
        token=invitation.token,
        invited_by_name=current_user.name
    )
    
    if not success:
        return jsonify({
            "warning": "Invitation created but email failed to send",
            "invitation": invitation.to_dict()
        }), 201
    
    return jsonify({
        "success": True,
        "invitation": invitation.to_dict()
    }), 201


@invitations_bp.route("/api/invitations", methods=["GET"])
@require_auth
def get_invitations():
    current_user: User = request.db_user
    
    if current_user.role != "professor":
        return jsonify({"error": "Forbidden"}), 403
    
    invitations = Invitation.query.order_by(Invitation.created_at.desc()).all()
    
    invitations_data = []
    for inv in invitations:
        inv_dict = inv.to_dict()
        if inv.inviter:
            inv_dict['invited_by_name'] = inv.inviter.name
        invitations_data.append(inv_dict)
    
    return jsonify({
        "success": True,
        "invitations": invitations_data
    })


@invitations_bp.route("/api/invitations/check/<token>", methods=["GET"])
def check_invitation(token):
    invitation = Invitation.query.filter_by(token=token).first()
    
    if not invitation:
        return jsonify({"error": "Invitation not found"}), 404
    
    if invitation.status == 'accepted':
        return jsonify({"error": "Invitation already accepted"}), 410
    
    if invitation.is_expired():
        return jsonify({"error": "Invitation expired"}), 410
    
    return jsonify({
        "success": True,
        "invitation": {
            "email": invitation.email,
            "role": invitation.role
        }
    })
