from functools import wraps
from flask import request, jsonify
from jwt import decode, get_unverified_header
from jwt.algorithms import RSAAlgorithm
import requests
import json

CLERK_JWKS_URL = "https://api.clerk.dev/v1/jwks"

def get_clerk_jwks():
    response = requests.get(CLERK_JWKS_URL)
    return response.json()

def verify_clerk_token(token):
    try:
        unverified_header = get_unverified_header(token)
        jwks = get_clerk_jwks()
        
        rsa_key = None
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header["kid"]:
                rsa_key = RSAAlgorithm.from_jwk(json.dumps(key))
                break
        
        if not rsa_key:
            return None
        
        decoded_token = decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_signature": True}
        )
        
        return decoded_token
    except Exception:
        return None

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'No authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        decoded_token = verify_clerk_token(token)
        
        if not decoded_token:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.clerk_user = decoded_token
        return f(*args, **kwargs)
    
    return decorated_function

