import re
import logging
from typing import Dict, Tuple, List
from app.infrastructure.db.models.claim import DocumentType

logger = logging.getLogger("classification_service")

class DocumentClassificationService:
    """Service for classifying medical documents based on OCR text."""
    
    def __init__(self):
        # Define keyword patterns for each document type
        self.classification_patterns = {
            DocumentType.DISCHARGE_SUMMARY: {
                'keywords': [
                    'discharge summary', 'discharge report', 'final discharge',
                    'patient discharged', 'discharge instructions',
                    'discharge diagnosis', 'hospital course',
                    'discharge medications', 'follow-up'
                ],
                'weight': 1.0
            },
            DocumentType.OPERATIVE_NOTE: {
                'keywords': [
                    'operative note', 'operation report', 'surgical report',
                    'procedure note', 'operative procedure',
                    'preoperative diagnosis', 'postoperative diagnosis',
                    'anesthesia', 'surgeon', 'operating room'
                ],
                'weight': 1.0
            },
            DocumentType.FINAL_BILL: {
                'keywords': [
                    'final bill', 'invoice', 'statement of account',
                    'total amount', 'balance due', 'payment due',
                    'billing statement', 'hospital bill',
                    'itemized bill', 'charges', 'amount due'
                ],
                'weight': 1.0
            },
            DocumentType.PRESCRIPTION: {
                'keywords': [
                    'prescription', 'rx', 'medication', 'pharmacy',
                    'dispense', 'dosage', 'take', 'refill',
                    'drug', 'medicine', 'prescribed by'
                ],
                'weight': 0.9
            },
            DocumentType.AUTHORIZATION_LETTER: {
                'keywords': [
                    'authorization', 'prior authorization', 'pre-authorization',
                    'approved', 'authorization number', 'authorization code',
                    'insurance authorization', 'treatment authorization',
                    'authorized by', 'authorization request'
                ],
                'weight': 1.0
            },
            DocumentType.INVESTIGATION_REPORT: {
                'keywords': [
                    'investigation report', 'diagnostic report',
                    'clinical investigation', 'medical investigation',
                    'examination report', 'assessment report'
                ],
                'weight': 0.9
            },
            DocumentType.LAB_REPORT: {
                'keywords': [
                    'lab report', 'laboratory report', 'laboratory results',
                    'blood test', 'lab results', 'pathology report',
                    'hematology', 'biochemistry', 'microbiology',
                    'specimen', 'reference range'
                ],
                'weight': 1.0
            },
            DocumentType.RADIOLOGY_REPORT: {
                'keywords': [
                    'radiology report', 'x-ray report', 'ct report',
                    'mri report', 'ultrasound report', 'imaging report',
                    'radiographic findings', 'impression', 'radiologist',
                    'scan', 'radiology'
                ],
                'weight': 1.0
            },
            DocumentType.INSURANCE_FORM: {
                'keywords': [
                    'insurance form', 'claim form', 'insurance claim',
                    'insurance information', 'policy number', 'member id',
                    'insurance company', 'provider', 'payer',
                    'claim form', 'cms-1500', 'ub-04'
                ],
                'weight': 1.0
            },
            DocumentType.CONSENT_FORM: {
                'keywords': [
                    'consent form', 'informed consent', 'patient consent',
                    'consent to treatment', 'consent to procedure',
                    'consent signed', 'authorization for treatment',
                    'patient authorization', 'consent agreement'
                ],
                'weight': 1.0
            }
        }
    
    def classify_document(self, ocr_text: str, filename: str = "") -> Tuple[str, float]:
        """
        Classify document based on OCR text and filename.
        
        Args:
            ocr_text: Extracted text from OCR
            filename: Original filename (optional)
            
        Returns:
            Tuple of (document_type, confidence_score)
        """
        if not ocr_text or len(ocr_text.strip()) < 50:
            logger.warning(f"[CLASSIFICATION_LOW_TEXT] Text too short for classification")
            return DocumentType.UNKNOWN.value, 0.0
        
        # Combine text and filename for classification
        combined_text = (ocr_text + " " + filename).lower()
        
        # Score each document type
        scores = {}
        for doc_type, pattern in self.classification_patterns.items():
            score = 0.0
            matched_keywords = []
            
            for keyword in pattern['keywords']:
                keyword_lower = keyword.lower()
                # Count occurrences of keyword
                count = combined_text.count(keyword_lower)
                if count > 0:
                    score += count * pattern['weight']
                    matched_keywords.append(keyword)
            
            if score > 0:
                scores[doc_type] = {
                    'score': score,
                    'matched_keywords': matched_keywords
                }
        
        if not scores:
            logger.info(f"[CLASSIFICATION_UNKNOWN] No matching patterns found")
            return DocumentType.UNKNOWN.value, 0.0
        
        # Get the highest scoring document type
        best_match = max(scores.items(), key=lambda x: x[1]['score'])
        doc_type, match_info = best_match
        
        # Calculate confidence based on score and text length
        max_possible_score = len(self.classification_patterns[doc_type]['keywords']) * 2.0
        raw_confidence = min(match_info['score'] / max_possible_score, 1.0)
        
        # Boost confidence if multiple keywords matched
        keyword_count = len(match_info['matched_keywords'])
        confidence_boost = min(keyword_count * 0.1, 0.3)
        
        final_confidence = min(raw_confidence + confidence_boost, 1.0)
        
        # Log classification details
        logger.info(f"[CLASSIFICATION_RESULT] Type: {doc_type.value}, Confidence: {final_confidence:.2f}, Keywords: {match_info['matched_keywords']}")
        
        return doc_type.value, final_confidence
    
    def get_classification_suggestions(self, ocr_text: str, filename: str = "", top_n: int = 3) -> List[Dict[str, any]]:
        """
        Get top N classification suggestions with confidence scores.
        
        Args:
            ocr_text: Extracted text from OCR
            filename: Original filename (optional)
            top_n: Number of suggestions to return
            
        Returns:
            List of classification suggestions with confidence scores
        """
        if not ocr_text or len(ocr_text.strip()) < 50:
            return [{'type': DocumentType.UNKNOWN.value, 'confidence': 0.0}]
        
        combined_text = (ocr_text + " " + filename).lower()
        scores = {}
        
        for doc_type, pattern in self.classification_patterns.items():
            score = 0.0
            matched_keywords = []
            
            for keyword in pattern['keywords']:
                keyword_lower = keyword.lower()
                count = combined_text.count(keyword_lower)
                if count > 0:
                    score += count * pattern['weight']
                    matched_keywords.append(keyword)
            
            if score > 0:
                max_possible_score = len(pattern['keywords']) * 2.0
                raw_confidence = min(score / max_possible_score, 1.0)
                keyword_count = len(matched_keywords)
                confidence_boost = min(keyword_count * 0.1, 0.3)
                final_confidence = min(raw_confidence + confidence_boost, 1.0)
                
                scores[doc_type] = {
                    'type': doc_type.value,
                    'confidence': final_confidence,
                    'matched_keywords': matched_keywords
                }
        
        # Sort by confidence and return top N
        sorted_scores = sorted(scores.values(), key=lambda x: x['confidence'], reverse=True)
        return sorted_scores[:top_n]


# Singleton instance
classification_service = DocumentClassificationService()
