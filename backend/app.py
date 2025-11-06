from flask import Flask
from flask_cors import CORS
from config import Config
from models import db

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
db.init_app(app)

@app.route('/api/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

