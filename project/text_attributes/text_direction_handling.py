from typing import Dict, Any, Literal
import math

DirectionMode = Literal['horizontal-tb', 'vertical-rl', 'vertical-lr']
WritingMode = Literal['horizontal-tb', 'vertical-rl', 'vertical-lr']

def extract_text_direction(span: Dict[str, Any]) -> tuple[str, str]:
    """Extract text direction and writing mode from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ("", "")
    
    # Check rotation matrix for text orientation
    if "transform" in span:
        matrix = span["transform"]
        # Calculate rotation angle from matrix
        angle = math.degrees(math.atan2(matrix[1], matrix[0]))
        
        # Normalize angle to 0-360 range
        angle = angle % 360
        
        if -45 <= angle <= 45:
            return ("direction: ltr;", "writing-mode: horizontal-tb;")
        elif 45 < angle <= 135:
            return ("direction: ltr;", "writing-mode: vertical-rl;")
        elif -135 <= angle < -45:
            return ("direction: ltr;", "writing-mode: vertical-lr;")
        else:
            return ("direction: rtl;", "writing-mode: horizontal-tb;")
            
    return ("direction: ltr;", "writing-mode: horizontal-tb;")

def apply_text_direction(html_fragment: str, direction: DirectionMode, writing_mode: WritingMode) -> str:
    """Apply text direction and writing mode during HTML generation"""
    return f'<div style="direction: {direction}; writing-mode: {writing_mode};">{html_fragment}</div>'

def reinsert_text_direction(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply text direction during PDF writing"""
    if "writing-mode" in style_dict:
        mode = style_dict["writing-mode"]
        
        # Calculate transformation matrix based on writing mode
        if mode == "vertical-rl":
            # 90-degree rotation
            span["transform"] = [0, 1, -1, 0, 0, 0]
        elif mode == "vertical-lr":
            # -90-degree rotation
            span["transform"] = [0, -1, 1, 0, 0, 0]
        else:
            # Horizontal (default)
            span["transform"] = [1, 0, 0, 1, 0, 0]
            
        # Adjust text positioning and bounds
        if "bbox" in span:
            bbox = span["bbox"]
            if mode.startswith("vertical"):
                # Swap width and height for vertical text
                original_width = bbox.width
                bbox.width = bbox.height
                bbox.height = original_width
                
                # Adjust position based on writing mode
                if mode == "vertical-rl":
                    bbox.x0 += original_width
                
        # Store writing mode for future reference
        span["writing_mode"] = mode
    
    return span

def calculate_vertical_metrics(text: str, font_size: float) -> Dict[str, float]:
    """Calculate metrics for vertical text layout"""
    char_count = len(text)
    return {
        "total_height": char_count * font_size * 1.2,  # 1.2 for typical line spacing
        "width": font_size,  # Single character width
        "char_spacing": font_size * 0.2  # Space between characters
    }

def get_available_modes() -> Dict[str, list]:
    """Get available text direction and writing modes"""
    return {
        "direction": ["ltr", "rtl"],
        "writing_mode": ["horizontal-tb", "vertical-rl", "vertical-lr"]
    }