from typing import Dict, Any, Optional
import pytesseract
import fitz
from PIL import Image
import io
from project.config.ocr_settings import get_ocr_parameters, configure_tesseract
from project.processing.ocr_preprocessing import prepare_page_for_ocr, get_language_hints
from project.processing.post_ocr_cleanup import clean_ocr_text, fix_line_breaks

class OCRProcessor:
    """Handle OCR processing for PDF documents"""
    
    def __init__(self):
        self.params = get_ocr_parameters()
        configure_tesseract()
        
    def process_pdf(self, pdf_path: str) -> bool:
        """Process PDF document with OCR"""
        try:
            doc = fitz.open(pdf_path)
            modified = False
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Skip pages that already have text
                if page.get_text().strip():
                    continue
                    
                # Get images from page
                images = self._extract_images(page)
                if not images:
                    continue
                    
                # Process each image
                for img_info in images:
                    text_blocks = self._process_image(img_info["image"])
                    if text_blocks:
                        self._insert_text(page, text_blocks, img_info["bbox"])
                        modified = True
                        
            if modified:
                doc.save(pdf_path)
                
            doc.close()
            return modified
            
        except Exception as e:
            print(f"OCR processing error: {str(e)}")
            return False
            
    def _extract_images(self, page: fitz.Page) -> list[Dict[str, Any]]:
        """Extract images from PDF page"""
        images = []
        for img in page.get_images():
            try:
                xref = img[0]
                base = page.parent.extract_image(xref)
                if base:
                    pil_img = Image.frombytes("RGB", 
                                            [base["width"], base["height"]], 
                                            base["image"])
                    images.append({
                        "image": pil_img,
                        "bbox": page.get_image_bbox(img),
                        "transform": img[1]  # Image transformation matrix
                    })
            except Exception as e:
                print(f"Image extraction error: {str(e)}")
                continue
                
        return images
        
    def _process_image(self, image: Image.Image) -> Optional[list[Dict[str, Any]]]:
        """Process image with OCR"""
        try:
            # Prepare image for OCR
            prepared_image = prepare_page_for_ocr(image)
            if not prepared_image:
                return None
                
            # Detect possible languages
            sample_text = pytesseract.image_to_string(
                prepared_image,
                config='--psm 3'
            )
            languages = get_language_hints(sample_text)
            
            # Perform OCR with detected languages
            ocr_data = pytesseract.image_to_data(
                prepared_image,
                lang='+'.join(languages),
                output_type=pytesseract.Output.DICT,
                config=f'--psm {self.params["psm"]} --oem {self.params["oem"]}'
            )
            
            # Convert OCR data to text blocks
            blocks = self._convert_to_blocks(ocr_data)
            
            # Clean up OCR results
            for block in blocks:
                if "text" in block:
                    block["text"] = clean_ocr_text(block["text"])
                    
            blocks = fix_line_breaks(blocks)
            
            return blocks
            
        except Exception as e:
            print(f"OCR processing error: {str(e)}")
            return None
            
    def _convert_to_blocks(self, ocr_data: Dict[str, Any]) -> list[Dict[str, Any]]:
        """Convert OCR data to text blocks"""
        blocks = []
        current_block = None
        
        for i in range(len(ocr_data['text'])):
            text = ocr_data['text'][i].strip()
            if not text:
                continue
                
            conf = float(ocr_data['conf'][i])
            if conf < 30:  # Skip low confidence results
                continue
                
            block_num = ocr_data['block_num'][i]
            
            if current_block is None or current_block['number'] != block_num:
                if current_block:
                    blocks.append(current_block)
                current_block = {
                    'number': block_num,
                    'bbox': fitz.Rect(
                        ocr_data['left'][i],
                        ocr_data['top'][i],
                        ocr_data['left'][i] + ocr_data['width'][i],
                        ocr_data['top'][i] + ocr_data['height'][i]
                    ),
                    'text': text,
                    'lines': []
                }
            else:
                current_block['text'] += f" {text}"
                current_block['bbox'] = current_block['bbox'] | fitz.Rect(
                    ocr_data['left'][i],
                    ocr_data['top'][i],
                    ocr_data['left'][i] + ocr_data['width'][i],
                    ocr_data['top'][i] + ocr_data['height'][i]
                )
                
        if current_block:
            blocks.append(current_block)
            
        return blocks
        
    def _insert_text(self, page: fitz.Page, blocks: list[Dict[str, Any]], image_bbox: fitz.Rect):
        """Insert OCR text blocks into PDF page"""
        for block in blocks:
            # Scale coordinates to match image position in PDF
            scale_x = image_bbox.width / page.rect.width
            scale_y = image_bbox.height / page.rect.height
            
            scaled_bbox = fitz.Rect(
                image_bbox.x0 + block['bbox'].x0 * scale_x,
                image_bbox.y0 + block['bbox'].y0 * scale_y,
                image_bbox.x0 + block['bbox'].x1 * scale_x,
                image_bbox.y0 + block['bbox'].y1 * scale_y
            )
            
            # Insert text
            page.insert_text(
                scaled_bbox.tl,  # Top-left point
                block['text'],
                fontname="helv",  # Use standard font
                fontsize=12,  # Default size
                color=(0, 0, 0)  # Black text
            )
            
            # Store original bbox for future reference
            annot = page.add_freetext_annot(
                scaled_bbox,
                str(block['bbox']),
                fontname="helv",
                fontsize=0.1,  # Make annotation invisible
                text_color=(0, 0, 0, 0)  # Transparent
            )