from typing import Dict, Any, Literal

UnderlineStyle = Literal['dashed', 'dotted', 'wavy']

def extract_dashed_underline(span: Dict[str, Any]) -> str:
    """Extract dashed underline formatting from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    # Check for dashed underline properties
    flags = span.get("flags", 0)
    if flags & 4:  # Basic underline flag
        style = span.get("underline_style", "")
        if style == "dashed":
            return "text-decoration-style: dashed;"
        elif style == "dotted":
            return "text-decoration-style: dotted;"
        elif style == "wavy":
            return "text-decoration-style: wavy;"
    
    return ""

def apply_dashed_underline(html_fragment: str, style: UnderlineStyle) -> str:
    """Apply dashed underline formatting during HTML generation"""
    return f'<span style="text-decoration: underline; text-decoration-style: {style};">{html_fragment}</span>'

def reinsert_dashed_underline(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply dashed underline formatting during PDF writing"""
    if "text-decoration-style" in style_dict:
        style = style_dict["text-decoration-style"]
        if style in ["dashed", "dotted", "wavy"]:
            # Set basic underline flag
            span["flags"] = span.get("flags", 0) | 4
            span["underline_style"] = style
            
            # Calculate metrics based on font size
            if "size" in span:
                font_size = span["size"]
                
                if style == "dashed":
                    # Configure dashed line parameters
                    span["dash_pattern"] = [3 * font_size/12, 2 * font_size/12]  # dash length, gap length
                    span["underline_thickness"] = max(0.5, font_size * 0.04)
                    span["underline_position"] = -font_size * 0.1
                    
                elif style == "dotted":
                    # Configure dotted line parameters
                    span["dash_pattern"] = [font_size/12, 2 * font_size/12]  # dot length, gap length
                    span["underline_thickness"] = max(0.5, font_size * 0.08)  # Thicker for dots
                    span["underline_position"] = -font_size * 0.1
                    
                elif style == "wavy":
                    # Configure wavy line parameters
                    span["wave_amplitude"] = font_size * 0.05
                    span["wave_length"] = font_size * 0.4
                    span["underline_thickness"] = max(0.5, font_size * 0.04)
                    span["underline_position"] = -font_size * 0.15
                    
                # Store the baseline offset for consistent positioning
                span["baseline_offset"] = -font_size * 0.1
    
    return span

def calculate_dash_pattern(font_size: float, style: UnderlineStyle) -> Dict[str, float]:
    """Calculate dash pattern metrics based on font size and style"""
    metrics = {
        "thickness": max(0.5, font_size * 0.04),
        "offset": -font_size * 0.1
    }
    
    if style == "dashed":
        metrics.update({
            "dash_length": 3 * font_size/12,
            "gap_length": 2 * font_size/12
        })
    elif style == "dotted":
        metrics.update({
            "dot_diameter": font_size/12,
            "gap_length": 2 * font_size/12
        })
    elif style == "wavy":
        metrics.update({
            "wave_amplitude": font_size * 0.05,
            "wave_length": font_size * 0.4
        })
    
    return metrics

def get_available_styles() -> list[UnderlineStyle]:
    """Get list of available underline styles"""
    return ['dashed', 'dotted', 'wavy']