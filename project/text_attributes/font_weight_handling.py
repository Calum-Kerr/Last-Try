from typing import Dict, Any, Union, Literal
from ..utils.font_mapping import get_font_variant
import re

# Common font weight names and their numeric values
WEIGHT_MAP = {
    'thin': 100,
    'extra-light': 200,
    'light': 300,
    'normal': 400,
    'regular': 400,
    'medium': 500,
    'semi-bold': 600,
    'bold': 700,
    'extra-bold': 800,
    'black': 900
}

WeightType = Literal['thin', 'extra-light', 'light', 'normal', 'medium', 'semi-bold', 'bold', 'extra-bold', 'black']

def extract_font_weight(span: Dict[str, Any]) -> str:
    """Extract font weight from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    # Check bold flag (16) in font flags
    flags = span.get("flags", 0)
    if flags & 16:
        return "font-weight: bold;"
        
    # Check font name for weight indicators
    if "font" in span:
        font_name = span["font"].lower()
        for weight_name, _ in WEIGHT_MAP.items():
            if weight_name in font_name:
                return f"font-weight: {weight_name};"
    
    return "font-weight: normal;"

def normalize_font_weight(weight: Union[str, int]) -> int:
    """Convert font weight to standard numeric value"""
    if isinstance(weight, int):
        return max(1, min(1000, weight))
    
    # Handle numeric strings
    if weight.isdigit():
        return normalize_font_weight(int(weight))
    
    # Handle named weights
    weight_lower = weight.lower()
    if weight_lower in WEIGHT_MAP:
        return WEIGHT_MAP[weight_lower]
    
    # Default to normal weight
    return 400

def get_closest_weight_name(numeric_weight: int) -> WeightType:
    """Get the closest standard weight name for a numeric weight"""
    min_diff = float('inf')
    closest = 'normal'
    
    for name, value in WEIGHT_MAP.items():
        diff = abs(value - numeric_weight)
        if diff < min_diff:
            min_diff = diff
            closest = name
            
    return closest

def apply_font_weight(html_fragment: str, weight: Union[str, int]) -> str:
    """Apply font weight during HTML generation"""
    normalized = normalize_font_weight(weight)
    return f'<span style="font-weight: {normalized};">{html_fragment}</span>'

def reinsert_font_weight(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply font weight during PDF writing"""
    if "font-weight" in style_dict:
        weight = normalize_font_weight(style_dict["font-weight"])
        
        # Set appropriate flags
        flags = span.get("flags", 0)
        if weight >= 700:  # Bold threshold
            flags |= 16  # Set bold flag
        else:
            flags &= ~16  # Clear bold flag
        span["flags"] = flags
        
        # Update font name to use appropriate variant
        if "font" in span:
            current_font = span["font"]
            is_italic = bool(flags & 1)  # Check if italic
            new_font = get_font_variant(
                current_font,
                bold=(weight >= 700),
                italic=is_italic
            )
            span["font"] = new_font
            
        # Store numeric weight for reference
        span["weight"] = weight
        
        # Adjust stroke width based on weight
        if weight > 400:
            base_size = span.get("size", 12)
            weight_factor = (weight - 400) / 500  # 0.0 to 1.0
            stroke_width = base_size * 0.05 * weight_factor
            span["stroke_width"] = stroke_width
    
    return span

def get_available_weights() -> Dict[str, int]:
    """Get dictionary of available font weights"""
    return WEIGHT_MAP

def calculate_weight_metrics(base_size: float, weight: Union[str, int]) -> Dict[str, float]:
    """Calculate metrics for font weight rendering"""
    numeric_weight = normalize_font_weight(weight)
    weight_factor = (numeric_weight - 400) / 500  # Normalized factor (-0.6 to 1.0)
    
    return {
        'stroke_width': max(0, base_size * 0.05 * weight_factor),
        'contrast': 1.0 + (0.2 * weight_factor),  # Adjust contrast based on weight
        'letter_spacing': -0.02 * weight_factor,  # Slightly tighter for heavier weights
        'baseline_offset': 0.02 * weight_factor  # Slight baseline adjustment
    }