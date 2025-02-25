from typing import Dict, Any, Union
import re

def extract_font_size(span: Dict[str, Any]) -> str:
    """Extract font size from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    if "size" in span:
        return f"font-size: {span['size']}pt;"
    
    return ""

def normalize_font_size(size: Union[str, float]) -> float:
    """Convert various size units to points"""
    if isinstance(size, (int, float)):
        return float(size)
    
    # Extract numeric value and unit
    match = re.match(r'(-?\d*\.?\d+)\s*(pt|px|em|rem|%)?', size)
    if not match:
        return 12.0  # Default size
        
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

def apply_font_size(html_fragment: str, size: Union[str, float]) -> str:
    """Apply font size during HTML generation"""
    size_pt = normalize_font_size(size)
    return f'<span style="font-size: {size_pt}pt;">{html_fragment}</span>'

def reinsert_font_size(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply font size during PDF writing"""
    if "font-size" in style_dict:
        size = normalize_font_size(style_dict["font-size"])
        span["size"] = size
        
        # Update text scaling and positioning
        if "text" in span and "bbox" in span:
            bbox = span["bbox"]
            
            # Calculate new dimensions based on size change
            old_size = span.get("size", 12.0)
            scale_factor = size / old_size
            
            # Update bbox dimensions
            bbox.height *= scale_factor
            
            # Adjust baseline position
            if "baseline" in span:
                span["baseline"] *= scale_factor
                
            # Store original size for reference
            span["original_size"] = old_size
    
    return span

def get_common_sizes() -> list[float]:
    """Get list of common font sizes in points"""
    return [6.0, 8.0, 9.0, 10.0, 11.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 36.0, 48.0, 72.0]

def calculate_size_metrics(size: float) -> Dict[str, float]:
    """Calculate various size-related metrics"""
    return {
        'x_height': size * 0.5,        # Typical x-height
        'cap_height': size * 0.7,      # Typical cap height
        'line_height': size * 1.2,     # Default line height
        'baseline_offset': size * 0.2,  # Distance below baseline
        'spacing': {
            'letter': size * 0.02,     # Default letter spacing
            'word': size * 0.25        # Default word spacing
        }
    }