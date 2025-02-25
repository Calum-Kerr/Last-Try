from typing import Dict, Any, List
import re
import difflib
from ..utils.pdf_metadata import PDFTextProperties

def clean_ocr_text(text: str) -> str:
    """Clean up common OCR artifacts and errors"""
    # Remove repeated whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix common OCR errors
    replacements = {
        r'l([A-Z])': r'I\1',  # lowercase l at start of word likely capital I
        r'([0-9])l': r'\11',  # lowercase l after number likely 1
        r'([A-Z])1': r'\1l',  # 1 after capital letter likely lowercase l
        r'0([A-Z])': r'O\1',  # 0 at start of word likely capital O
        r'([A-Z])0': r'\1O',  # 0 after capital likely capital O
        r'([a-z])/([a-z])': r'\1l\2',  # slash between lowercase likely lowercase l
        r'rn': 'm',  # 'rn' commonly misrecognized as 'm'
        r'([A-Z])5': r'\1S',  # 5 after capital likely S
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    
    return text.strip()

def fix_line_breaks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fix incorrect line breaks in OCR output"""
    for block in blocks:
        if "lines" in block:
            fixed_lines = []
            current_line = ""
            
            for line in block["lines"]:
                if "text" in line:
                    text = line["text"]
                    
                    # Check if line ends with hyphenation
                    if text.endswith('-'):
                        current_line += text[:-1]
                        continue
                        
                    # Check if line ends mid-sentence
                    if not any(text.endswith(p) for p in '.!?'):
                        # Check next line's case to determine if it's a continuation
                        next_line = block["lines"][block["lines"].index(line) + 1] \
                            if block["lines"].index(line) < len(block["lines"]) - 1 else None
                            
                        if next_line and "text" in next_line and \
                           next_line["text"][0].islower():
                            current_line += text + " "
                            continue
                            
                    current_line += text
                    fixed_lines.append({"text": current_line, **{k: v for k, v in line.items() if k != "text"}})
                    current_line = ""
                    
            if current_line:  # Handle any remaining text
                fixed_lines.append({"text": current_line})
                
            block["lines"] = fixed_lines
            
    return blocks

def merge_similar_blocks(blocks: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
    """Merge text blocks that are likely part of the same content"""
    merged_blocks = []
    current_block = None
    
    for block in blocks:
        if not current_block:
            current_block = block
            continue
            
        # Check if blocks have similar properties
        current_props = PDFTextProperties.extract_block_properties(current_block)
        next_props = PDFTextProperties.extract_block_properties(block)
        
        # Compare text properties
        props_match = all(
            current_props.get(prop) == next_props.get(prop)
            for prop in ['font-family', 'font-size', 'text-align']
        )
        
        # Check text content similarity
        if props_match and "text" in current_block and "text" in block:
            similarity = difflib.SequenceMatcher(
                None,
                current_block["text"],
                block["text"]
            ).ratio()
            
            if similarity >= similarity_threshold:
                # Merge blocks
                current_block["lines"].extend(block["lines"])
                continue
                
        merged_blocks.append(current_block)
        current_block = block
        
    if current_block:
        merged_blocks.append(current_block)
        
    return merged_blocks

def validate_text_attributes(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate and normalize text attributes after OCR"""
    for block in blocks:
        if "lines" in block:
            for line in block["lines"]:
                if "spans" in line:
                    for span in line["spans"]:
                        # Validate font properties
                        if "font" in span:
                            span["font"] = re.sub(r'[^\w\s-]', '', span["font"])
                            
                        # Normalize size values
                        if "size" in span:
                            try:
                                span["size"] = float(span["size"])
                            except (ValueError, TypeError):
                                span["size"] = 12.0  # Default size
                                
                        # Validate flags
                        if "flags" in span:
                            span["flags"] = int(span["flags"]) & 0xFF  # Ensure valid flag byte
                            
        # Ensure block has required properties
        if "bbox" not in block:
            block["bbox"] = None  # Will be calculated later
            
    return blocks

def fix_text_positioning(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fix text positioning and alignment issues"""
    for block in blocks:
        if "lines" in block:
            # Calculate average line metrics
            line_heights = []
            line_indents = []
            
            for line in block["lines"]:
                if "bbox" in line:
                    line_heights.append(line["bbox"].height)
                    line_indents.append(line["bbox"].x0)
                    
            if line_heights and line_indents:
                avg_height = sum(line_heights) / len(line_heights)
                most_common_indent = max(set(line_indents), key=line_indents.count)
                
                # Normalize line positioning
                y_pos = block.get("bbox", None).y0 if block.get("bbox") else 0
                for line in block["lines"]:
                    if "bbox" in line:
                        # Align to most common indent
                        line["bbox"].x0 = most_common_indent
                        # Set consistent line height
                        line["bbox"].height = avg_height
                        # Update vertical position
                        line["bbox"].y0 = y_pos
                        y_pos += avg_height
                        
    return blocks