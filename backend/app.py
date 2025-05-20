import os
import sys
import logging

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from flask import Flask
from flask_cors import CORS
from backend.routes.data import data_bp
from backend.routes.analysis import analysis_bp

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
    
    # Configure file upload settings
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Register blueprints
    app.register_blueprint(data_bp)
    app.register_blueprint(analysis_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000) 