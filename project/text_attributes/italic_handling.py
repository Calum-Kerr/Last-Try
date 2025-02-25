from typing import Dict, Any, Literal
from ..utils.font_mapping import get_font_variant

FontStyle = Literal['normal', 'italic']

def extract_italic(span: Dict[str, Any]) -> str:
    """Extract italic formatting from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    # Check italic flag (1) in font flags
    flags = span.get("flags", 0)
    if flags & 1:
        return "font-style: italic;"
        
    # Check font name for italic indicators
    if "font" in span:
        font_name = span["font"].lower()
        if any(x in font_name for x in ['italic', 'oblique']):
            return "font-style: italic;"
    
    return "font-style: normal;"

def apply_italic(html_fragment: str, use_italic: bool) -> str:
    """Apply italic formatting during HTML generation"""
    if not use_italic:
        return html_fragment
    return f'<span style="font-style: italic;">{html_fragment}</span>'

def reinsert_italic(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply italic formatting during PDF writing"""
    if "font-style" in style_dict:
        is_italic = style_dict["font-style"] == "italic"
        
        # Set italic flag
        flags = span.get("flags", 0)
        if is_italic:
            flags |= 1  # Set italic flag
        else:
            flags &= ~1  # Clear italic flag
        span["flags"] = flags
        
        # Update font name to use italic variant
        if "font" in span:
            current_font = span["font"]
            is_bold = bool(flags & 16)  # Check if bold
            new_font = get_font_variant(
                current_font,
                bold=is_bold,
                italic=is_italic
            )
            span["font"] = new_font
            
        # Add slight rotation for italic appearance if needed
        if is_italic and not any(x in span.get("font", "").lower() for x in ['italic', 'oblique']):
            # Apply 12-degree slant transformation
            span["matrix"] = [1, 0, 0.2679, 1, 0, 0]  # tan(12°) ≈ 0.2679
    
    return span

def get_available_styles() -> list[FontStyle]:
    """Get list of available font styles"""
    return ['normal', 'italic']