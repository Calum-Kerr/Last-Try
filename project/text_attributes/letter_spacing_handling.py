from typing import Dict, Any, Union
import re

def extract_letter_spacing(span: Dict[str, Any]) -> str:
    """Extract letter spacing from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    if "char_spacing" in span:
        spacing = span["char_spacing"]
        if spacing != 0:  # Only include if non-default
            return f"letter-spacing: {spacing}pt;"
    
    # Try to detect spacing from character positions
    if "chars" in span:
        spacings = []
        for i in range(len(span["chars"]) - 1):
            if "bbox" in span["chars"][i] and "bbox" in span["chars"][i + 1]:
                gap = span["chars"][i + 1]["bbox"].x0 - span["chars"][i]["bbox"].x1
                if gap > 0:
                    spacings.append(gap)
                    
        if spacings:
            avg_spacing = sum(spacings) / len(spacings)
            if avg_spacing > 0.1:  # Threshold to ignore minimal spacing
                return f"letter-spacing: {avg_spacing:.2f}pt;"
    
    return ""

def normalize_letter_spacing(spacing: Union[str, float]) -> float:
    """Convert letter spacing to points"""
    if isinstance(spacing, (int, float)):
        return float(spacing)
    
    # Extract numeric value and unit
    match = re.match(r'(-?\d*\.?\d+)\s*(pt|px|em|rem|%)?', spacing)
    if not match:
        return 0.0  # Default spacing
        
    value = float(match.group(1))
    unit = match.group(2) or 'pt'
    
    # Convert to points
    unit_conversions = {
        'pt': 1.0,
        'px': 0.75,   # Approximate: 1px ≈ 0.75pt
        'em': 12.0,   # 1em = 12pt (base size)
        'rem': 12.0,
        '%': 0.12,    # 100% = 12pt
    }
    
    return value * unit_conversions[unit]

def apply_letter_spacing(html_fragment: str, spacing: Union[str, float]) -> str:
    """Apply letter spacing during HTML generation"""
    spacing_pt = normalize_letter_spacing(spacing)
    if spacing_pt != 0:
        return f'<span style="letter-spacing: {spacing_pt}pt;">{html_fragment}</span>'
    return html_fragment

def reinsert_letter_spacing(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply letter spacing during PDF writing"""
    if "letter-spacing" in style_dict:
        spacing = normalize_letter_spacing(style_dict["letter-spacing"])
        span["char_spacing"] = spacing
        
        # Update text positioning if needed
        if "text" in span:
            text = span["text"]
            char_count = len(text) - 1  # Spaces between characters
            total_spacing = char_count * spacing
            
            # Adjust text positioning and dimensions
            if "bbox" in span:
                span["bbox"].width += total_spacing
                
            # Store character count for layout calculations
            span["char_count"] = char_count
            
            # Handle character-level positioning if needed
            if spacing > 0.5:  # Significant spacing
                chars = []
                x_pos = span["bbox"].x0 if "bbox" in span else 0
                
                for char in text:
                    char_width = pdf_writer.get_text_width(char)
                    chars.append({
                        "c": char,
                        "bbox": type("Rect", (), {
                            "x0": x_pos,
                            "x1": x_pos + char_width,
                            "y0": span["bbox"].y0 if "bbox" in span else 0,
                            "y1": span["bbox"].y1 if "bbox" in span else 0
                        })
                    })
                    x_pos += char_width + spacing
                    
                span["chars"] = chars
    
    return span

def calculate_spacing_metrics(font_size: float) -> Dict[str, float]:
    """Calculate metrics for letter spacing"""
    return {
        'default': 0,  # Normal spacing
        'tight': -0.05 * font_size,  # Tighter than normal
        'loose': 0.1 * font_size,    # Looser than normal
        'wide': 0.2 * font_size,     # Wide spacing
        'max_recommended': 0.5 * font_size  # Maximum recommended spacing
    }

def get_common_spacing_values() -> Dict[str, float]:
    """Get common letter spacing presets in points"""
    return {
        'none': 0.0,
        'tight': -0.5,
        'normal': 0.0,
        'loose': 0.5,
        'wide': 1.0,
        'extra-wide': 2.0
    }