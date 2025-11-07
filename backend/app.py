from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models import db
from auth import require_auth

app = Flask(__name__)
app.config.from_object(Config)

CORS(app, supports_credentials=True, allow_headers=['Content-Type', 'Authorization'])
db.init_app(app)

@app.route('/api/health')
def health():
    return {'status': 'ok'}

@app.route('/api/user')
@require_auth
def get_user():
    user = request.clerk_user
    return jsonify({
        'user_id': user.get('sub'),
        'metadata': user.get('metadata', {})
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

