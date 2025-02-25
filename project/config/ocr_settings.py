from typing import Dict, Any, List
import os

def get_ocr_parameters() -> Dict[str, Any]:
    """Get OCR processing parameters"""
    return {
        'dpi': 300,  # Resolution for image processing
        'lang': 'eng',  # Default language
        'psm': 3,  # Page segmentation mode: 3 = Fully automatic without OSD
        'oem': 3,  # OCR Engine mode: 3 = Default
        'preprocessing': {
            'contrast_threshold': 128,  # Threshold for binarization
            'min_text_height': 8,  # Minimum text height in pixels
            'noise_reduction': True,  # Apply noise reduction
            'deskew': True  # Automatic page deskewing
        },
        'tesseract_path': r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Default Windows path
    }

def get_language_files() -> List[str]:
    """Get available language data files"""
    tesseract_path = r'C:\Program Files\Tesseract-OCR\tessdata'
    if not os.path.exists(tesseract_path):
        return ['eng']  # Default to English if path not found
        
    langs = []
    for file in os.listdir(tesseract_path):
        if file.endswith('.traineddata'):
            langs.append(file[:-12])  # Remove .traineddata extension
    return langs or ['eng']

def configure_tesseract() -> None:
    """Configure Tesseract environment variables if needed"""
    if os.name == 'nt':  # Windows
        tesseract_path = r'C:\Program Files\Tesseract-OCR'
        if os.path.exists(tesseract_path):
            os.environ['TESSDATA_PREFIX'] = os.path.join(tesseract_path, 'tessdata')
            if 'PATH' in os.environ:
                os.environ['PATH'] = f"{tesseract_path};{os.environ['PATH']}"

def validate_ocr_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize OCR settings"""
    validated = {}
    
    # Validate basic settings
    validated["dpi"] = max(72, min(1200, settings.get("dpi", 300)))
    validated["language"] = settings.get("language", "eng")
    
    # Validate preprocessing settings
    preprocessing = settings.get("preprocessing", {})
    validated["preprocessing"] = {
        "denoise": bool(preprocessing.get("denoise", True)),
        "deskew": bool(preprocessing.get("deskew", True)),
        "remove_borders": bool(preprocessing.get("remove_borders", True)),
        "contrast_enhancement": bool(preprocessing.get("contrast_enhancement", True)),
        "thresholding": preprocessing.get("thresholding", "adaptive")
    }
    
    # Validate PDF settings
    pdf_settings = settings.get("pdf", {})
    validated["pdf"] = {
        "embedded_text_handling": pdf_settings.get("embedded_text_handling", "preserve"),
        "image_dpi_threshold": max(72, min(600, pdf_settings.get("image_dpi_threshold", 150))),
        "force_ocr": bool(pdf_settings.get("force_ocr", False))
    }
    
    # Validate performance settings
    performance = settings.get("performance", {})
    validated["performance"] = {
        "threads": max(1, min(16, performance.get("threads", 4))),
        "batch_size": max(1, min(50, performance.get("batch_size", 10))),
        "gpu_acceleration": bool(performance.get("gpu_acceleration", True)),
        "memory_limit": max(512, min(8192, performance.get("memory_limit", 2048)))
    }
    
    return validated

def merge_ocr_settings(base_settings: Dict[str, Any], override_settings: Dict[str, Any]) -> Dict[str, Any]:
    """Merge OCR settings with overrides"""
    merged = base_settings.copy()
    
    for key, value in override_settings.items():
        if isinstance(value, dict) and key in merged:
            merged[key] = merge_ocr_settings(merged[key], value)
        else:
            merged[key] = value
            
    return merged