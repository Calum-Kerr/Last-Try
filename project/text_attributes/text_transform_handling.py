from typing import Dict, Any, Literal

TransformType = Literal['none', 'capitalize', 'uppercase', 'lowercase']

def extract_text_transform(span: Dict[str, Any]) -> str:
    """Extract text transform style from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
        
    if "text" in span and "original_text" in span:
        text = span["text"]
        original = span["original_text"]
        
        # Compare current text with original to detect transformation
        if text.isupper() and not original.isupper():
            return "text-transform: uppercase;"
        elif text.islower() and not original.islower():
            return "text-transform: lowercase;"
        elif text.istitle() and not original.istitle():
            return "text-transform: capitalize;"
            
    return "text-transform: none;"

def apply_text_transform(html_fragment: str, transform: TransformType) -> str:
    """Apply text transform during HTML generation"""
    if transform == "none":
        return html_fragment
    return f'<span style="text-transform: {transform};">{html_fragment}</span>'

def reinsert_text_transform(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply text transform during PDF writing"""
    if "text-transform" in style_dict and "text" in span:
        transform = style_dict["text-transform"]
        text = span["text"]
        
        # Store original text before transformation
        span["original_text"] = text
        
        # Apply transformation
        if transform == "uppercase":
            span["text"] = text.upper()
        elif transform == "lowercase":
            span["text"] = text.lower()
        elif transform == "capitalize":
            span["text"] = text.title()
            
        # Update text width if needed
        if "bbox" in span:
            new_width = pdf_writer.get_text_width(span["text"])
            if new_width != pdf_writer.get_text_width(text):
                span["bbox"].width = new_width
                
        # Store transformation type
        span["transform"] = transform
    
    return span

def get_available_transforms() -> list[TransformType]:
    """Get list of available text transform options"""
    return ['none', 'capitalize', 'uppercase', 'lowercase']

def preserve_case_mapping(text: str) -> Dict[str, str]:
    """Create mapping to preserve special case patterns"""
    mapping = {}
    
    # Store patterns for acronyms, initialisms, etc.
    words = text.split()
    for word in words:
        if word.isupper() and len(word) > 1:
            # Likely an acronym
            mapping[word.lower()] = word
        elif any(c.isupper() for c in word[1:]):
            # Contains mid-word capitals (e.g., camelCase)
            mapping[word.lower()] = word
            
    return mapping