from typing import Dict, Any, Literal

SmoothingMode = Literal['auto', 'none', 'antialiased', 'subpixel-antialiased']

def extract_font_smoothing(span: Dict[str, Any]) -> str:
    """Extract font smoothing settings from PyMuPDF span data"""
    if not isinstance(span, dict):
        return ""
    
    # Check for explicit smoothing settings
    if "rendering_mode" in span:
        mode = span["rendering_mode"]
        if mode == 0:  # Fill text
            return "font-smooth: auto;"
        elif mode == 3:  # Fill text and add to path for stroke (smoother)
            return "font-smooth: antialiased;"
        elif mode == 1:  # Stroke text (no smoothing)
            return "font-smooth: none;"
    
    return "font-smooth: auto;"

def apply_font_smoothing(html_fragment: str, mode: SmoothingMode) -> str:
    """Apply font smoothing during HTML generation"""
    css_properties = {
        "auto": "-webkit-font-smoothing: auto; -moz-osx-font-smoothing: auto;",
        "none": "-webkit-font-smoothing: none; -moz-osx-font-smoothing: none;",
        "antialiased": "-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;",
        "subpixel-antialiased": "-webkit-font-smoothing: subpixel-antialiased; -moz-osx-font-smoothing: auto;"
    }
    
    style = css_properties.get(mode, css_properties["auto"])
    return f'<span style="{style}">{html_fragment}</span>'

def reinsert_font_smoothing(pdf_writer: Any, span: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply font smoothing during PDF writing"""
    if "font-smooth" in style_dict:
        mode = style_dict["font-smooth"]
        
        # Map smoothing mode to PyMuPDF rendering mode
        mode_map = {
            "none": 1,      # Stroke text
            "auto": 0,      # Fill text (default)
            "antialiased": 3,  # Fill and stroke
            "subpixel-antialiased": 3  # Fill and stroke (best quality)
        }
        
        rendering_mode = mode_map.get(mode, 0)
        span["rendering_mode"] = rendering_mode
        
        # Adjust other properties for better smoothing
        if mode in ["antialiased", "subpixel-antialiased"]:
            # Increase stroke width slightly for smoother appearance
            span["stroke_width"] = 0.1
            # Add slight stroke adjustment
            span["stroke_adjustment"] = True
    
    return span

def get_available_smoothing_modes() -> list[SmoothingMode]:
    """Get list of available font smoothing modes"""
    return ['auto', 'none', 'antialiased', 'subpixel-antialiased']