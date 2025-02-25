from typing import Dict, Any, Union
import re

def extract_text_indent(block: Dict[str, Any]) -> str:
    """Extract text indentation from PyMuPDF block data"""
    if not isinstance(block, dict):
        return ""
        
    # Check for explicit indent settings
    if "indent" in block:
        return f"text-indent: {block['indent']}pt;"
        
    # Try to detect indentation from first line position
    if "lines" in block and block["lines"]:
        first_line = block["lines"][0]
        other_lines = block["lines"][1:]
        
        if "bbox" in first_line and other_lines:
            # Get average starting position of other lines
            other_starts = [line["bbox"].x0 for line in other_lines if "bbox" in line]
            if other_starts:
                avg_start = sum(other_starts) / len(other_starts)
                indent = first_line["bbox"].x0 - avg_start
                
                if abs(indent) > 1:  # More than 1pt difference
                    return f"text-indent: {indent:.1f}pt;"
    
    return ""

def normalize_indent(indent: Union[str, float]) -> float:
    """Convert indent value to points"""
    if isinstance(indent, (int, float)):
        return float(indent)
    
    # Extract numeric value and unit
    match = re.match(r'(-?\d*\.?\d+)\s*(pt|px|em|rem|%)?', indent)
    if not match:
        return 0.0  # Default indent
        
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

def apply_text_indent(html_fragment: str, indent: Union[str, float]) -> str:
    """Apply text indentation during HTML generation"""
    indent_pt = normalize_indent(indent)
    if indent_pt != 0:
        return f'<div style="text-indent: {indent_pt}pt;">{html_fragment}</div>'
    return html_fragment

def reinsert_text_indent(pdf_writer: Any, block: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply text indentation during PDF writing"""
    if "text-indent" in style_dict and "lines" in block:
        indent = normalize_indent(style_dict["text-indent"])
        block["indent"] = indent
        
        if block["lines"]:
            first_line = block["lines"][0]
            if "bbox" in first_line:
                # Apply indent to first line
                first_line["bbox"].x0 += indent
                
                # Handle negative indents (outdents)
                if indent < 0:
                    # Ensure other lines are aligned properly
                    for line in block["lines"][1:]:
                        if "bbox" in line:
                            line["bbox"].x0 = first_line["bbox"].x0 - indent
                            
        # Store indentation settings
        block["indent_settings"] = {
            "value": indent,
            "original_x0": block["lines"][0]["bbox"].x0 if block["lines"] else 0
        }
    
    return block

def get_common_indents() -> Dict[str, float]:
    """Get dictionary of common indentation values"""
    return {
        'none': 0.0,
        'small': 12.0,       # 1em
        'medium': 24.0,      # 2em
        'large': 36.0,       # 3em
        'paragraph': 48.0,   # 4em - standard paragraph indent
        'block': 72.0        # 6em - block quote style
    }

def calculate_indent_metrics(block: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate metrics for text indentation"""
    metrics = {
        'first_line_offset': 0,
        'other_lines_avg_offset': 0,
        'block_width': 0,
        'recommendations': {}
    }
    
    if "lines" in block and block["lines"]:
        first_line = block["lines"][0]
        other_lines = block["lines"][1:]
        
        if "bbox" in first_line:
            metrics['first_line_offset'] = first_line["bbox"].x0
            
            if other_lines:
                other_starts = [line["bbox"].x0 for line in other_lines 
                              if "bbox" in line]
                if other_starts:
                    metrics['other_lines_avg_offset'] = (
                        sum(other_starts) / len(other_starts)
                    )
            
            if "bbox" in block:
                metrics['block_width'] = block["bbox"].width
                
                # Calculate recommendations
                relative_indent = (metrics['first_line_offset'] - 
                                 metrics['other_lines_avg_offset'])
                metrics['recommendations'] = {
                    'paragraph_indent': relative_indent >= 0 and 
                                      relative_indent <= metrics['block_width'] * 0.2,
                    'hanging_indent': relative_indent < 0 and 
                                    abs(relative_indent) <= metrics['block_width'] * 0.1,
                    'block_indent': all(x >= metrics['block_width'] * 0.1 
                                      for x in other_starts)
                }
    
    return metrics