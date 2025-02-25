from flask import Blueprint, request, jsonify, current_app, render_template
from werkzeug.utils import secure_filename
import os
from project.utils.session_manager import pdf_session_manager
from project.processing.ocr_preprocessing import needs_ocr
from project.processing.ocr_execution import OCRProcessor

upload_bp = Blueprint('upload', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    """Check if file has PDF extension"""
    return '.' in filename and filename.lower().endswith('.pdf')

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload"""
    # Check if file was uploaded
    if 'pdf' not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400
        
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Invalid file type"}), 400
        
    try:
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        # Create editing session
        session_id = pdf_session_manager.create_session(upload_path)
        
        # Check if OCR is needed
        if needs_ocr(upload_path):
            # Initialize OCR processor
            ocr = OCRProcessor()
            # Process PDF with OCR
            ocr.process_pdf(upload_path)
        
        return jsonify({
            "success": True,
            "session_id": session_id
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error processing file: {str(e)}"
        }), 500

@upload_bp.route('/', methods=['GET'])
def upload_page():
    """Render upload page"""
    return render_template('upload.html')