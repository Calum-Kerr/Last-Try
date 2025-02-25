from flask import Blueprint, send_file, jsonify, current_app
import os
from project.utils.session_manager import pdf_session_manager

download_bp = Blueprint('download', __name__)

@download_bp.route('/download/<session_id>', methods=['GET'])
def download_pdf(session_id):
    """Download the edited PDF file"""
    session = pdf_session_manager.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    if not os.path.exists(session["path"]):
        return jsonify({"error": "PDF file not found"}), 404
        
    try:
        # Get original filename
        filename = os.path.basename(session["original_path"])
        # Add '_edited' suffix before extension
        base, ext = os.path.splitext(filename)
        new_filename = f"{base}_edited{ext}"
        
        return send_file(
            session["path"],
            as_attachment=True,
            download_name=new_filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({
            "error": "Failed to download file",
            "message": str(e)
        }), 500

@download_bp.route('/preview/<session_id>', methods=['GET'])
def preview_pdf(session_id):
    """Preview the PDF file without downloading"""
    session = pdf_session_manager.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    if not os.path.exists(session["path"]):
        return jsonify({"error": "PDF file not found"}), 404
        
    try:
        return send_file(
            session["path"],
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({
            "error": "Failed to preview file",
            "message": str(e)
        }), 500