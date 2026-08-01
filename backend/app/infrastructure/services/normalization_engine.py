import re
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from dateutil import parser as date_parser
from decimal import Decimal, InvalidOperation

logger = logging.getLogger("normalization_engine")


class DateNormalizer:
    """Normalize dates to ISO 8601 format"""
    
    # Common Indian date formats
    INDIAN_DATE_FORMATS = [
        "%d-%m-%Y",  # 01-01-2024
        "%d/%m/%Y",  # 01/01/2024
        "%d.%m.%Y",  # 01.01.2024
        "%d %b %Y",  # 01 Jan 2024
        "%d %B %Y",  # 01 January 2024
        "%d-%m-%y",  # 01-01-24
        "%d/%m/%y",  # 01/01/24
        "%Y-%m-%d",  # 2024-01-01 (ISO)
        "%Y/%m/%d",  # 2024/01/01
        "%b %d, %Y",  # Jan 01, 2024
        "%B %d, %Y",  # January 01, 2024
    ]
    
    @classmethod
    def normalize(cls, date_str: str) -> Tuple[Optional[str], float]:
        """
        Normalize date string to ISO 8601 format.
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Tuple of (normalized_iso_date, confidence_score)
        """
        if not date_str or not isinstance(date_str, str):
            return None, 0.0
        
        date_str = date_str.strip()
        
        # Try parsing with dateutil (handles most formats)
        try:
            parsed_date = date_parser.parse(date_str, dayfirst=True)
            iso_date = parsed_date.strftime("%Y-%m-%d")
            return iso_date, 0.95
        except (ValueError, TypeError):
            pass
        
        # Try specific Indian formats
        for fmt in cls.INDIAN_DATE_FORMATS:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                iso_date = parsed_date.strftime("%Y-%m-%d")
                return iso_date, 0.85
            except ValueError:
                continue
        
        logger.warning(f"[DATE_NORMALIZATION_FAILED] Could not parse: {date_str}")
        return None, 0.0


class DoctorNameNormalizer:
    """Normalize doctor names by removing prefixes while preserving original"""
    
    # Common doctor prefixes in India
    PREFIXES = [
        "Dr.", "Dr ", "DR.", "DR ", "Dr", "DR",
        "Dr.", "Dr ", "Prof.", "Prof ", "Prof",
        "Prof. Dr.", "Prof. Dr ", "Prof Dr.", "Prof Dr ",
        "Ms.", "Ms ", "Mrs.", "Mrs ", "Mr.", "Mr ",
        "Shri.", "Shri ", "Smt.", "Smt "
    ]
    
    @classmethod
    def normalize(cls, name: str) -> Tuple[Optional[str], str, float]:
        """
        Normalize doctor name by removing prefixes.
        
        Args:
            name: Doctor name with possible prefixes
            
        Returns:
            Tuple of (normalized_name, original_name, confidence_score)
        """
        if not name or not isinstance(name, str):
            return None, name or "", 0.0
        
        original_name = name.strip()
        normalized_name = original_name
        
        # Remove prefixes
        for prefix in cls.PREFIXES:
            if normalized_name.startswith(prefix):
                normalized_name = normalized_name[len(prefix):].strip()
                return normalized_name, original_name, 0.9
        
        # No prefix found, return as-is
        return normalized_name, original_name, 1.0


class DiagnosisNormalizer:
    """Normalize diagnosis by standardizing spacing and punctuation"""
    
    @classmethod
    def normalize(cls, diagnosis: str) -> Tuple[Optional[str], str, float]:
        """
        Normalize diagnosis text.
        
        Args:
            diagnosis: Diagnosis text
            
        Returns:
            Tuple of (normalized_diagnosis, original_diagnosis, confidence_score)
        """
        if not diagnosis or not isinstance(diagnosis, str):
            return None, diagnosis or "", 0.0
        
        original_diagnosis = diagnosis.strip()
        normalized = original_diagnosis
        
        # Normalize spacing: multiple spaces to single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Normalize punctuation: ensure single spaces after commas, periods
        normalized = re.sub(r'\s*,\s*', ', ', normalized)
        normalized = re.sub(r'\s*\.\s*', '. ', normalized)
        normalized = re.sub(r'\s*;\s*', '; ', normalized)
        
        # Remove trailing punctuation
        normalized = normalized.rstrip('.,;:')
        
        # Capitalize first letter of each sentence
        sentences = normalized.split('. ')
        normalized = '. '.join(s.capitalize() for s in sentences)
        
        # Calculate confidence based on changes made
        changes = sum(1 for a, b in zip(original_diagnosis, normalized) if a != b)
        confidence = max(0.5, 1.0 - (changes / len(original_diagnosis)) * 0.5)
        
        return normalized, original_diagnosis, confidence


class ProcedureCodeNormalizer:
    """Normalize procedure codes to uppercase"""
    
    @classmethod
    def normalize(cls, code: str) -> Tuple[Optional[str], str, float]:
        """
        Normalize procedure code to uppercase.
        
        Args:
            code: Procedure code (CPT, ICD, etc.)
            
        Returns:
            Tuple of (normalized_code, original_code, confidence_score)
        """
        if not code or not isinstance(code, str):
            return None, code or "", 0.0
        
        original_code = code.strip()
        normalized = original_code.upper()
        
        # Remove spaces from codes (e.g., "CPT 12345" -> "CPT12345")
        normalized = re.sub(r'\s+', '', normalized)
        
        confidence = 1.0 if normalized == original_code.upper() else 0.95
        
        return normalized, original_code, confidence


class InsuranceNameNormalizer:
    """Normalize insurance company names using alias mapping"""
    
    # Insurance company aliases mapping
    INSURANCE_ALIASES = {
        # Star Health variations
        "star health": "Star Health Insurance",
        "starhealth": "Star Health Insurance",
        "star health insurance": "Star Health Insurance",
        "starhealthinsurance": "Star Health Insurance",
        "star": "Star Health Insurance",
        
        # Apollo variations
        "apollo": "Apollo Munich Health Insurance",
        "apollo munich": "Apollo Munich Health Insurance",
        "apollo health": "Apollo Munich Health Insurance",
        "apollo insurance": "Apollo Munich Health Insurance",
        
        # HDFC Ergo variations
        "hdfc": "HDFC ERGO General Insurance",
        "hdfc ergo": "HDFC ERGO General Insurance",
        "hdfc insurance": "HDFC ERGO General Insurance",
        "hdfc general": "HDFC ERGO General Insurance",
        
        # ICICI Lombard variations
        "icici": "ICICI Lombard General Insurance",
        "icici lombard": "ICICI Lombard General Insurance",
        "icici insurance": "ICICI Lombard General Insurance",
        
        # Bajaj Allianz variations
        "bajaj": "Bajaj Allianz General Insurance",
        "bajaj allianz": "Bajaj Allianz General Insurance",
        "bajaj insurance": "Bajaj Allianz General Insurance",
        
        # Reliance variations
        "reliance": "Reliance General Insurance",
        "reliance general": "Reliance General Insurance",
        "reliance insurance": "Reliance General Insurance",
        
        # Max Bupa variations
        "max bupa": "Max Bupa Health Insurance",
        "max": "Max Bupa Health Insurance",
        "maxbupa": "Max Bupa Health Insurance",
        
        # Cigna variations
        "cigna": "Cigna TTK Health Insurance",
        "cigna ttk": "Cigna TTK Health Insurance",
        
        # Acko variations
        "acko": "Acko General Insurance",
        "acko insurance": "Acko General Insurance",
        
        # Digit variations
        "digit": "Go Digit General Insurance",
        "go digit": "Go Digit General Insurance",
        "godigit": "Go Digit General Insurance",
    }
    
    @classmethod
    def normalize(cls, name: str) -> Tuple[Optional[str], str, float]:
        """
        Normalize insurance company name using alias mapping.
        
        Args:
            name: Insurance company name
            
        Returns:
            Tuple of (normalized_name, original_name, confidence_score)
        """
        if not name or not isinstance(name, str):
            return None, name or "", 0.0
        
        original_name = name.strip()
        normalized = original_name.lower()
        
        # Check against aliases
        for alias, standard_name in cls.INSURANCE_ALIASES.items():
            if normalized == alias or normalized.startswith(alias + " "):
                return standard_name, original_name, 0.95
        
        # No alias match, return original with title case
        normalized = original_name.title()
        return normalized, original_name, 0.7


class AmountNormalizer:
    """Normalize amounts to decimal format"""
    
    @classmethod
    def normalize(cls, amount: Any) -> Tuple[Optional[float], str, float]:
        """
        Normalize amount to decimal format.
        
        Args:
            amount: Amount in various formats (string, int, float, etc.)
            
        Returns:
            Tuple of (normalized_amount, original_amount, confidence_score)
        """
        if amount is None:
            return None, "", 0.0
        
        original_amount = str(amount).strip()
        
        # Remove currency symbols and commas
        cleaned = re.sub(r'[₹$€£,]', '', original_amount)
        cleaned = cleaned.strip()
        
        try:
            # Try to convert to decimal
            decimal_amount = float(cleaned)
            return decimal_amount, original_amount, 1.0
        except (ValueError, InvalidOperation):
            pass
        
        # Try to extract number from text (e.g., "Rs. 5000 only")
        numbers = re.findall(r'[\d.]+', cleaned)
        if numbers:
            try:
                decimal_amount = float(numbers[0])
                return decimal_amount, original_amount, 0.8
            except ValueError:
                pass
        
        logger.warning(f"[AMOUNT_NORMALIZATION_FAILED] Could not parse: {original_amount}")
        return None, original_amount, 0.0


class TextNormalizer:
    """General text normalization"""
    
    @classmethod
    def trim(cls, text: str) -> Tuple[Optional[str], str, float]:
        """Trim whitespace from text"""
        if not text or not isinstance(text, str):
            return None, text or "", 0.0
        
        original = text
        normalized = text.strip()
        confidence = 1.0 if normalized == original else 0.95
        
        return normalized, original, confidence
    
    @classmethod
    def title_case(cls, text: str) -> Tuple[Optional[str], str, float]:
        """Convert text to title case"""
        if not text or not isinstance(text, str):
            return None, text or "", 0.0
        
        original = text
        normalized = text.strip().title()
        confidence = 1.0 if normalized == original else 0.9
        
        return normalized, original, confidence


class NormalizationEngine:
    """Main normalization engine that orchestrates all normalizers"""
    
    def __init__(self):
        self.normalizers = {
            'date': DateNormalizer,
            'doctor_name': DoctorNameNormalizer,
            'diagnosis': DiagnosisNormalizer,
            'procedure_code': ProcedureCodeNormalizer,
            'insurance_name': InsuranceNameNormalizer,
            'amount': AmountNormalizer,
            'text': TextNormalizer
        }
    
    def normalize_field(
        self,
        field_name: str,
        field_value: Any,
        field_type: str,
        document_id: str,
        hospital_id: str
    ) -> Dict[str, Any]:
        """
        Normalize a single field based on its type.
        
        Args:
            field_name: Name of the field (e.g., 'patient_name', 'diagnosis')
            field_value: Original value to normalize
            field_type: Type of field (date, text, amount, etc.)
            document_id: Document ID for tracking
            hospital_id: Hospital ID for tracking
            
        Returns:
            dict with normalization results
        """
        if field_value is None or field_value == "":
            return {
                "field_name": field_name,
                "original_value": "",
                "normalized_value": None,
                "normalization_method": "none",
                "confidence": 0.0,
                "success": False
            }
        
        # Determine normalizer based on field name and type
        normalizer_class = self._get_normalizer(field_name, field_type)
        
        if not normalizer_class:
            # No specific normalizer, use basic text trim
            normalized, original, confidence = TextNormalizer.trim(str(field_value))
            method = "text_trim"
        else:
            # Use specific normalizer
            if field_type == 'date':
                normalized, confidence = normalizer_class.normalize(str(field_value))
                original = str(field_value)
            elif field_type == 'amount':
                normalized, original, confidence = normalizer_class.normalize(field_value)
            else:
                normalized, original, confidence = normalizer_class.normalize(str(field_value))
            
            method = self._get_method_name(normalizer_class)
        
        return {
            "field_name": field_name,
            "field_type": field_type,
            "original_value": original,
            "normalized_value": normalized,
            "normalization_method": method,
            "confidence": confidence,
            "success": normalized is not None
        }
    
    def normalize_clinical_data(
        self,
        clinical_data: Dict[str, Any],
        document_id: str,
        hospital_id: str
    ) -> Dict[str, Any]:
        """
        Normalize all clinical data fields.
        
        Args:
            clinical_data: Dictionary of extracted clinical data
            document_id: Document ID for tracking
            hospital_id: Hospital ID for tracking
            
        Returns:
            dict with normalized data and normalization results
        """
        normalized_data = {}
        normalization_results = {}
        
        # Field type mapping
        field_types = {
            'admission_date': 'date',
            'discharge_date': 'date',
            'operation_date': 'date',
            'doctor': 'doctor_name',
            'diagnosis': 'diagnosis',
            'procedure': 'diagnosis',
            'insurance_company': 'insurance_name',
            'bill_amount': 'amount',
            'cpt_codes': 'procedure_code',
            'icd_codes': 'procedure_code'
        }
        
        for field_name, field_value in clinical_data.items():
            if field_value is None or field_value == "":
                normalized_data[field_name] = field_value
                continue
            
            field_type = field_types.get(field_name, 'text')
            
            # Handle array fields
            if isinstance(field_value, list):
                normalized_array = []
                for item in field_value:
                    result = self.normalize_field(field_name, item, field_type, document_id, hospital_id)
                    normalized_array.append(result['normalized_value'])
                    normalization_results[f"{field_name}_{len(normalization_results)}"] = result
                normalized_data[field_name] = normalized_array
            else:
                result = self.normalize_field(field_name, field_value, field_type, document_id, hospital_id)
                normalized_data[field_name] = result['normalized_value']
                normalization_results[field_name] = result
        
        return {
            "normalized_data": normalized_data,
            "normalization_results": normalization_results,
            "document_id": document_id,
            "hospital_id": hospital_id
        }
    
    def _get_normalizer(self, field_name: str, field_type: str):
        """Get appropriate normalizer for field"""
        if field_type == 'date':
            return DateNormalizer
        elif field_type == 'amount':
            return AmountNormalizer
        elif field_name in ['doctor', 'doctor_name']:
            return DoctorNameNormalizer
        elif field_name in ['diagnosis', 'procedure']:
            return DiagnosisNormalizer
        elif field_name in ['cpt_codes', 'icd_codes', 'procedure_code']:
            return ProcedureCodeNormalizer
        elif field_name in ['insurance_company', 'insurance']:
            return InsuranceNameNormalizer
        else:
            return None
    
    def _get_method_name(self, normalizer_class) -> str:
        """Get normalization method name from normalizer class"""
        mapping = {
            DateNormalizer: "date_iso",
            DoctorNameNormalizer: "doctor_name_clean",
            DiagnosisNormalizer: "diagnosis_standardize",
            ProcedureCodeNormalizer: "procedure_code_upper",
            InsuranceNameNormalizer: "insurance_alias",
            AmountNormalizer: "amount_decimal",
            TextNormalizer: "text_trim"
        }
        return mapping.get(normalizer_class, "custom")


# Global normalization engine instance
_normalization_engine: Optional[NormalizationEngine] = None


def get_normalization_engine() -> NormalizationEngine:
    """Get or create the global normalization engine instance"""
    global _normalization_engine
    if _normalization_engine is None:
        _normalization_engine = NormalizationEngine()
    return _normalization_engine
