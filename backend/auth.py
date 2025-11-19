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

        # Log request details for debugging
        auth_header = request.headers.get("Authorization")
        origin = request.headers.get("Origin")
        print(f"=== AUTH DEBUG ===")
        print(f"Method: {request.method}")
        print(f"Origin: {origin}")
        print(f"Authorization header present: {bool(auth_header)}")
        if auth_header:
            print(f"Authorization header (first 50 chars): {auth_header[:50]}...")
        print(f"All headers: {dict(request.headers)}")

        try:
            # Try without authorized_parties first to see if that's the issue
            # If that doesn't work, we'll add it back
            try:
                # First try without authorized_parties restriction
                print("Attempting authentication without authorized_parties...")
                request_state = sdk.authenticate_request(request)
                print(
                    f"Auth successful without restriction. Signed in: {request_state.is_signed_in}"
                )
            except Exception as e1:
                print(f"Auth failed without restriction: {str(e1)}")
                # If that fails, try with authorized_parties
                print("Attempting authentication with authorized_parties...")
                options = AuthenticateRequestOptions(
                    authorized_parties=[
                        "http://localhost:5173",
                        "https://chinese-tutoring-system-fe-b28d59bea6ca.herokuapp.com",
                        "https://chinese-tutoring-system-fe-b28d59bea6ca.herokuapp.com/",
                    ]
                )
                request_state = sdk.authenticate_request(request, options)
                print(
                    f"Auth successful with restriction. Signed in: {request_state.is_signed_in}"
                )

            if not request_state.is_signed_in:
                print(f"ERROR: User not signed in. Request state: {request_state}")
                return jsonify({"error": "Unauthorized - not signed in"}), 401

            clerk_user_id = request_state.payload.get("sub")
            name = request_state.payload.get("name", "")
            email = request_state.payload.get("email", "")
            print(f"Authentication successful. User ID: {clerk_user_id}")

            db_user = User.get_or_create_from_clerk(clerk_user_id, name, email)
            request.db_user = db_user
            request.clerk_user = request_state.payload

            return f(*args, **kwargs)
        except Exception as e:
            import traceback

            print(f"=== AUTHENTICATION EXCEPTION ===")
            print(f"Error: {str(e)}")
            print(f"Type: {type(e).__name__}")
            print(f"Traceback:")
            print(traceback.format_exc())
            return jsonify({"error": "Unauthorized"}), 401

    return decorated_function
