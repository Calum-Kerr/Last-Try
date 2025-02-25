from typing import Dict, Any, Literal
from ..utils.font_mapping import get_font_variant

FontStyleType = Literal['normal', 'italic', 'oblique']

def extract_font_style(span: Dict[str, Any]) -> str:
    """Extract font style from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    # Check italic flag (1) in font flags
    flags = span.get("flags", 0)
    if flags & 1:
        return "font-style: italic;"
        
    # Check font name for style indicators
    if "font" in span:
        font_name = span["font"].lower()
        if "italic" in font_name:
            return "font-style: italic;"
        elif "oblique" in font_name:
            return "font-style: oblique;"
    
    return "font-style: normal;"

def apply_font_style(html_fragment: str, style: FontStyleType) -> str:
    """Apply font style during HTML generation"""
    if style == "normal":
        return html_fragment
    return f'<span style="font-style: {style};">{html_fragment}</span>'

def reinsert_font_style(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply font style during PDF writing"""
    if "font-style" in style_dict:
        style = style_dict["font-style"]
        
        # Update font flags
        flags = span.get("flags", 0)
        if style in ["italic", "oblique"]:
            flags |= 1  # Set italic flag
        else:
            flags &= ~1  # Clear italic flag
        span["flags"] = flags
        
        # Update font name to use appropriate variant
        if "font" in span:
            current_font = span["font"]
            is_bold = bool(flags & 16)  # Check if bold
            new_font = get_font_variant(
                current_font,
                bold=is_bold,
                italic=(style in ["italic", "oblique"])
            )
            span["font"] = new_font
            
        # Store style for future reference
        span["font_style"] = style
    
    return span

def get_available_font_styles() -> list[FontStyleType]:
    """Get list of available font styles"""
    return ['normal', 'italic', 'oblique']

def is_italic_compatible(font_name: str) -> bool:
    """Check if a font supports italic/oblique style"""
    # This is a simplified check - in practice, you'd want to check
    # actual font metadata or maintain a database of font capabilities
    font_lower = font_name.lower()
    return not any(x in font_lower for x in ['symbol', 'zapf', 'dingbats'])