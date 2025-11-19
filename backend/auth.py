from functools import wraps
from flask import request, jsonify
import os
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
from models import db, User


def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return f(*args, **kwargs)

        sdk = Clerk(bearer_auth=os.environ.get("CLERK_SECRET_KEY"))

        try:
            options = AuthenticateRequestOptions(
                authorized_parties=os.environ.get("AUTHORIZED_PARTIES")
            )
            request_state = sdk.authenticate_request(request, options)

            if not request_state.is_signed_in:
                return jsonify({"error": "Unauthorized"}), 401

            clerk_user_id = request_state.payload.get("sub")
            name = request_state.payload.get("name", "")
            email = request_state.payload.get("email", "")

            db_user = User.get_or_create_from_clerk(clerk_user_id, name, email)
            request.db_user = db_user
            request.clerk_user = request_state.payload

            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Unauthorized"}), 401

    return decorated_function
