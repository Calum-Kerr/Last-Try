from typing import Dict, Any, Optional
import fitz  # PyMuPDF
import os
import tempfile
import uuid
from datetime import datetime, timedelta

class PDFSessionManager:
    """Manage PDF documents and their editing state in the session"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.cleanup_interval = timedelta(hours=1)
        
    def create_session(self, pdf_path: str) -> str:
        """Create a new editing session for a PDF document"""
        session_id = str(uuid.uuid4())
        temp_path = os.path.join(self.temp_dir, f"{session_id}.pdf")
        
        # Copy PDF to temporary location
        doc = fitz.open(pdf_path)
        doc.save(temp_path)
        doc.close()
        
        self.sessions[session_id] = {
            "path": temp_path,
            "original_path": pdf_path,
            "created": datetime.now(),
            "last_modified": datetime.now(),
            "changes": [],  # Track editing operations
            "metadata": {}  # Store extracted metadata
        }
        
        return session_id
        
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information by ID"""
        return self.sessions.get(session_id)
        
    def update_session(self, session_id: str, changes: list) -> bool:
        """Update session with new changes"""
        if session_id not in self.sessions:
            return False
            
        session = self.sessions[session_id]
        session["changes"].extend(changes)
        session["last_modified"] = datetime.now()
        
        # Apply changes to temporary PDF
        doc = fitz.open(session["path"])
        try:
            for change in changes:
                if change["type"] == "text_style":
                    self._apply_text_style(doc, change)
                elif change["type"] == "text_content":
                    self._apply_text_content(doc, change)
            doc.save(session["path"])
            return True
        except Exception as e:
            print(f"Error applying changes: {str(e)}")
            return False
        finally:
            doc.close()
            
    def _apply_text_style(self, doc: fitz.Document, change: Dict[str, Any]):
        """Apply text styling changes to PDF"""
        page = doc[change["page"]]
        for span in change.get("spans", []):
            # Apply text styling attributes
            if "font" in span:
                page.insert_font(span["font"])
            if "text_style" in span:
                style = span["text_style"]
                page.insert_text(
                    point=(span["x"], span["y"]),
                    text=span["text"],
                    fontsize=style.get("size", 12),
                    fontname=style.get("font", "helv"),
                    color=style.get("color", (0, 0, 0))
                )
                
    def _apply_text_content(self, doc: fitz.Document, change: Dict[str, Any]):
        """Apply text content changes to PDF"""
        page = doc[change["page"]]
        if "remove" in change:
            # Handle text removal
            page.add_redact_annot(change["remove"]["rect"])
            page.apply_redactions()
        if "insert" in change:
            # Handle text insertion
            insert = change["insert"]
            page.insert_text(
                point=(insert["x"], insert["y"]),
                text=insert["text"],
                fontsize=insert.get("size", 12),
                fontname=insert.get("font", "helv")
            )
            
    def cleanup_old_sessions(self):
        """Remove expired sessions and temporary files"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if now - session["last_modified"] > self.cleanup_interval:
                # Remove temporary file
                try:
                    if os.path.exists(session["path"]):
                        os.remove(session["path"])
                except Exception:
                    pass
                expired_sessions.append(session_id)
                
        # Remove expired sessions from dictionary
        for session_id in expired_sessions:
            self.sessions.pop(session_id, None)
            
    def save_final_pdf(self, session_id: str, output_path: str) -> bool:
        """Save the final edited PDF to the specified location"""
        if session_id not in self.sessions:
            return False
            
        session = self.sessions[session_id]
        try:
            doc = fitz.open(session["path"])
            doc.save(output_path)
            doc.close()
            return True
        except Exception:
            return False
            
    def close_session(self, session_id: str):
        """Close a session and cleanup temporary files"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            try:
                if os.path.exists(session["path"]):
                    os.remove(session["path"])
            except Exception:
                pass
            self.sessions.pop(session_id)
            
# Create global session manager instance
pdf_session_manager = PDFSessionManager()