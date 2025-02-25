from typing import Dict, Any, Literal, Union
from ..utils.font_mapping import get_font_metrics

UnderlineStyle = Literal['solid', 'dotted', 'dashed', 'double', 'wavy']
UnderlineColor = Union[str, tuple[int, int, int]]

def extract_underline(span: Dict[str, Any]) -> str:
    """Extract underline formatting from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    # Check underline flag (4) in font flags
    flags = span.get("flags", 0)
    if flags & 4:
        style = span.get("underline_style", "solid")
        color = span.get("underline_color", None)
        
        if color:
            return f"text-decoration: underline {style} rgb{color};"
        return f"text-decoration: underline {style};"
    
    return ""

def apply_underline(
    html_fragment: str,
    style: UnderlineStyle = "solid",
    color: UnderlineColor = None
) -> str:
    """Apply underline formatting during HTML generation"""
    if color:
        color_str = f"rgb{color}" if isinstance(color, tuple) else color
        return f'<span style="text-decoration: underline {style} {color_str};">{html_fragment}</span>'
    return f'<span style="text-decoration: underline {style};">{html_fragment}</span>'

def reinsert_underline(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply underline formatting during PDF writing"""
    if "text-decoration" in style_dict:
        decoration = style_dict["text-decoration"]
        if "underline" in decoration:
            # Set underline flag
            flags = span.get("flags", 0)
            flags |= 4  # Set underline flag
            span["flags"] = flags
            
            # Parse style and color
            parts = decoration.split()
            style = parts[1] if len(parts) > 1 else "solid"
            color = None
            if len(parts) > 2:
                color = parts[2:]
                
            # Store underline properties
            span["underline_style"] = style
            if color:
                span["underline_color"] = color
                
            # Calculate underline position and thickness
            font_size = span.get("size", 12)
            metrics = get_font_metrics(span.get("font", "helvetica"))
            
            position = font_size * metrics["underline_position"]
            thickness = font_size * metrics["underline_thickness"]
            
            if style == "double":
                # Adjust for double underline
                span["underline_positions"] = [position, position - thickness * 3]
                span["underline_thickness"] = thickness
            elif style in ["dotted", "dashed"]:
                # Configure dash pattern
                if style == "dotted":
                    span["underline_dash"] = [thickness, thickness * 2]
                else:
                    span["underline_dash"] = [thickness * 3, thickness * 2]
                span["underline_position"] = position
                span["underline_thickness"] = thickness
            elif style == "wavy":
                # Configure wave parameters
                span["underline_wave"] = {
                    "amplitude": thickness * 2,
                    "length": font_size * 0.4,
                    "position": position
                }
            else:
                # Standard solid underline
                span["underline_position"] = position
                span["underline_thickness"] = thickness
    
    return span

def get_available_styles() -> list[UnderlineStyle]:
    """Get list of available underline styles"""
    return ['solid', 'dotted', 'dashed', 'double', 'wavy']

def calculate_underline_metrics(font_size: float, style: UnderlineStyle) -> Dict[str, float]:
    """Calculate metrics for underline rendering"""
    base_thickness = max(0.5, font_size * 0.05)  # Minimum 0.5pt
    base_position = -font_size * 0.15  # 15% below baseline
    
    metrics = {
        'thickness': base_thickness,
        'position': base_position,
        'gap': base_thickness * 2  # Gap for dotted/dashed styles
    }
    
    if style == "double":
        metrics.update({
            'gap_between_lines': base_thickness * 2,
            'second_position': base_position - base_thickness * 3
        })
    elif style == "wavy":
        metrics.update({
            'wave_amplitude': base_thickness * 2,
            'wave_length': font_size * 0.4
        })
        
    return metrics