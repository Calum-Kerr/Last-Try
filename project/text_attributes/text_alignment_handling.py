from typing import Dict, Any, Literal

AlignType = Literal['left', 'right', 'center', 'justify']

def extract_text_align(block: Dict[str, Any]) -> str:
    """Extract text alignment from PyMuPDF block data"""
    if not isinstance(block, dict):
        return ""
        
    # Check explicit alignment property
    if "align" in block:
        return f"text-align: {block['align']};"
        
    # Try to detect alignment from text positioning
    if "lines" in block and block["lines"]:
        lines = block["lines"]
        left_edges = []
        right_edges = []
        
        for line in lines:
            if "bbox" in line:
                left_edges.append(line["bbox"].x0)
                right_edges.append(line["bbox"].x1)
                
        if left_edges and right_edges:
            # Calculate variances
            left_variance = max(left_edges) - min(left_edges)
            right_variance = max(right_edges) - min(right_edges)
            
            if left_variance < 1 and right_variance < 1:
                # Both edges aligned - likely justified
                return "text-align: justify;"
            elif left_variance < 1:
                # Left edges aligned
                return "text-align: left;"
            elif right_variance < 1:
                # Right edges aligned
                return "text-align: right;"
            else:
                # Check for center alignment
                centers = [(l + r) / 2 for l, r in zip(left_edges, right_edges)]
                center_variance = max(centers) - min(centers)
                if center_variance < 1:
                    return "text-align: center;"
    
    return "text-align: left;"  # Default alignment

def apply_text_align(html_fragment: str, alignment: AlignType) -> str:
    """Apply text alignment during HTML generation"""
    return f'<div style="text-align: {alignment};">{html_fragment}</div>'

def reinsert_text_align(pdf_writer: Any, block: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply text alignment during PDF writing"""
    if "text-align" in style_dict and "lines" in block:
        alignment = style_dict["text-align"]
        block["align"] = alignment
        
        # Get block boundaries
        if not block.get("bbox"):
            return block
            
        block_width = block["bbox"].width
        
        # Adjust line positions based on alignment
        for line in block["lines"]:
            if "bbox" in line:
                line_width = line["bbox"].width
                
                if alignment == "center":
                    offset = (block_width - line_width) / 2
                    line["bbox"].x0 = block["bbox"].x0 + offset
                elif alignment == "right":
                    offset = block_width - line_width
                    line["bbox"].x0 = block["bbox"].x0 + offset
                elif alignment == "justify" and line_width < block_width * 0.9:
                    # Only justify if line fills less than 90% of block width
                    words = line.get("spans", [])
                    if len(words) > 1:
                        extra_space = block_width - line_width
                        space_per_word = extra_space / (len(words) - 1)
                        
                        # Adjust word positions
                        x_pos = line["bbox"].x0
                        for i, word in enumerate(words):
                            if "bbox" in word:
                                word["bbox"].x0 = x_pos
                                word["bbox"].x1 = x_pos + word["bbox"].width
                                x_pos += word["bbox"].width + space_per_word
                else:  # left alignment
                    line["bbox"].x0 = block["bbox"].x0
                    
        # Store alignment for future reference
        block["text_align"] = alignment
    
    return block

def get_available_alignments() -> list[AlignType]:
    """Get list of available text alignments"""
    return ['left', 'right', 'center', 'justify']

def calculate_alignment_metrics(block_width: float, line_widths: list[float]) -> Dict[str, Any]:
    """Calculate metrics for text alignment"""
    metrics = {
        'block_width': block_width,
        'average_line_width': sum(line_widths) / len(line_widths) if line_widths else 0,
        'max_line_width': max(line_widths) if line_widths else 0,
        'min_line_width': min(line_widths) if line_widths else 0,
        'line_count': len(line_widths),
        'fill_ratios': [w / block_width for w in line_widths] if line_widths else []
    }
    
    # Calculate alignment recommendations
    metrics['recommendations'] = {
        'justify': all(r > 0.7 for r in metrics['fill_ratios']),  # Lines mostly fill width
        'center': metrics['line_count'] < 5,  # Short blocks work well centered
        'right': metrics['average_line_width'] < block_width * 0.5  # Short lines
    }
    
    return metrics