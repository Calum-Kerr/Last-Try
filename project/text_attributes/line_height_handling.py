from typing import Dict, Any, Union
import re

def extract_line_height(block: Dict[str, Any]) -> str:
    """Extract line height from PyMuPDF block data"""
    if not isinstance(block, dict) or "lines" not in block:
        return ""
    
    lines = block["lines"]
    if len(lines) < 2:
        return ""
        
    # Calculate average line spacing
    spacings = []
    for i in range(len(lines) - 1):
        if "bbox" in lines[i] and "bbox" in lines[i + 1]:
            current_bottom = lines[i]["bbox"].y1
            next_top = lines[i + 1]["bbox"].y0
            spacing = next_top - current_bottom
            if spacing > 0:
                spacings.append(spacing)
    
    if spacings:
        avg_spacing = sum(spacings) / len(spacings)
        # Get reference font size from first line
        if "spans" in lines[0] and lines[0]["spans"]:
            font_size = lines[0]["spans"][0].get("size", 12)
            line_height = avg_spacing / font_size
            return f"line-height: {line_height:.2f};"
    
    return ""

def normalize_line_height(value: Union[str, float]) -> float:
    """Convert line height to normalized value"""
    if isinstance(value, (int, float)):
        return float(value)
    
    # Extract numeric value and unit
    match = re.match(r'(-?\d*\.?\d+)\s*(em|rem|%)?', value)
    if not match:
        return 1.2  # Default multiplier
        
    value = float(match.group(1))
    unit = match.group(2)
    
    # Handle percentage
    if unit == '%':
        return value / 100
    
    return value

def apply_line_height(html_fragment: str, line_height: Union[str, float]) -> str:
    """Apply line height during HTML generation"""
    height = normalize_line_height(line_height)
    return f'<div style="line-height: {height};">{html_fragment}</div>'

def reinsert_line_height(pdf_writer: Any, block: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply line height during PDF writing"""
    if "line-height" in style_dict and "lines" in block:
        height = normalize_line_height(style_dict["line-height"])
        lines = block["lines"]
        
        if lines:
            # Get base font size from first line
            base_size = 12.0
            if "spans" in lines[0] and lines[0]["spans"]:
                base_size = lines[0]["spans"][0].get("size", 12.0)
                
            # Calculate line spacing in points
            spacing = base_size * height
            
            # Adjust line positions
            y_pos = block.get("bbox", None).y0 if block.get("bbox") else 0
            for line in lines:
                if "bbox" in line:
                    # Set line position
                    line["bbox"].y0 = y_pos
                    line["bbox"].y1 = y_pos + base_size
                    
                    # Move to next line position
                    y_pos += spacing
                    
            # Store line height for future reference
            block["line_height"] = height
    
    return block

def calculate_line_metrics(font_size: float, line_height: float) -> Dict[str, float]:
    """Calculate metrics for line spacing"""
    spacing = font_size * line_height
    return {
        'total_height': spacing,
        'text_height': font_size,
        'gap': spacing - font_size,
        'baseline_offset': font_size * 0.2,
        'recommended_spacing': {
            'minimum': font_size * 1.0,  # Single spacing
            'comfortable': font_size * 1.5,  # 1.5 spacing
            'double': font_size * 2.0  # Double spacing
        }
    }

def get_common_line_heights() -> list[float]:
    """Get list of common line height values"""
    return [1.0, 1.2, 1.5, 1.8, 2.0]