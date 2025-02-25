from typing import Dict, Any, Literal

WhiteSpaceMode = Literal['normal', 'nowrap', 'pre', 'pre-wrap', 'pre-line', 'break-spaces']

def extract_white_space(block: Dict[str, Any]) -> str:
    """Extract white space handling mode from PyMuPDF block data"""
    if not isinstance(block, dict):
        return ""
    
    # Try to detect whitespace mode from block properties
    if "preserve_whitespace" in block and block["preserve_whitespace"]:
        return "white-space: pre;"
    
    if "lines" in block and len(block["lines"]) > 0:
        line = block["lines"][0]
        if "text" in line:
            # Check for preserved spaces at start/end
            if line["text"].startswith(" ") or line["text"].endswith(" "):
                return "white-space: pre-wrap;"
            # Check for multiple consecutive spaces
            if "  " in line["text"]:
                return "white-space: pre;"
    
    return "white-space: normal;"

def apply_white_space(html_fragment: str, mode: WhiteSpaceMode) -> str:
    """Apply white space handling during HTML generation"""
    return f'<div style="white-space: {mode};">{html_fragment}</div>'

def reinsert_white_space(pdf_writer: Any, block: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply white space handling during PDF writing"""
    if "white-space" in style_dict:
        mode = style_dict["white-space"]
        
        # Set whitespace preservation flag
        block["preserve_whitespace"] = mode in ['pre', 'pre-wrap', 'pre-line', 'break-spaces']
        
        # Handle specific modes
        if "lines" in block:
            for line in block["lines"]:
                if "text" in line:
                    text = line["text"]
                    
                    if mode == "normal":
                        # Collapse multiple spaces and trim
                        text = " ".join(text.split())
                    elif mode == "nowrap":
                        # Collapse spaces but don't allow breaks
                        text = " ".join(text.split())
                        line["no_wrap"] = True
                    elif mode in ["pre", "pre-wrap"]:
                        # Preserve all whitespace
                        pass
                    elif mode == "pre-line":
                        # Preserve line breaks but collapse spaces
                        text = " ".join(part.strip() for part in text.split("\n"))
                    
                    line["text"] = text
                    
                    # Handle word wrapping
                    if mode in ["normal", "pre-wrap", "pre-line", "break-spaces"]:
                        line["wrap"] = True
                    else:
                        line["wrap"] = False
    
    return block

def get_available_white_space_modes() -> list[WhiteSpaceMode]:
    """Get list of available white space handling modes"""
    return ['normal', 'nowrap', 'pre', 'pre-wrap', 'pre-line', 'break-spaces']