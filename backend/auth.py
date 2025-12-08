from functools import wraps
from flask import request, jsonify
import os
import requests
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from models import User


def _extract_email(payload):
    if not payload:
        return ""
    email = (payload.get("email") or "").strip()
    if email:
        return email
    email_addresses = payload.get("email_addresses") or []
    primary_id = payload.get("primary_email_address_id")
    if primary_id:
        for entry in email_addresses:
            if entry.get("id") == primary_id:
                email_address = (entry.get("email_address") or "").strip()
                if email_address:
                    return email_address
    for entry in email_addresses:
        email_address = (entry.get("email_address") or "").strip()
        if email_address:
            return email_address
    return ""


def _extract_display_name(payload, fallback_email=""):
    if not payload:
        return fallback_email or ""
    name = (payload.get("name") or "").strip()
    if name:
        return name
    first = (payload.get("first_name") or "").strip()
    last = (payload.get("last_name") or "").strip()
    if first or last:
        return f"{first} {last}".strip()
    username = (payload.get("username") or "").strip()
    if username:
        return username
    email = fallback_email or (payload.get("email") or "").strip()
    if email:
        return email.split("@")[0]
    return fallback_email or ""


def fetch_clerk_user(user_id):
    secret = os.environ.get("CLERK_SECRET_KEY")
    if not secret or not user_id:
        return None
    resp = requests.get(
        f"https://api.clerk.dev/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        sdk = Clerk(bearer_auth=os.environ.get("CLERK_SECRET_KEY"))

        try:
            try:
                request_state = sdk.authenticate_request(request)
            except Exception:
                authorized_party = os.environ.get("AUTHORIZED_PARTY")
                options = AuthenticateRequestOptions(authorized_parties=[authorized_party])
                request_state = sdk.authenticate_request(request, options)

            if not request_state.is_signed_in:
                return jsonify({"error": "Unauthorized"}), 401

            clerk_user_id = request_state.payload.get("sub")
            clerk_user_data = fetch_clerk_user(clerk_user_id)

            merged_payload = dict(request_state.payload)
            if clerk_user_data:
                for key in ["first_name", "last_name", "primary_email_address_id", "email_addresses"]:
                    merged_payload.setdefault(key, clerk_user_data.get(key))
                merged_payload.setdefault("name", clerk_user_data.get("full_name"))
                merged_payload.setdefault("email", _extract_email(clerk_user_data))

            email = _extract_email(merged_payload)
            name = _extract_display_name(merged_payload, email)

            db_user = User.get_or_create_from_clerk(clerk_user_id, name, email)
            request.db_user = db_user
            request.clerk_user = request_state.payload

            return f(*args, **kwargs)
        except Exception:
            return jsonify({"error": "Unauthorized"}), 401

    return decorated_function
