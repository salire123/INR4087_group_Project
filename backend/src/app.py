from flask import Flask
from routes import *

from utils import *



app = Flask(__name__)
app.config['SECRET_KEY'] = Config.get('SECRET_KEY')
app.config['JWT'] = JWTManager(app.config['SECRET_KEY'])

# Setup logging
with app.app_context():
    setup_logging()

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(post_bp, url_prefix='/posts')
app.register_blueprint(analyze_bp, url_prefix='/analyze')
app.register_blueprint(history_bp, url_prefix='/history')
app.register_blueprint(user_bp, url_prefix='/user')

if __name__ == '__main__':
    app.logger.info("-" * 50)
    app.logger.info("Starting app")
    app.logger.info(f"Starting app on port {Config.get('APP_PORT')}")

    if Config.get('MODE') == 'debug':
        app.logger.info("Running in debug mode")
        app.run(debug=True, host='0.0.0.0', port=Config.get('APP_PORT'))
    else:
        app.logger.info("Running in production mode")
        app.run(debug=False, host='0.0.0.0', port=Config.get('APP_PORT'))