from typing import Dict, Any, Literal
from ..utils.font_mapping import get_font_variant

FontWeight = Literal['normal', 'bold']

def extract_bold(span: Dict[str, Any]) -> str:
    """Extract bold formatting from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    # Check bold flag (16) in font flags
    flags = span.get("flags", 0)
    if flags & 16:
        return "font-weight: bold;"
        
    # Check font name for bold indicators
    if "font" in span:
        font_name = span["font"].lower()
        if any(x in font_name for x in ['bold', 'heavy', 'black']):
            return "font-weight: bold;"
    
    return "font-weight: normal;"

def apply_bold(html_fragment: str, use_bold: bool) -> str:
    """Apply bold formatting during HTML generation"""
    if not use_bold:
        return html_fragment
    return f'<span style="font-weight: bold;">{html_fragment}</span>'

def reinsert_bold(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply bold formatting during PDF writing"""
    if "font-weight" in style_dict:
        is_bold = style_dict["font-weight"] == "bold"
        
        # Set bold flag
        flags = span.get("flags", 0)
        if is_bold:
            flags |= 16  # Set bold flag
        else:
            flags &= ~16  # Clear bold flag
        span["flags"] = flags
        
        # Update font name to use bold variant
        if "font" in span:
            current_font = span["font"]
            is_italic = bool(flags & 1)  # Check if italic
            new_font = get_font_variant(
                current_font,
                bold=is_bold,
                italic=is_italic
            )
            span["font"] = new_font
            
        # Adjust stroke width for bold appearance
        if is_bold:
            span["stroke_width"] = span.get("size", 12) * 0.05  # 5% of font size
    
    return span

def get_available_weights() -> list[FontWeight]:
    """Get list of available font weights"""
    return ['normal', 'bold']