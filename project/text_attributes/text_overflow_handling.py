from typing import Dict, Any, Literal
import math

OverflowMode = Literal['visible', 'hidden', 'ellipsis', 'clip']

def extract_text_overflow(block: Dict[str, Any]) -> str:
    """Extract text overflow settings from PyMuPDF block data"""
    if not isinstance(block, dict):
        return ""
        
    if "overflow" in block:
        return f"text-overflow: {block['overflow']};"
        
    # Try to detect overflow behavior
    if "lines" in block and "bbox" in block:
        for line in block["lines"]:
            if "bbox" in line:
                if line["bbox"].x1 > block["bbox"].x1:
                    # Text extends beyond container
                    if "spans" in line:
                        last_span = line["spans"][-1]
                        if "text" in last_span and last_span["text"].endswith("..."):
                            return "text-overflow: ellipsis;"
                        return "text-overflow: visible;"
                        
    return "text-overflow: clip;"  # Default

def apply_text_overflow(html_fragment: str, mode: OverflowMode) -> str:
    """Apply text overflow during HTML generation"""
    style = f"text-overflow: {mode};"
    if mode in ['ellipsis', 'clip']:
        style += "overflow: hidden; white-space: nowrap;"
    return f'<div style="{style}">{html_fragment}</div>'

def reinsert_text_overflow(pdf_writer: Any, block: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply text overflow during PDF writing"""
    if "text-overflow" in style_dict and "lines" in block:
        mode = style_dict["text-overflow"]
        block["overflow"] = mode
        
        if mode in ['hidden', 'clip', 'ellipsis']:
            # Get container boundaries
            if not block.get("bbox"):
                return block
                
            max_width = block["bbox"].width
            
            for line in block["lines"]:
                if "bbox" in line and line["bbox"].width > max_width:
                    if mode == "ellipsis" and "spans" in line:
                        # Add ellipsis
                        last_span = line["spans"][-1]
                        if "text" in last_span:
                            # Calculate available space
                            current_width = sum(span["bbox"].width 
                                             for span in line["spans"][:-1])
                            last_width = line["spans"][-1]["bbox"].width
                            ellipsis_width = pdf_writer.get_text_width("...")
                            
                            if current_width + ellipsis_width <= max_width:
                                # Can fit ellipsis with some of last word
                                available = max_width - current_width - ellipsis_width
                                text = last_span["text"]
                                for i in range(len(text)):
                                    if pdf_writer.get_text_width(text[:i]) > available:
                                        last_span["text"] = text[:i-1] + "..."
                                        last_span["bbox"].width = (
                                            pdf_writer.get_text_width(last_span["text"])
                                        )
                                        break
                            else:
                                # Remove last word and add ellipsis
                                line["spans"] = line["spans"][:-1]
                                if line["spans"]:
                                    last_span = line["spans"][-1]
                                    last_span["text"] = last_span["text"] + "..."
                                    last_span["bbox"].width = (
                                        pdf_writer.get_text_width(last_span["text"])
                                    )
                    
                    # Clip or hide overflowing content
                    line["bbox"].width = min(line["bbox"].width, max_width)
                    if "spans" in line:
                        cumulative_width = 0
                        visible_spans = []
                        
                        for span in line["spans"]:
                            if cumulative_width + span["bbox"].width <= max_width:
                                visible_spans.append(span)
                                cumulative_width += span["bbox"].width
                            else:
                                # Partial span visibility
                                if mode == "clip":
                                    remaining = max_width - cumulative_width
                                    if remaining > 0:
                                        span_copy = span.copy()
                                        span_copy["bbox"].width = remaining
                                        visible_spans.append(span_copy)
                                break
                                
                        line["spans"] = visible_spans
        
        # Store overflow settings
        block["overflow_settings"] = {
            "mode": mode,
            "applied": True
        }
    
    return block

def get_available_modes() -> list[OverflowMode]:
    """Get list of available overflow modes"""
    return ['visible', 'hidden', 'ellipsis', 'clip']

def calculate_overflow_metrics(block: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate metrics for text overflow"""
    metrics = {
        'container_width': 0,
        'max_line_width': 0,
        'overflow_count': 0,
        'overflow_percentage': 0,
        'recommendations': {}
    }
    
    if "bbox" in block and "lines" in block:
        container_width = block["bbox"].width
        overflowing_lines = 0
        max_width = 0
        
        for line in block["lines"]:
            if "bbox" in line:
                line_width = line["bbox"].width
                max_width = max(max_width, line_width)
                if line_width > container_width:
                    overflowing_lines += 1
                    
        total_lines = len(block["lines"])
        
        metrics.update({
            'container_width': container_width,
            'max_line_width': max_width,
            'overflow_count': overflowing_lines,
            'overflow_percentage': (overflowing_lines / total_lines * 100 
                                  if total_lines > 0 else 0)
        })
        
        # Generate recommendations
        metrics['recommendations'] = {
            'ellipsis': (metrics['overflow_percentage'] < 20 and 
                        metrics['max_line_width'] <= container_width * 1.2),
            'clip': metrics['overflow_percentage'] < 10,
            'visible': metrics['overflow_percentage'] > 20,
            'needs_resize': metrics['max_line_width'] > container_width * 1.5
        }
    
    return metrics