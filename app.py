from flask import Flask
from flask_cors import CORS
import anvil.server
import os
import sys
from dotenv import load_dotenv
from config import Config
from utils.auth_utils import init_auth

def create_app():

    app = Flask(__name__)
    CORS(app)
    # CORS(app,origins=["http://localhost:5173","productionFrontendSite-Deployed.com"]) # for restrictive permissible domains
    app.config.from_object(Config)
    load_dotenv()
    ANVIL_KEY = os.getenv('ANVIL_UPLINK_KEY')
    if not ANVIL_KEY:
        raise ValueError("ANVIL_UPLINK_KEY environment variable is required")

    # import sys
    if 'gunicorn' not in sys.modules:
        anvil.server.connect(ANVIL_KEY)

    init_auth(app.config['SESSIONS'])

    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.projects import projects_bp
    from blueprints.sponsors import sponsors_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api')
    app.register_blueprint(sponsors_bp, url_prefix='/api/sponsors')
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)