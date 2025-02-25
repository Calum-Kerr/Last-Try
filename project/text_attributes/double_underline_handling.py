from typing import Dict, Any, Optional

def extract_double_underline(span: Dict[str, Any]) -> str:
    """Extract double underline formatting from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    # Check for double underline annotation or flag combination
    flags = span.get("flags", 0)
    if flags & 4 and span.get("double_underline", False):  # 4 is underline flag
        return "text-decoration-style: double;"
    
    return ""

def apply_double_underline(html_fragment: str, use_double: bool) -> str:
    """Apply double underline formatting during HTML generation"""
    if not use_double:
        return html_fragment
    return f'<span style="text-decoration: underline; text-decoration-style: double;">{html_fragment}</span>'

def reinsert_double_underline(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply double underline formatting during PDF writing"""
    if "text-decoration-style" in style_dict and style_dict["text-decoration-style"] == "double":
        # Set underline flag and double underline property
        span["flags"] = span.get("flags", 0) | 4  # Set underline flag
        span["double_underline"] = True
        
        # Store original text height for line positioning
        if "text" in span and "size" in span:
            text_height = span["size"]
            
            # Calculate positions for both underlines
            span["underline_positions"] = [
                -text_height * 0.1,  # First line slightly below baseline
                -text_height * 0.2   # Second line further below
            ]
            
            # Set line thickness (typically thinner than single underline)
            span["underline_thickness"] = max(0.5, text_height * 0.04)
    
    return span

def calculate_double_underline_metrics(font_size: float) -> Dict[str, float]:
    """Calculate metrics for double underline rendering"""
    return {
        "line_thickness": max(0.5, font_size * 0.04),
        "line_spacing": font_size * 0.1,
        "offset_from_baseline": font_size * 0.1
    }