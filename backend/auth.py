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
        if request.method == 'OPTIONS':
            print(f"[DEBUG] OPTIONS request, skipping auth")
            return f(*args, **kwargs)
        
        print(f"[DEBUG] require_auth called for {request.path}, method: {request.method}")
        print(f"[DEBUG] Authorization header: {request.headers.get('Authorization', 'NOT FOUND')}")
        
        sdk = Clerk(bearer_auth=os.environ.get('CLERK_SECRET_KEY'))
        print(f"[DEBUG] SDK created, CLERK_SECRET_KEY exists: {bool(os.environ.get('CLERK_SECRET_KEY'))}")
        
        try:
            options = AuthenticateRequestOptions(
                authorized_parties=['http://localhost:5173']
            )
            print(f"[DEBUG] About to call authenticate_request")
            request_state = sdk.authenticate_request(request, options)
            print(f"[DEBUG] authenticate_request completed, is_signed_in: {request_state.is_signed_in}")
            
            if not request_state.is_signed_in:
                print(f"[DEBUG] User not signed in, returning 401")
                return jsonify({'error': 'Unauthorized'}), 401
            
            clerk_user_id = request_state.payload.get('sub')
            name = request_state.payload.get('name', '')
            email = request_state.payload.get('email', '')
            
            db_user = User.get_or_create_from_clerk(clerk_user_id, name, email)
            request.db_user = db_user
            request.clerk_user = request_state.payload
            
            print(f"[DEBUG] Auth successful, calling next decorator/function")
            return f(*args, **kwargs)
        except Exception as e:
            print(f"[DEBUG] Auth error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': 'Unauthorized'}), 401
    
    return decorated_function
