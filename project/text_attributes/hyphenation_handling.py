from typing import Dict, Any, Literal, Optional
import re

HyphenationMode = Literal['auto', 'manual', 'none']

class Hyphenator:
    """Simple hyphenation engine using common English patterns"""
    def __init__(self):
        # Common English syllable patterns
        self.patterns = [
            r'([^aeiou])([aeiou])([^aeiou])',  # CVC pattern
            r'([aeiou])([^aeiou]{2,})',        # VCC pattern
            r'([^aeiou]{2,})([aeiou])',        # CCV pattern
        ]
        
    def hyphenate(self, word: str) -> list[str]:
        """Split word into hyphenatable parts"""
        if len(word) < 4:  # Don't hyphenate short words
            return [word]
            
        positions = set()
        for pattern in self.patterns:
            for match in re.finditer(pattern, word.lower()):
                pos = match.end(1)
                if pos > 1 and pos < len(word) - 2:  # Avoid start/end
                    positions.add(pos)
        
        if not positions:
            return [word]
            
        # Build parts
        positions = sorted(positions)
        parts = []
        last_pos = 0
        for pos in positions:
            parts.append(word[last_pos:pos])
            last_pos = pos
        parts.append(word[last_pos:])
        return parts

def extract_hyphenation(block: Dict[str, Any]) -> str:
    """Extract hyphenation settings from PyMuPDF block data"""
    if not isinstance(block, dict):
        return ""
    
    # Check for explicit hyphenation settings
    if "hyphenation" in block:
        return f"hyphens: {block['hyphenation']};"
    
    # Try to detect from content
    if "lines" in block and len(block["lines"]) > 0:
        for line in block["lines"]:
            if "text" in line:
                # Check for hyphenated line endings
                if line["text"].endswith("-"):
                    return "hyphens: auto;"
    
    return "hyphens: none;"

def apply_hyphenation(html_fragment: str, mode: HyphenationMode) -> str:
    """Apply hyphenation during HTML generation"""
    if mode == "none":
        return html_fragment
    return f'<div style="hyphens: {mode};">{html_fragment}</div>'

def reinsert_hyphenation(pdf_writer: Any, block: Dict[str, Any], style_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Reapply hyphenation during PDF writing"""
    if "hyphens" in style_dict:
        mode = style_dict["hyphens"]
        block["hyphenation"] = mode
        
        if mode != "none" and "lines" in block:
            hyphenator = Hyphenator()
            
            # Process each line
            for i, line in enumerate(block["lines"]):
                if "text" in line and "bbox" in line:
                    text = line["text"]
                    available_width = line["bbox"].width
                    
                    # Only process lines that might overflow
                    if pdf_writer.get_text_width(text) > available_width:
                        words = text.split()
                        current_line = []
                        current_width = 0
                        
                        for word in words:
                            word_width = pdf_writer.get_text_width(word + " ")
                            
                            if current_width + word_width > available_width:
                                # Try hyphenation
                                parts = hyphenator.hyphenate(word)
                                if len(parts) > 1:
                                    # Find best hyphenation point
                                    for j in range(len(parts) - 1):
                                        partial = "-".join(parts[:j+1]) + "-"
                                        if current_width + pdf_writer.get_text_width(partial) <= available_width:
                                            # Update current line with hyphenated part
                                            current_line.append(partial)
                                            line["text"] = " ".join(current_line)
                                            
                                            # Create new line with remainder
                                            remainder = "".join(parts[j+1:])
                                            if i + 1 < len(block["lines"]):
                                                block["lines"][i + 1]["text"] = remainder + " " + \
                                                    block["lines"][i + 1].get("text", "")
                                            else:
                                                block["lines"].append({
                                                    "text": remainder,
                                                    "bbox": line["bbox"].copy()
                                                })
                                            break
                            else:
                                current_line.append(word)
                                current_width += word_width
    
    return block

def get_available_hyphenation_modes() -> list[HyphenationMode]:
    """Get list of available hyphenation modes"""
    return ['auto', 'manual', 'none']