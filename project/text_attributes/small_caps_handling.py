from typing import Dict, Any
import string

def extract_small_caps(span: Dict[str, Any]) -> str:
    """Extract small caps formatting from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    # Check small caps flag (64) in font flags
    flags = span.get("flags", 0)
    if flags & 64:
        return "font-variant: small-caps;"
    
    # Check for simulated small caps (mixed font sizes)
    if "chars" in span:
        uppercase_size = None
        lowercase_size = None
        
        for char in span["chars"]:
            if "c" in char and "size" in char:
                if char["c"].isupper():
                    uppercase_size = char["size"]
                elif char["c"].islower():
                    lowercase_size = char["size"]
                    
        if uppercase_size and lowercase_size:
            # If lowercase is ~80% of uppercase size, likely small caps
            if 0.75 <= lowercase_size / uppercase_size <= 0.85:
                return "font-variant: small-caps;"
    
    return ""

def apply_small_caps(html_fragment: str, use_small_caps: bool) -> str:
    """Apply small caps formatting during HTML generation"""
    if not use_small_caps:
        return html_fragment
    return f'<span style="font-variant: small-caps;">{html_fragment}</span>'

def reinsert_small_caps(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply small caps formatting during PDF writing"""
    if "font-variant" in style_dict and style_dict["font-variant"] == "small-caps":
        # Set small caps flag
        flags = span.get("flags", 0)
        flags |= 64  # Set small caps flag
        span["flags"] = flags
        
        # Apply simulated small caps if font doesn't support it
        if "text" in span and not span.get("font", "").lower().endswith("sc"):
            text = span["text"]
            base_size = span.get("size", 12.0)
            
            # Create character-by-character formatting
            chars = []
            for char in text:
                char_data = {
                    "c": char,
                    "flags": flags
                }
                
                if char in string.ascii_lowercase:
                    # Convert to uppercase and reduce size
                    char_data["c"] = char.upper()
                    char_data["size"] = base_size * 0.8
                else:
                    char_data["size"] = base_size
                    
                chars.append(char_data)
                
            span["chars"] = chars
            
        # Store small caps state for future reference
        span["small_caps"] = True
    
    return span

def get_available_variants() -> list[str]:
    """Get list of available font variants"""
    return ['normal', 'small-caps']

def calculate_small_caps_metrics(font_size: float) -> Dict[str, float]:
    """Calculate metrics for small caps rendering"""
    return {
        'uppercase_size': font_size,
        'lowercase_size': font_size * 0.8,
        'letter_spacing': font_size * 0.02,
        'word_spacing': font_size * 0.25
    }