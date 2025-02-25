from typing import Dict, Any, Literal, Union
import re

JustifyMode = Literal['none', 'auto', 'inter-word', 'inter-character']

def extract_text_justify(block: Dict[str, Any]) -> str:
    """Extract text justification settings from PyMuPDF block data"""
    if not isinstance(block, dict):
        return ""
        
    # Check for explicit justify settings
    if "justify" in block:
        return f"text-justify: {block['justify']};"
        
    # Try to detect justification from text properties
    if "lines" in block and block["lines"]:
        # Check word spacing consistency
        spaces = []
        for line in block["lines"]:
            if "spans" in line and len(line["spans"]) > 1:
                for i in range(len(line["spans"]) - 1):
                    if "bbox" in line["spans"][i] and "bbox" in line["spans"][i + 1]:
                        space = line["spans"][i + 1]["bbox"].x0 - line["spans"][i]["bbox"].x1
                        spaces.append(space)
                        
        if spaces:
            variance = max(spaces) - min(spaces)
            mean_space = sum(spaces) / len(spaces)
            
            if variance > mean_space * 0.5:
                # Significant variance in spacing suggests justification
                if any(s > mean_space * 2 for s in spaces):
                    return "text-justify: inter-word;"
                else:
                    return "text-justify: inter-character;"
    
    return "text-justify: auto;"

def apply_text_justify(html_fragment: str, mode: JustifyMode) -> str:
    """Apply text justification during HTML generation"""
    if mode == "none":
        return html_fragment
    return f'<div style="text-justify: {mode};">{html_fragment}</div>'

def reinsert_text_justify(pdf_writer: Any, block: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply text justification during PDF writing"""
    if "text-justify" in style_dict and "lines" in block:
        justify_mode = style_dict["text-justify"]
        block["justify"] = justify_mode
        
        if justify_mode in ["inter-word", "inter-character"]:
            # Get block boundaries
            if not block.get("bbox"):
                return block
                
            block_width = block["bbox"].width
            
            for line in block["lines"]:
                if "spans" in line and len(line["spans"]) > 1:
                    line_width = sum(span["bbox"].width for span in line["spans"] 
                                   if "bbox" in span)
                    extra_space = block_width - line_width
                    
                    if extra_space <= 0:
                        continue
                        
                    if justify_mode == "inter-word":
                        # Distribute space between words
                        word_gaps = len(line["spans"]) - 1
                        space_per_gap = extra_space / word_gaps
                        
                        # Adjust word positions
                        x_pos = line["bbox"].x0
                        for span in line["spans"]:
                            if "bbox" in span:
                                span["bbox"].x0 = x_pos
                                span["bbox"].x1 = x_pos + span["bbox"].width
                                x_pos += span["bbox"].width + space_per_gap
                                
                    else:  # inter-character
                        # Distribute space between all characters
                        total_chars = sum(len(span.get("text", "")) for span in line["spans"])
                        if total_chars > 1:
                            space_per_char = extra_space / (total_chars - 1)
                            
                            # Adjust character positions within spans
                            x_pos = line["bbox"].x0
                            for span in line["spans"]:
                                if "text" in span and "bbox" in span:
                                    chars = []
                                    for char in span["text"]:
                                        char_width = pdf_writer.get_text_width(char)
                                        chars.append({
                                            "c": char,
                                            "bbox": type("Rect", (), {
                                                "x0": x_pos,
                                                "x1": x_pos + char_width,
                                                "y0": span["bbox"].y0,
                                                "y1": span["bbox"].y1
                                            })
                                        })
                                        x_pos += char_width + space_per_char
                                    span["chars"] = chars
                                    
        # Store justification settings
        block["justify_settings"] = {
            "mode": justify_mode,
            "applied": True
        }
    
    return block

def get_available_modes() -> list[JustifyMode]:
    """Get list of available justification modes"""
    return ['none', 'auto', 'inter-word', 'inter-character']

def calculate_justify_metrics(text_block: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate metrics for text justification"""
    metrics = {
        'word_count': 0,
        'char_count': 0,
        'avg_word_length': 0,
        'line_fill_ratio': 0,
        'recommendations': {}
    }
    
    if "lines" in text_block and text_block["lines"]:
        words = []
        chars = 0
        total_width = 0
        block_width = text_block["bbox"].width if "bbox" in text_block else 0
        
        for line in text_block["lines"]:
            if "spans" in line:
                for span in line["spans"]:
                    if "text" in span:
                        text = span["text"].strip()
                        words.extend(text.split())
                        chars += len(text)
                    if "bbox" in span:
                        total_width += span["bbox"].width
                        
        metrics.update({
            'word_count': len(words),
            'char_count': chars,
            'avg_word_length': chars / len(words) if words else 0,
            'line_fill_ratio': total_width / (block_width * len(text_block["lines"]))
                if block_width and text_block["lines"] else 0
        })
        
        # Generate recommendations
        metrics['recommendations'] = {
            'inter-word': metrics['avg_word_length'] > 5 and metrics['line_fill_ratio'] > 0.8,
            'inter-character': (metrics['avg_word_length'] < 5 or 
                              any(len(w) > 12 for w in words)),
            'none': metrics['word_count'] < 5 or metrics['line_fill_ratio'] < 0.5
        }
    
    return metrics