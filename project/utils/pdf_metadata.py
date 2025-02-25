from typing import Dict, Any, Optional, List, Tuple
import fitz  # PyMuPDF

class PDFTextProperties:
    """Helper class for extracting and managing PDF text properties"""
    
    @staticmethod
    def get_text_span_properties(span: Dict[str, Any]) -> Dict[str, str]:
        """Extract all text styling properties from a PyMuPDF span"""
        properties = {}
        
        if not isinstance(span, dict):
            return properties
            
        # Font properties
        if "font" in span:
            properties["font-family"] = span["font"].split("-")[0]
            if "bold" in span["font"].lower():
                properties["font-weight"] = "bold"
            if "italic" in span["font"].lower():
                properties["font-style"] = "italic"
                
        # Size and spacing
        if "size" in span:
            properties["font-size"] = f"{span['size']}pt"
        if "character_spacing" in span:
            properties["letter-spacing"] = f"{span['character_spacing']}pt"
            
        # Text decoration and alignment
        flags = span.get("flags", 0)
        if flags & 4:  # Underline flag
            properties["text-decoration"] = "underline"
        if flags & 2:  # Superscript flag
            properties["vertical-align"] = "super"
        elif flags & 3:  # Subscript flag
            properties["vertical-align"] = "sub"
            
        return properties

    @staticmethod
    def extract_block_properties(block: Dict[str, Any]) -> Dict[str, str]:
        """Extract text block level properties"""
        properties = {}
        
        if not isinstance(block, dict):
            return properties
            
        # Alignment
        align_map = {0: "left", 1: "center", 2: "right", 3: "justify"}
        if "align" in block:
            properties["text-align"] = align_map.get(block["align"], "left")
            
        # Line properties
        if "line_height" in block:
            properties["line-height"] = f"{block['line_height']}pt"
            
        # Text flow properties
        if "preserve_whitespace" in block:
            properties["white-space"] = "pre" if block["preserve_whitespace"] else "normal"
            
        return properties
        
    @staticmethod
    def get_font_info(doc: fitz.Document) -> Dict[str, Dict[str, Any]]:
        """Extract font information from PDF document"""
        fonts = {}
        for page in doc:
            for font in page.get_fonts():
                name = font["name"]
                if name not in fonts:
                    fonts[name] = {
                        "type": font["type"],
                        "encoding": font.get("encoding", "unknown"),
                        "embedded": font["embedded"],
                        "subset": font.get("subset", False)
                    }
        return fonts
        
    @staticmethod
    def analyze_text_block(block: Dict[str, Any]) -> Dict[str, Any]:
        """Perform detailed analysis of a text block"""
        analysis = {
            "word_count": 0,
            "char_count": 0,
            "line_count": 0,
            "avg_word_length": 0,
            "avg_line_length": 0,
            "has_hyphenation": False,
            "text_direction": "ltr",  # Default to left-to-right
        }
        
        if "lines" in block:
            analysis["line_count"] = len(block["lines"])
            
            for line in block["lines"]:
                if "text" in line:
                    text = line["text"]
                    words = text.split()
                    analysis["word_count"] += len(words)
                    analysis["char_count"] += len(text)
                    
                    # Check for hyphenation
                    if text.endswith("-"):
                        analysis["has_hyphenation"] = True
                        
            if analysis["line_count"] > 0:
                analysis["avg_line_length"] = analysis["char_count"] / analysis["line_count"]
            if analysis["word_count"] > 0:
                analysis["avg_word_length"] = analysis["char_count"] / analysis["word_count"]
                
        return analysis

    @staticmethod
    def calculate_text_dimensions(text: str, font_size: float, font_name: str) -> Tuple[float, float]:
        """Calculate approximate text dimensions"""
        # This is a simplified calculation - actual dimensions would require
        # the specific font metrics from the PDF
        char_width = font_size * 0.6  # Approximate average character width
        width = len(text) * char_width
        height = font_size * 1.2  # Standard line height
        return (width, height)