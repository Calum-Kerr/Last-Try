from typing import Dict, Any, Union
import re

def extract_word_spacing(block: Dict[str, Any]) -> str:
    """Extract word spacing from PyMuPDF block data"""
    if not isinstance(block, dict):
        return ""
        
    if "word_spacing" in block:
        return f"word-spacing: {block['word_spacing']}pt;"
        
    # Try to detect word spacing from spans
    if "lines" in block:
        spaces = []
        for line in block["lines"]:
            if "spans" in line and len(line["spans"]) > 1:
                for i in range(len(line["spans"]) - 1):
                    if "bbox" in line["spans"][i] and "bbox" in line["spans"][i + 1]:
                        space = line["spans"][i + 1]["bbox"].x0 - line["spans"][i]["bbox"].x1
                        if space > 0:
                            spaces.append(space)
                            
        if spaces:
            avg_space = sum(spaces) / len(spaces)
            if avg_space != 0:
                return f"word-spacing: {avg_space:.1f}pt;"
    
    return ""

def normalize_spacing(spacing: Union[str, float]) -> float:
    """Convert word spacing to points"""
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

def apply_word_spacing(html_fragment: str, spacing: Union[str, float]) -> str:
    """Apply word spacing during HTML generation"""
    spacing_pt = normalize_spacing(spacing)
    if spacing_pt != 0:
        return f'<span style="word-spacing: {spacing_pt}pt;">{html_fragment}</span>'
    return html_fragment

def reinsert_word_spacing(pdf_writer: Any, block: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply word spacing during PDF writing"""
    if "word-spacing" in style_dict:
        spacing = normalize_spacing(style_dict["word-spacing"])
        block["word_spacing"] = spacing
        
        # Apply spacing to all lines
        if "lines" in block:
            for line in block["lines"]:
                if "spans" in line and len(line["spans"]) > 1:
                    # Calculate total width adjustment
                    word_count = len(line["spans"]) - 1  # Gaps between words
                    total_spacing = word_count * spacing
                    
                    # Adjust span positions
                    x_pos = line["spans"][0]["bbox"].x0
                    for span in line["spans"]:
                        if "bbox" in span:
                            span["bbox"].x0 = x_pos
                            span["bbox"].x1 = x_pos + span["bbox"].width
                            x_pos += span["bbox"].width + spacing
                            
                    # Update line width
                    if "bbox" in line:
                        line["bbox"].width += total_spacing
                        
        # Store spacing settings
        block["spacing_settings"] = {
            "word_spacing": spacing,
            "applied": True
        }
    
    return block

def get_common_spacings() -> Dict[str, float]:
    """Get dictionary of common word spacing values"""
    return {
        'tight': -0.5,      # Tighter than normal
        'normal': 0.0,      # Default spacing
        'loose': 1.0,       # Slightly loose
        'wide': 2.0,        # Wide spacing
        'extra-wide': 4.0   # Very wide spacing
    }

def calculate_spacing_metrics(block: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate metrics for word spacing"""
    metrics = {
        'avg_word_spacing': 0,
        'min_spacing': 0,
        'max_spacing': 0,
        'spacing_variance': 0,
        'recommendations': {}
    }
    
    if "lines" in block:
        spaces = []
        for line in block["lines"]:
            if "spans" in line and len(line["spans"]) > 1:
                for i in range(len(line["spans"]) - 1):
                    if "bbox" in line["spans"][i] and "bbox" in line["spans"][i + 1]:
                        space = (line["spans"][i + 1]["bbox"].x0 - 
                               line["spans"][i]["bbox"].x1)
                        if space > 0:
                            spaces.append(space)
                            
        if spaces:
            avg_space = sum(spaces) / len(spaces)
            metrics.update({
                'avg_word_spacing': avg_space,
                'min_spacing': min(spaces),
                'max_spacing': max(spaces),
                'spacing_variance': max(spaces) - min(spaces)
            })
            
            # Generate recommendations
            metrics['recommendations'] = {
                'tight': avg_space < 0,
                'normal': -0.1 <= avg_space <= 0.1,
                'loose': 0.1 < avg_space <= 1.0,
                'wide': avg_space > 1.0,
                'justified': metrics['spacing_variance'] > avg_space * 0.5
            }
    
    return metrics