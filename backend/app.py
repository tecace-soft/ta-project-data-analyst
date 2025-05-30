import os
import sys
import logging

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from flask import Flask, send_from_directory, send_file
from flask_cors import CORS
from backend.routes.data import data_bp
from backend.routes.analysis import analysis_bp

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app():
    # Configure Flask to serve static files from React build directory
    # Render root is set to frontend/, so build files are in frontend/build/
    frontend_build_path = os.path.join(project_root, 'frontend', 'build')
    static_folder = os.path.join(frontend_build_path, 'static')
    template_folder = frontend_build_path
    
    app = Flask(__name__, 
                static_folder=static_folder,
                template_folder=template_folder)
    
    # Configure CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})  # Allow all origins for deployment
    
    # Configure file upload settings
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Register API blueprints
    app.register_blueprint(data_bp)
    app.register_blueprint(analysis_bp)
    
    # Frontend routes for serving React app
    @app.route('/static/<path:path>')
    def serve_static(path):
        """Serve static files from React build"""
        static_dir = os.path.join(project_root, 'frontend', 'build', 'static')
        return send_from_directory(static_dir, path)
    
    @app.route('/favicon.ico')
    def serve_favicon():
        """Serve favicon from React build"""
        build_dir = os.path.join(project_root, 'frontend', 'build')
        return send_from_directory(build_dir, 'favicon.ico')
    
    @app.route('/')
    @app.route('/<path:path>')
    def serve_frontend(path=''):
        """Serve React app for all non-API routes"""
        # Check if it's an API route
        if path.startswith('api/'):
            return {'error': 'API endpoint not found'}, 404
        
        # Serve the React app's index.html for all other routes
        build_dir = os.path.join(project_root, 'frontend', 'build')
        index_path = os.path.join(build_dir, 'index.html')
        
        if os.path.exists(index_path):
            return send_file(index_path)
        else:
            # If build doesn't exist, show helpful message
            return '''
            <h1>Frontend not built</h1>
            <p>Build directory not found at: {}</p>
            <p>Render should build from frontend/ directory automatically.</p>
            '''.format(build_dir), 404
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Get port from environment (for deployment), fallback to 5000 for local dev
    port = int(os.environ.get("PORT", 5000))
    
    # Get host from environment or use localhost for local dev
    host = os.environ.get("HOST", "0.0.0.0")
    
    app.run(host=host, port=port, debug=True)