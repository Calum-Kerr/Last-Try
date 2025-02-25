from flask import Blueprint, request, render_template, jsonify, current_app
from project.utils.session_manager import pdf_session_manager
from project.utils.pdf_metadata import PDFTextProperties
import fitz

edit_bp = Blueprint('edit', __name__)

@edit_bp.route('/edit/<session_id>', methods=['GET'])
def edit_pdf(session_id):
    """Render PDF editor interface"""
    session = pdf_session_manager.get_session(session_id)
    if not session:
        return "Session not found", 404
        
    # Load PDF and extract initial text properties
    doc = fitz.open(session["path"])
    page = doc[0]  # Start with first page
    
    # Extract text blocks with properties
    blocks = []
    for block in page.get_text("dict")["blocks"]:
        if "lines" in block:
            text_props = PDFTextProperties.get_text_span_properties(block)
            block_props = PDFTextProperties.extract_block_properties(block)
            blocks.append({
                "content": block,
                "text_properties": text_props,
                "block_properties": block_props
            })
    
    doc.close()
    
    return render_template(
        'edit.html',
        session_id=session_id,
        blocks=blocks
    )

@edit_bp.route('/api/apply_style', methods=['POST'])
def apply_style():
    """Apply text styling changes"""
    data = request.json
    session_id = data.get('session_id')
    changes = data.get('changes', [])
    
    if not session_id or not changes:
        return jsonify({"error": "Missing required parameters"}), 400
        
    # Apply changes through session manager
    success = pdf_session_manager.update_session(session_id, changes)
    
    return jsonify({
        "success": success,
        "message": "Changes applied successfully" if success else "Failed to apply changes"
    })

@edit_bp.route('/api/text_properties', methods=['POST'])
def get_text_properties():
    """Get text properties for selected text"""
    data = request.json
    session_id = data.get('session_id')
    selection = data.get('selection', {})
    
    if not session_id or not selection:
        return jsonify({"error": "Missing required parameters"}), 400
        
    session = pdf_session_manager.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    # Extract properties for selected text
    doc = fitz.open(session["path"])
    page = doc[selection.get('page', 0)]
    
    properties = {}
    for block in page.get_text("dict")["blocks"]:
        if block.get("number") == selection.get("block"):
            text_props = PDFTextProperties.get_text_span_properties(block)
            block_props = PDFTextProperties.extract_block_properties(block)
            properties = {**text_props, **block_props}
            break
            
    doc.close()
    
    return jsonify(properties)

@edit_bp.route('/api/save', methods=['POST'])
def save_changes():
    """Save all changes to PDF"""
    data = request.json
    session_id = data.get('session_id')
    output_path = data.get('output_path')
    
    if not session_id or not output_path:
        return jsonify({"error": "Missing required parameters"}), 400
        
    # Save final PDF
    success = pdf_session_manager.save_final_pdf(session_id, output_path)
    
    return jsonify({
        "success": success,
        "message": "PDF saved successfully" if success else "Failed to save PDF"
    })

@edit_bp.route('/api/revert', methods=['POST'])
def revert_changes():
    """Revert changes in current session"""
    data = request.json
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({"error": "Missing session ID"}), 400
        
    # Close current session and create new one from original
    session = pdf_session_manager.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    original_path = session["original_path"]
    pdf_session_manager.close_session(session_id)
    new_session_id = pdf_session_manager.create_session(original_path)
    
    return jsonify({
        "success": True,
        "new_session_id": new_session_id
    })