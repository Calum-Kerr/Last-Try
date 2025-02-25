from typing import Dict, Optional, List

# Default PDF core fonts
CORE_FONTS = {
    'helvetica': {
        'normal': 'helv',
        'bold': 'helvb',
        'italic': 'helvi',
        'bold-italic': 'helvbi'
    },
    'times': {
        'normal': 'tiro',
        'bold': 'tirob',
        'italic': 'tiroi',
        'bold-italic': 'tirobi'
    },
    'courier': {
        'normal': 'cour',
        'bold': 'courb',
        'italic': 'couri',
        'bold-italic': 'courbi'
    }
}

# Font family mapping
FONT_FAMILY_MAP = {
    # Sans-serif fonts
    'arial': 'helvetica',
    'verdana': 'helvetica',
    'tahoma': 'helvetica',
    'trebuchet': 'helvetica',
    'segoe ui': 'helvetica',
    
    # Serif fonts
    'georgia': 'times',
    'palatino': 'times',
    'garamond': 'times',
    'cambria': 'times',
    
    # Monospace fonts
    'consolas': 'courier',
    'monaco': 'courier',
    'lucida console': 'courier'
}

def get_font_variant(font_name: str, bold: bool = False, italic: bool = False) -> str:
    """Get appropriate font variant based on style flags"""
    # Normalize font name
    font_name = font_name.lower().split('-')[0].strip()
    
    # Map to core font family
    base_font = FONT_FAMILY_MAP.get(font_name, font_name)
    if base_font not in CORE_FONTS:
        base_font = 'helvetica'  # Default to Helvetica
        
    # Determine variant
    style = 'normal'
    if bold and italic:
        style = 'bold-italic'
    elif bold:
        style = 'bold'
    elif italic:
        style = 'italic'
        
    return CORE_FONTS[base_font][style]

def get_similar_fonts(font_name: str) -> List[str]:
    """Get list of similar fonts for fallback"""
    font_name = font_name.lower()
    
    # Group similar fonts
    sans_serif = ['helvetica', 'arial', 'verdana', 'tahoma']
    serif = ['times', 'georgia', 'palatino', 'garamond']
    monospace = ['courier', 'consolas', 'monaco']
    
    if font_name in sans_serif or any(f.startswith(font_name) for f in sans_serif):
        return sans_serif
    elif font_name in serif or any(f.startswith(font_name) for f in serif):
        return serif
    elif font_name in monospace or any(f.startswith(font_name) for f in monospace):
        return monospace
        
    return ['helvetica']  # Default fallback

def normalize_font_name(font_name: str) -> str:
    """Normalize font name to standard format"""
    # Remove common suffixes and normalize spacing
    name = font_name.lower().strip()
    name = name.replace('-', ' ')
    
    # Remove common suffixes
    suffixes = [' mt', ' ms', ' std', ' pro', ' regular']
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            
    return name.strip()

def get_font_metrics(font_name: str) -> Dict[str, float]:
    """Get standard metrics for font"""
    # These are approximate metrics based on common fonts
    metrics = {
        'x_height': 0.5,  # Relative to font size
        'cap_height': 0.7,
        'ascender': 0.8,
        'descender': -0.2,
        'line_gap': 0.2,
        'stem_width': 0.08,
        'underline_position': -0.1,
        'underline_thickness': 0.05
    }
    
    font_name = normalize_font_name(font_name)
    
    # Adjust metrics based on font family
    if font_name in FONT_FAMILY_MAP:
        base_font = FONT_FAMILY_MAP[font_name]
        if base_font == 'times':
            metrics.update({
                'x_height': 0.45,
                'cap_height': 0.65,
                'stem_width': 0.06
            })
        elif base_font == 'courier':
            metrics.update({
                'x_height': 0.52,
                'stem_width': 0.1,
                'line_gap': 0.25
            })
            
    return metrics

def supports_style(font_name: str, style: str) -> bool:
    """Check if font supports specific style"""
    font_name = normalize_font_name(font_name)
    base_font = FONT_FAMILY_MAP.get(font_name, 'helvetica')
    
    # All core fonts support basic styles
    if base_font in CORE_FONTS:
        if style in ['bold', 'italic', 'bold-italic']:
            return True
            
    return False