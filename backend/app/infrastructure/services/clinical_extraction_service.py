import re
import logging
from typing import Dict, Optional, List
from datetime import datetime

from app.infrastructure.services.normalization_service import get_normalization_service
from app.infrastructure.services.normalization_engine import get_normalization_engine

logger = logging.getLogger("clinical_extraction_service")

class ClinicalExtractionService:
    """Service for extracting structured clinical data from OCR text."""
    
    def __init__(self):
        # Define regex patterns for clinical data extraction
        self.patterns = {
            # Patient Information
            'patient_name': [
                r'patient\s*(?:name|:)\s*([A-Z][a-zA-Z\s]+)',
                r'name\s*[:]\s*([A-Z][a-zA-Z\s]+)',
                r'patient\s*[:]\s*([A-Z][a-zA-Z\s]+)',
                r'pt\s*name\s*[:]\s*([A-Z][a-zA-Z\s]+)'
            ],
            'uhid': [
                r'uhid\s*[:]\s*([A-Za-z0-9\-]+)',
                r'unique\s*hospital\s*id\s*[:]\s*([A-Za-z0-9\-]+)',
                r'uhid\s*no\s*[:]\s*([A-Za-z0-9\-]+)'
            ],
            'mrn': [
                r'mrn\s*[:]\s*([A-Za-z0-9\-]+)',
                r'medical\s*record\s*number\s*[:]\s*([A-Za-z0-9\-]+)',
                r'mr\s*no\s*[:]\s*([A-Za-z0-9\-]+)'
            ],
            'age': [
                r'age\s*[:]\s*(\d+)\s*(?:years?|yrs?|y)?',
                r'patient\s*age\s*[:]\s*(\d+)',
                r'aged\s*(\d+)\s*(?:years?|yrs?|y)?'
            ],
            'gender': [
                r'gender\s*[:]\s*(male|female|m|f)',
                r'sex\s*[:]\s*(male|female|m|f)',
                r'patient\s*sex\s*[:]\s*(male|female|m|f)'
            ],
            
            # Dates
            'admission_date': [
                r'admission\s*(?:date|dt)\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'admitted\s*(?:on|date)\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'date\s*of\s*admission\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
            ],
            'discharge_date': [
                r'discharge\s*(?:date|dt)\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'discharged\s*(?:on|date)\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'date\s*of\s*discharge\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
            ],
            'operation_date': [
                r'operation\s*(?:date|dt)\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'surgery\s*(?:date|dt)\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'procedure\s*date\s*[:]\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
            ],
            
            # Hospital Information
            'hospital': [
                r'hospital\s*name\s*[:]\s*([A-Za-z\s&]+)',
                r'hospital\s*[:]\s*([A-Za-z\s&]+)',
                r'institution\s*[:]\s*([A-Za-z\s&]+)'
            ],
            'doctor': [
                r'(?:attending|treating|consulting)\s*(?:doctor|physician|dr)\s*[:]\s*([A-Z][a-zA-Z\s\.]+)',
                r'doctor\s*[:]\s*([A-Z][a-zA-Z\s\.]+)',
                r'dr\s*[:]\s*([A-Z][a-zA-Z\s\.]+)',
                r'physician\s*[:]\s*([A-Z][a-zA-Z\s\.]+)'
            ],
            'department': [
                r'department\s*[:]\s*([A-Za-z\s]+)',
                r'ward\s*[:]\s*([A-Za-z\s]+)',
                r'unit\s*[:]\s*([A-Za-z\s]+)'
            ],
            
            # Medical Information
            'diagnosis': [
                r'diagnosis\s*[:]\s*([A-Za-z0-9\s\-\.,]+(?:\n[A-Za-z0-9\s\-\.,]+)*)',
                r'final\s*diagnosis\s*[:]\s*([A-Za-z0-9\s\-\.,]+(?:\n[A-Za-z0-9\s\-\.,]+)*)',
                r'principal\s*diagnosis\s*[:]\s*([A-Za-z0-9\s\-\.,]+(?:\n[A-Za-z0-9\s\-\.,]+)*)'
            ],
            'icd_codes': [
                r'icd\s*(?:code|10)\s*[:]\s*([A-Za-z0-9\.]+)',
                r'icd\s*[:]\s*([A-Za-z0-9\.]+)',
                r'diagnosis\s*code\s*[:]\s*([A-Za-z0-9\.]+)'
            ],
            'procedure': [
                r'procedure\s*(?:performed|done)\s*[:]\s*([A-Za-z0-9\s\-\.,]+(?:\n[A-Za-z0-9\s\-\.,]+)*)',
                r'surgery\s*[:]\s*([A-Za-z0-9\s\-\.,]+(?:\n[A-Za-z0-9\s\-\.,]+)*)',
                r'operation\s*[:]\s*([A-Za-z0-9\s\-\.,]+(?:\n[A-Za-z0-9\s\-\.,]+)*)'
            ],
            'cpt_codes': [
                r'cpt\s*(?:code|codes)\s*[:]\s*([0-9]+)',
                r'procedure\s*code\s*[:]\s*([0-9]+)',
                r'cpt\s*[:]\s*([0-9]+)'
            ],
            'medicines': [
                r'medicine(?:s)?\s*[:]\s*([A-Za-z0-9\s\-\.,]+)',
                r'drug(?:s)?\s*[:]\s*([A-Za-z0-9\s\-\.,]+)',
                r'medication(?:s)?\s*[:]\s*([A-Za-z0-9\s\-\.,]+)',
                r'prescribed\s*[:]\s*([A-Za-z0-9\s\-\.,]+)'
            ],
            'implants': [
                r'implant(?:s)?\s*[:]\s*([A-Za-z0-9\s\-\.,]+)',
                r'prosthesis\s*[:]\s*([A-Za-z0-9\s\-\.,]+)',
                r'device\s*[:]\s*([A-Za-z0-9\s\-\.,]+)'
            ],
            
            # Insurance Information
            'insurance_company': [
                r'insurance\s*company\s*[:]\s*([A-Za-z\s&]+)',
                r'insurer\s*[:]\s*([A-Za-z\s&]+)',
                r'tpa\s*[:]\s*([A-Za-z\s&]+)',
                r'insurance\s*provider\s*[:]\s*([A-Za-z\s&]+)'
            ],
            'policy_number': [
                r'policy\s*(?:number|no)\s*[:]\s*([A-Za-z0-9\-]+)',
                r'policy\s*[:]\s*([A-Za-z0-9\-]+)',
                r'insurance\s*policy\s*[:]\s*([A-Za-z0-9\-]+)'
            ],
            'bill_amount': [
                r'(?:total|bill|invoice)\s*amount\s*[:]\s*[\$€£₹]?\s*([0-9,]+\.?\d*)',
                r'amount\s*[:]\s*[\$€£₹]?\s*([0-9,]+\.?\d*)',
                r'charged\s*[:]\s*[\$€£₹]?\s*([0-9,]+\.?\d*)'
            ],
            'invoice_number': [
                r'invoice\s*(?:number|no)\s*[:]\s*([A-Za-z0-9\-]+)',
                r'bill\s*(?:number|no)\s*[:]\s*([A-Za-z0-9\-]+)',
                r'invoice\s*[:]\s*([A-Za-z0-9\-]+)'
            ]
        }
    
    def extract_clinical_data(self, ocr_text: str, document_id: str = None, hospital_id: str = None, db = None) -> Dict[str, any]:
        """
        Extract structured clinical data from OCR text and normalize it.
        
        Args:
            ocr_text: Raw OCR text from document
            document_id: Document ID for normalization tracking
            hospital_id: Hospital ID for normalization tracking
            db: Database session for storing normalization results
            
        Returns:
            Dictionary containing extracted and normalized clinical fields
        """
        if not ocr_text or len(ocr_text.strip()) < 50:
            logger.warning("[EXTRACTION_LOW_TEXT] Text too short for extraction")
            return self._empty_extraction()
        
        logger.info("[EXTRACTION_START] Beginning clinical data extraction")
        
        extracted_data = self._empty_extraction()
        fields_found = 0
        
        # Extract each field using patterns
        for field_name, patterns in self.patterns.items():
            value = self._extract_field(ocr_text, patterns, field_name)
            if value is not None:
                extracted_data[field_name] = value
                fields_found += 1
                logger.debug(f"[EXTRACTION_FIELD] {field_name}: {value}")
        
        # Calculate length of stay if dates available
        if extracted_data['admission_date'] and extracted_data['discharge_date']:
            extracted_data['length_of_stay'] = self._calculate_length_of_stay(
                extracted_data['admission_date'],
                extracted_data['discharge_date']
            )
        
        # Calculate extraction confidence
        total_fields = len(self.patterns)
        extraction_confidence = fields_found / total_fields if total_fields > 0 else 0.0
        extracted_data['extraction_confidence'] = extraction_confidence
        
        logger.info(f"[EXTRACTION_COMPLETE] Fields found: {fields_found}/{total_fields}, Confidence: {extraction_confidence:.2f}")
        
        # Normalize extracted data if document_id and hospital_id provided
        if document_id and hospital_id and db:
            try:
                normalization_service = get_normalization_service(db)
                normalization_result = normalization_service.normalize_and_store(
                    extracted_data,
                    document_id,
                    hospital_id
                )
                
                # Replace extracted data with normalized data for downstream use
                # Original values are preserved in the normalization table
                extracted_data = normalization_result["normalized_data"]
                extracted_data['original_data'] = {k: v for k, v in extracted_data.items()}
                
                logger.info(f"[NORMALIZATION_APPLIED] Document ID: {document_id}, Fields normalized: {len(normalization_result['normalization_results'])}")
            except Exception as e:
                logger.error(f"[NORMALIZATION_ERROR] Document ID: {document_id}, Error: {e}")
                # Continue with original data if normalization fails
        
        return extracted_data
    
    def _extract_field(self, text: str, patterns: List[str], field_name: str) -> Optional[any]:
        """Extract a single field using multiple patterns."""
        text_lower = text.lower()
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    
                    # Clean up the value
                    value = self._clean_value(value, field_name)
                    
                    if value and len(value) > 0:
                        return value
            except Exception as e:
                logger.debug(f"[EXTRACTION_PATTERN_ERROR] Field: {field_name}, Pattern: {pattern}, Error: {e}")
                continue
        
        return None
    
    def _clean_value(self, value: str, field_name: str) -> str:
        """Clean and normalize extracted value."""
        if not value:
            return value
        
        # Remove extra whitespace
        value = ' '.join(value.split())
        
        # Truncate very long values
        if len(value) > 500:
            value = value[:500]
        
        # Field-specific cleaning
        if field_name in ['age', 'bill_amount']:
            # Keep only numeric characters and decimal point
            value = re.sub(r'[^\d.]', '', value)
        elif field_name in ['gender']:
            value = value.lower()
            if value.startswith('m'):
                value = 'Male'
            elif value.startswith('f'):
                value = 'Female'
        elif field_name in ['icd_codes', 'cpt_codes']:
            # Keep only alphanumeric and dots
            value = re.sub(r'[^A-Za-z0-9\.]', '', value)
        
        return value
    
    def _calculate_length_of_stay(self, admission_date: str, discharge_date: str) -> Optional[int]:
        """Calculate length of stay in days."""
        try:
            # Parse dates (handle various formats)
            formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y', '%m/%d/%Y']
            
            adm_date = None
            dis_date = None
            
            for fmt in formats:
                try:
                    if not adm_date:
                        adm_date = datetime.strptime(admission_date, fmt)
                    if not dis_date:
                        dis_date = datetime.strptime(discharge_date, fmt)
                except ValueError:
                    continue
            
            if adm_date and dis_date:
                los = (dis_date - adm_date).days
                return max(0, los)  # Ensure non-negative
        except Exception as e:
            logger.debug(f"[LOS_CALCULATION_ERROR] {e}")
        
        return None
    
    def _empty_extraction(self) -> Dict[str, any]:
        """Return empty extraction structure."""
        return {
            'patient_name': None,
            'uhid': None,
            'mrn': None,
            'age': None,
            'gender': None,
            'admission_date': None,
            'discharge_date': None,
            'operation_date': None,
            'length_of_stay': None,
            'hospital': None,
            'doctor': None,
            'department': None,
            'diagnosis': None,
            'icd_codes': None,
            'procedure': None,
            'cpt_codes': None,
            'medicines': None,
            'implants': None,
            'insurance_company': None,
            'policy_number': None,
            'bill_amount': None,
            'invoice_number': None,
            'extraction_confidence': 0.0
        }


# Singleton instance
clinical_extraction_service = ClinicalExtractionService()
