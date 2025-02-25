from typing import Dict, Any, Literal, Optional

WrapMode = Literal['normal', 'break-word', 'anywhere', 'balance']

def extract_text_wrap(block: Dict[str, Any]) -> str:
    """Extract text wrapping mode from PyMuPDF block data"""
    if not isinstance(block, dict):
        return ""
    
    if "wrap" in block:
        wrap_mode = block["wrap"]
        if isinstance(wrap_mode, str):
            return f"overflow-wrap: {wrap_mode};"
    
    # Try to detect wrap mode from content
    if "lines" in block and len(block["lines"]) > 1:
        # Check if lines are balanced
        line_lengths = [len(line.get("text", "")) for line in block["lines"]]
        if line_lengths:
            avg_length = sum(line_lengths) / len(line_lengths)
            variance = sum((l - avg_length) ** 2 for l in line_lengths) / len(line_lengths)
            
            if variance < 2:  # Low variance indicates balanced wrapping
                return "overflow-wrap: balance;"
    
    return "overflow-wrap: normal;"

def apply_text_wrap(html_fragment: str, mode: WrapMode) -> str:
    """Apply text wrapping during HTML generation"""
    return f'<div style="overflow-wrap: {mode};">{html_fragment}</div>'

def reinsert_text_wrap(pdf_writer: Any, block: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply text wrapping during PDF writing"""
    if "overflow-wrap" in style_dict:
        mode = style_dict["overflow-wrap"]
        block["wrap"] = mode
        
        if "lines" in block:
            text_content = ""
            for line in block["lines"]:
                if "text" in line:
                    text_content += line["text"] + " "
            
            if text_content and "bbox" in block:
                bbox = block["bbox"]
                width = bbox.width
                
                # Apply wrapping based on mode
                if mode == "normal":
                    # Wrap at word boundaries only
                    words = text_content.split()
                    current_line = []
                    current_width = 0
                    
                    for word in words:
                        word_width = pdf_writer.get_text_width(word + " ")
                        if current_width + word_width > width:
                            # Start new line
                            block["lines"].append({
                                "text": " ".join(current_line),
                                "x0": bbox.x0,
                                "width": current_width
                            })
                            current_line = [word]
                            current_width = word_width
                        else:
                            current_line.append(word)
                            current_width += word_width
                            
                elif mode == "break-word":
                    # Allow breaking words if necessary
                    chars = list(text_content)
                    current_line = []
                    current_width = 0
                    
                    for char in chars:
                        char_width = pdf_writer.get_text_width(char)
                        if current_width + char_width > width:
                            block["lines"].append({
                                "text": "".join(current_line),
                                "x0": bbox.x0,
                                "width": current_width
                            })
                            current_line = [char]
                            current_width = char_width
                        else:
                            current_line.append(char)
                            current_width += char_width
                            
                elif mode == "balance":
                    # Try to balance line lengths
                    words = text_content.split()
                    total_width = sum(pdf_writer.get_text_width(word + " ") for word in words)
                    optimal_lines = max(1, round(total_width / width))
                    target_width = total_width / optimal_lines
                    
                    current_line = []
                    current_width = 0
                    
                    for word in words:
                        word_width = pdf_writer.get_text_width(word + " ")
                        if abs(current_width + word_width - target_width) > abs(current_width - target_width):
                            block["lines"].append({
                                "text": " ".join(current_line),
                                "x0": bbox.x0,
                                "width": current_width
                            })
                            current_line = [word]
                            current_width = word_width
                        else:
                            current_line.append(word)
                            current_width += word_width
    
    return block

def get_available_wrap_modes() -> list[WrapMode]:
    """Get list of available text wrap modes"""
    return ['normal', 'break-word', 'anywhere', 'balance']