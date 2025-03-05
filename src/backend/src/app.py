from flask import Flask
from routes.auth import auth_bp
from routes.post import post_bp
from dotenv import load_dotenv

import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(post_bp, url_prefix='/posts')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)