from typing import Dict, Any, Literal, Union

VerticalAlignType = Literal['baseline', 'sub', 'super', 'text-top', 'text-bottom', 'middle']

def extract_vertical_align(span: Dict[str, Any]) -> str:
    """Extract vertical alignment from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    # Check for subscript/superscript flags
    flags = span.get("flags", 0)
    if flags & 2:  # Superscript flag
        return "vertical-align: super;"
    elif flags & 3:  # Subscript flag
        return "vertical-align: sub;"
        
    # Check vertical position relative to baseline
    if "rise" in span:
        rise = span["rise"]
        if rise > 0:
            return "vertical-align: super;"
        elif rise < 0:
            return "vertical-align: sub;"
            
    return "vertical-align: baseline;"

def apply_vertical_align(html_fragment: str, align_type: VerticalAlignType) -> str:
    """Apply vertical alignment during HTML generation"""
    return f'<span style="vertical-align: {align_type};">{html_fragment}</span>'

def reinsert_vertical_align(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply vertical alignment during PDF writing"""
    if "vertical-align" in style_dict:
        align = style_dict["vertical-align"]
        
        # Reset any existing alignment
        span["flags"] = span.get("flags", 0) & ~(2 | 3)  # Clear super/sub flags
        span["rise"] = 0
        
        # Apply new alignment
        if align == "super":
            span["flags"] |= 2  # Set superscript flag
            span["rise"] = span.get("size", 12) * 0.33  # Rise by 1/3 font size
        elif align == "sub":
            span["flags"] |= 3  # Set subscript flag
            span["rise"] = -span.get("size", 12) * 0.33  # Lower by 1/3 font size
        elif align == "text-top":
            span["rise"] = span.get("size", 12)  # Rise by full font size
        elif align == "text-bottom":
            span["rise"] = -span.get("size", 12)  # Lower by full font size
        elif align == "middle":
            span["rise"] = span.get("size", 12) * 0.5  # Rise by half font size
            
        # Adjust font size for sub/superscript
        if align in ("sub", "super"):
            span["size"] = span.get("size", 12) * 0.75  # Reduce to 75%
            
    return span

def normalize_vertical_align(value: Union[str, float]) -> float:
    """Convert vertical alignment to rise value in points"""
    if isinstance(value, (int, float)):
        return float(value)
        
    align_values = {
        "super": 0.33,    # 1/3 em up
        "sub": -0.33,     # 1/3 em down
        "text-top": 1.0,  # 1em up
        "text-bottom": -1.0,  # 1em down
        "middle": 0.5,    # 1/2 em up
        "baseline": 0.0   # No rise
    }
    
    return align_values.get(value, 0.0)

def get_available_alignments() -> list[VerticalAlignType]:
    """Get list of available vertical alignment options"""
    return ['baseline', 'sub', 'super', 'text-top', 'text-bottom', 'middle']