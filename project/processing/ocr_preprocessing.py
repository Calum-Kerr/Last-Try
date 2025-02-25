from typing import Dict, Any, Optional
import fitz
from PIL import Image
import numpy as np
from project.config.ocr_settings import get_ocr_parameters

def needs_ocr(pdf_path: str) -> bool:
    """Determine if a PDF needs OCR processing"""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            # Check if page has text
            if page.get_text().strip():
                continue
                
            # Check for image-only content
            image_list = page.get_images()
            if image_list:
                return True
                
        return False
    except Exception as e:
        print(f"Error checking OCR requirements: {str(e)}")
        return False
    finally:
        if 'doc' in locals():
            doc.close()

def optimize_for_ocr(image: Image.Image) -> Image.Image:
    """Optimize image for OCR processing"""
    # Convert to grayscale
    if image.mode != 'L':
        image = image.convert('L')
        
    # Increase contrast
    enhanced = Image.fromarray(np.uint8(255 * (np.array(image) / 255) ** 0.8))
    
    # Apply adaptive thresholding
    threshold = get_adaptive_threshold(enhanced)
    binary = enhanced.point(lambda x: 255 if x > threshold else 0)
    
    return binary

def get_adaptive_threshold(image: Image.Image) -> int:
    """Calculate adaptive threshold using Otsu's method"""
    hist = image.histogram()
    total = sum(hist)
    
    weight_bg = weight_fg = 0
    sum_bg = sum_fg = 0
    max_variance = 0
    threshold = 0
    
    for t in range(256):
        weight_bg += hist[t]
        if weight_bg == 0:
            continue
            
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
            
        sum_bg += t * hist[t]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum(i * hist[i] for i in range(t+1, 256))) / weight_fg
        
        variance = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if variance > max_variance:
            max_variance = variance
            threshold = t
            
    return threshold

def estimate_dpi(page: fitz.Page) -> int:
    """Estimate effective DPI for OCR processing"""
    # Get page dimensions
    width, height = page.rect.width, page.rect.height
    
    # Check images on page
    max_dpi = 0
    for img in page.get_images():
        xref = img[0]
        base = page.parent.extract_image(xref)
        if base:
            pil_img = Image.frombytes("RGB", [base["width"], base["height"]], base["image"])
            img_dpi = int(base["width"] / width * 72)  # 72 is the base PDF DPI
            max_dpi = max(max_dpi, img_dpi)
            
    return max_dpi if max_dpi > 0 else 300  # Default to 300 DPI

def prepare_page_for_ocr(page: fitz.Page) -> Optional[Image.Image]:
    """Prepare a PDF page for OCR processing"""
    try:
        # Convert page to image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scaling for better OCR
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Optimize image
        optimized = optimize_for_ocr(img)
        
        return optimized
    except Exception as e:
        print(f"Error preparing page for OCR: {str(e)}")
        return None

def get_language_hints(text_sample: str) -> list[str]:
    """Detect potential languages in text for OCR optimization"""
    # Simple character-based language detection
    languages = []
    
    # Check for CJK characters
    if any(ord(c) > 0x4E00 and ord(c) < 0x9FFF for c in text_sample):
        languages.extend(['chi_sim', 'chi_tra', 'jpn', 'kor'])
        
    # Check for Cyrillic
    if any(ord(c) > 0x0400 and ord(c) < 0x04FF for c in text_sample):
        languages.append('rus')
        
    # Default to English if no specific scripts detected
    if not languages:
        languages.append('eng')
        
    return languages