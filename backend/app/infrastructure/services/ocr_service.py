import os
import time
import logging
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger("ocr_service")

class OCRService:
    """Production-grade OCR service using Tesseract."""
    
    def __init__(self):
        # Configure Tesseract path if needed
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
        self.supported_formats = ['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif']
    
    def process_document(self, file_path: str, document_id: str, hospital_id: str) -> Dict[str, Any]:
        """
        Process a document through the OCR pipeline.
        
        Args:
            file_path: Path to the document file
            document_id: ID of the document being processed
            hospital_id: ID of the hospital owning the document
            
        Returns:
            Dictionary containing OCR results and metadata
        """
        start_time = time.time()
        logger.info(f"[OCR_START] Document ID: {document_id}, File: {file_path}")
        
        try:
            # Determine file type
            file_ext = os.path.splitext(file_path)[1].lower().replace('.', '')
            
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Extract text based on file type
            if file_ext == 'pdf':
                raw_text, page_count, confidence = self._process_pdf(file_path)
            else:
                raw_text, page_count, confidence = self._process_image(file_path)
            
            processing_time = time.time() - start_time
            
            # Detect language
            detected_language = self._detect_language(raw_text)
            
            # Extract structured data (basic)
            structured_data = self._extract_structured_data(raw_text)
            
            logger.info(f"[OCR_SUCCESS] Document ID: {document_id}, Pages: {page_count}, Confidence: {confidence:.2f}, Time: {processing_time:.2f}s")
            
            return {
                'raw_text': raw_text,
                'structured_data': structured_data,
                'ocr_confidence': confidence,
                'processing_time_seconds': processing_time,
                'page_count': page_count,
                'detected_language': detected_language,
                'processing_status': 'completed',
                'error_message': None
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"[OCR_ERROR] Document ID: {document_id}, Error: {str(e)}")
            
            return {
                'raw_text': None,
                'structured_data': None,
                'ocr_confidence': 0.0,
                'processing_time_seconds': processing_time,
                'page_count': 0,
                'detected_language': None,
                'processing_status': 'failed',
                'error_message': str(e)
            }
    
    def _process_pdf(self, file_path: str) -> Tuple[str, int, float]:
        """Process PDF file with OCR."""
        logger.info(f"[OCR_PDF] Processing PDF: {file_path}")
        
        # Convert PDF to images
        try:
            images = convert_from_path(file_path, dpi=300)
        except Exception as e:
            logger.error(f"[OCR_PDF_ERROR] Failed to convert PDF: {e}")
            raise
        
        page_count = len(images)
        all_text = []
        total_confidence = 0.0
        
        for i, image in enumerate(images):
            logger.debug(f"[OCR_PDF_PAGE] Processing page {i+1}/{page_count}")
            
            # Preprocess image
            processed_image = self._preprocess_image(image)
            
            # Perform OCR
            text, confidence = self._perform_ocr(processed_image)
            
            all_text.append(text)
            total_confidence += confidence
        
        combined_text = "\n\n".join(all_text)
        avg_confidence = total_confidence / page_count if page_count > 0 else 0.0
        
        return combined_text, page_count, avg_confidence
    
    def _process_image(self, file_path: str) -> Tuple[str, int, float]:
        """Process single image file with OCR."""
        logger.info(f"[OCR_IMAGE] Processing image: {file_path}")
        
        # Load image
        image = Image.open(file_path)
        
        # Preprocess
        processed_image = self._preprocess_image(image)
        
        # Perform OCR
        text, confidence = self._perform_ocr(processed_image)
        
        return text, 1, confidence
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy."""
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Apply thresholding for better text extraction
        _, thresholded = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.medianBlur(thresholded, 3)
        
        # Convert back to PIL Image
        processed_image = Image.fromarray(denoised)
        
        return processed_image
    
    def _perform_ocr(self, image: Image.Image) -> Tuple[str, float]:
        """Perform OCR on image and return text with confidence."""
        # Configure Tesseract for better medical document processing
        config = r'--oem 3 --psm 6 -l eng+spa+fra+deu'  # LSTM OCR, assume uniform block of text, multiple languages
        
        # Get OCR data with confidence
        data = pytesseract.image_to_data(image, config=config, output_type=pytesseract.Output.DICT)
        
        # Extract text
        text_lines = []
        confidence_values = []
        
        for i, text in enumerate(data['text']):
            if text.strip():
                text_lines.append(text)
                conf = int(data['conf'][i])
                if conf > 0:
                    confidence_values.append(conf)
        
        combined_text = "\n".join(text_lines)
        avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0.0
        
        return combined_text, avg_confidence
    
    def _detect_language(self, text: str) -> str:
        """Detect language from OCR text."""
        if not text or len(text) < 10:
            return "unknown"
        
        # Simple language detection based on character patterns
        # In production, use a proper language detection library like langdetect
        text_sample = text[:1000].lower()
        
        # Check for common language indicators
        if any(char in text_sample for char in 'äöüß'):
            return "ger"
        elif any(char in text_sample for char in 'áéíóúñ¿¡'):
            return "spa"
        elif any(char in text_sample for char in 'àâäéèêëïîôùûüÿœæ'):
            return "fra"
        else:
            return "eng"  # Default to English
    
    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        """Extract structured data from OCR text."""
        structured_data = {
            'potential_dates': [],
            'potential_amounts': [],
            'potential_phone_numbers': [],
            'line_count': len(text.split('\n')),
            'word_count': len(text.split()),
            'char_count': len(text)
        }
        
        # Extract potential dates (DD/MM/YYYY, MM/DD/YYYY formats)
        import re
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{1,2}-\d{1,2}-\d{4}',
            r'\d{4}/\d{1,2}/\d{1,2}'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            structured_data['potential_dates'].extend(matches)
        
        # Extract potential monetary amounts
        amount_pattern = r'[\$€£₹]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
        amount_matches = re.findall(amount_pattern, text)
        structured_data['potential_amounts'].extend(amount_matches)
        
        # Extract potential phone numbers
        phone_pattern = r'\+?[\d\s\-\(\)]{10,}'
        phone_matches = re.findall(phone_pattern, text)
        structured_data['potential_phone_numbers'].extend(phone_matches)
        
        return structured_data


# Singleton instance
ocr_service = OCRService()
