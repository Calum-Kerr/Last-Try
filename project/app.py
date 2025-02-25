from flask import Flask, render_template
import os
from project.routes.upload_route import upload_bp
from project.routes.edit_route import edit_bp
from project.routes.download_route import download_bp
from project.utils.session_manager import pdf_session_manager

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Configure application
    app.config.update(
        UPLOAD_FOLDER=os.path.join(os.path.dirname(__file__), 'uploads'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
        SECRET_KEY=os.urandom(24)
    )
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(upload_bp)
    app.register_blueprint(edit_bp)
    app.register_blueprint(download_bp)
    
    # Setup cleanup task for expired sessions
    @app.before_request
    def cleanup_sessions():
        pdf_session_manager.cleanup_old_sessions()
    
    @app.route('/')
    def index():
        """Render application home page"""
        return render_template('upload.html')
    
    @app.errorhandler(413)
    def too_large(e):
        """Handle file too large error"""
        return "File is too large", 413
        
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors"""
        return render_template('404.html'), 404
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)