from functools import wraps
from flask import request, jsonify
import os
import requests
import time
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from models import db, User


def _extract_email(payload):
    """Resolve best email from Clerk payload."""
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
    """Build the best available display name from Clerk payload."""
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


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "OPTIONS":
            return f(*args, **kwargs)

        auth_start = time.time()
        print(f"[TIMING] Auth - Started for {request.path}")

        sdk = Clerk(bearer_auth=os.environ.get("CLERK_SECRET_KEY"))

        def fetch_clerk_user(user_id):
            secret = os.environ.get("CLERK_SECRET_KEY")
            if not (secret and user_id):
                return None
            try:
                clerk_api_start = time.time()
                resp = requests.get(
                    f"https://api.clerk.dev/v1/users/{user_id}",
                    headers={
                        "Authorization": f"Bearer {secret}",
                        "Content-Type": "application/json",
                    },
                )
                print(f"[TIMING] Auth - Clerk API call: {(time.time() - clerk_api_start)*1000:.2f}ms")
                if resp.status_code == 200:
                    return resp.json()
            except Exception as exc:
                return (
                    jsonify({"error": f"Failed to fetch Clerk user {user_id}: {exc}"}),
                    401,
                )

        try:
            jwt_start = time.time()
            try:
                request_state = sdk.authenticate_request(request)
            except Exception:
                authorized_party = os.environ.get("AUTHORIZED_PARTY")
                options = AuthenticateRequestOptions(
                    authorized_parties=[authorized_party]
                )
                request_state = sdk.authenticate_request(request, options)
            print(f"[TIMING] Auth - JWT verification: {(time.time() - jwt_start)*1000:.2f}ms")

            if not request_state.is_signed_in:
                return jsonify({"error": "Unauthorized"}), 401

            clerk_user_id = request_state.payload.get("sub")
            clerk_user_data = fetch_clerk_user(clerk_user_id)
            merged_payload = dict(request_state.payload)
            if clerk_user_data:
                merged_payload.setdefault(
                    "first_name", clerk_user_data.get("first_name")
                )
                merged_payload.setdefault("last_name", clerk_user_data.get("last_name"))
                merged_payload.setdefault("name", clerk_user_data.get("full_name"))
                merged_payload.setdefault(
                    "primary_email_address_id",
                    clerk_user_data.get("primary_email_address_id"),
                )
                merged_payload.setdefault(
                    "email_addresses", clerk_user_data.get("email_addresses")
                )
                merged_payload.setdefault("email", _extract_email(clerk_user_data))

            email = _extract_email(merged_payload)
            name = _extract_display_name(merged_payload, email)

            db_start = time.time()
            db_user = User.get_or_create_from_clerk(clerk_user_id, name, email)
            print(f"[TIMING] Auth - DB user lookup/create: {(time.time() - db_start)*1000:.2f}ms")
            
            request.db_user = db_user
            request.clerk_user = request_state.payload

            print(f"[TIMING] Auth - Total auth time: {(time.time() - auth_start)*1000:.2f}ms")
            return f(*args, **kwargs)
        except Exception:
            return jsonify({"error": "Unauthorized"}), 401

    return decorated_function
