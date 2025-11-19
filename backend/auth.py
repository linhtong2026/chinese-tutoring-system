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
            # Parse AUTHORIZED_PARTIES from environment variable
            authorized_parties_str = os.environ.get("AUTHORIZED_PARTIES")

            if authorized_parties_str:
                # Clean up the string - remove brackets, quotes, and whitespace
                authorized_parties_str = authorized_parties_str.strip()
                # Remove surrounding brackets if present (e.g., "['url']" -> "'url'")
                if authorized_parties_str.startswith(
                    "["
                ) and authorized_parties_str.endswith("]"):
                    authorized_parties_str = authorized_parties_str[1:-1].strip()
                # Remove surrounding quotes if present
                if (
                    authorized_parties_str.startswith('"')
                    and authorized_parties_str.endswith('"')
                ) or (
                    authorized_parties_str.startswith("'")
                    and authorized_parties_str.endswith("'")
                ):
                    authorized_parties_str = authorized_parties_str[1:-1].strip()

                # Split by comma and clean each URL
                authorized_parties = [
                    party.strip().strip('"').strip("'")
                    for party in authorized_parties_str.split(",")
                    if party.strip()
                ]

                print(f"Parsed authorized_parties: {authorized_parties}")
                options = AuthenticateRequestOptions(
                    authorized_parties=authorized_parties
                )
                request_state = sdk.authenticate_request(request, options)
            else:
                # No AUTHORIZED_PARTIES set - accept tokens from any origin
                print("No AUTHORIZED_PARTIES set - accepting tokens from any origin")
                request_state = sdk.authenticate_request(request)

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
