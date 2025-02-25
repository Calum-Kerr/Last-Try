from typing import Dict, Any, List
from ..utils.font_mapping import (
    normalize_font_name,
    get_similar_fonts,
    CORE_FONTS,
    FONT_FAMILY_MAP
)

def extract_font_family(span: Dict[str, Any]) -> str:
    """Extract font family from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
        
    if "font" in span:
        font_name = normalize_font_name(span["font"])
        # Map to standard font family if possible
        if font_name in FONT_FAMILY_MAP:
            font_name = FONT_FAMILY_MAP[font_name]
        return f"font-family: {font_name};"
    
    return ""

def apply_font_family(html_fragment: str, font_family: str) -> str:
    """Apply font family during HTML generation"""
    # Get fallback fonts
    fallbacks = get_similar_fonts(font_family)
    font_stack = [font_family] + fallbacks
    font_css = ", ".join(f"'{f}'" for f in font_stack)
    
    return f'<span style="font-family: {font_css};">{html_fragment}</span>'

def reinsert_font_family(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply font family during PDF writing"""
    if "font-family" in style_dict:
        font_name = normalize_font_name(style_dict["font-family"])
        
        # Preserve style flags
        flags = span.get("flags", 0)
        is_bold = bool(flags & 16)
        is_italic = bool(flags & 1)
        
        # Map to core font if needed
        if font_name in FONT_FAMILY_MAP:
            base_font = FONT_FAMILY_MAP[font_name]
            font_dict = CORE_FONTS[base_font]
            
            # Select appropriate variant
            if is_bold and is_italic:
                span["font"] = font_dict["bold-italic"]
            elif is_bold:
                span["font"] = font_dict["bold"]
            elif is_italic:
                span["font"] = font_dict["italic"]
            else:
                span["font"] = font_dict["normal"]
        else:
            # Use original font name if not mapped
            span["font"] = font_name
            
        # Store original font family for reference
        span["font_family"] = font_name
    
    return span

def get_available_fonts() -> Dict[str, List[str]]:
    """Get lists of available fonts by category"""
    return {
        'sans-serif': [
            'helvetica',
            'arial',
            'verdana',
            'tahoma',
            'trebuchet',
            'segoe ui'
        ],
        'serif': [
            'times',
            'georgia',
            'palatino',
            'garamond',
            'cambria'
        ],
        'monospace': [
            'courier',
            'consolas',
            'monaco',
            'lucida console'
        ]
    }

def is_font_available(font_name: str) -> bool:
    """Check if a font is available for use"""
    font_name = normalize_font_name(font_name)
    
    # Check if it's a core font or mapped to one
    return (
        font_name in CORE_FONTS or
        font_name in FONT_FAMILY_MAP or
        any(font_name in fonts for fonts in get_available_fonts().values())
    )