import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dateutil import parser as date_parser

from app.infrastructure.db.models.claim import ValidationSeverity, ValidationCategory

logger = logging.getLogger("claim_validators")


class ValidationFinding:
    """Represents a single validation finding"""
    
    def __init__(
        self,
        severity: str,
        category: str,
        confidence: float,
        affected_document: Optional[str] = None,
        affected_field: Optional[str] = None,
        explanation: str = "",
        recommended_fix: Optional[str] = None,
        source_document_id: Optional[str] = None,
        source_page_number: Optional[int] = None,
        source_text_snippet: Optional[str] = None
    ):
        self.severity = severity
        self.category = category
        self.confidence = confidence
        self.affected_document = affected_document
        self.affected_field = affected_field
        self.explanation = explanation
        self.recommended_fix = recommended_fix
        self.source_document_id = source_document_id
        self.source_page_number = source_page_number
        self.source_text_snippet = source_text_snippet
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "confidence": self.confidence,
            "affected_document": self.affected_document,
            "affected_field": self.affected_field,
            "explanation": self.explanation,
            "recommended_fix": self.recommended_fix,
            "source_document_id": self.source_document_id,
            "source_page_number": self.source_page_number,
            "source_text_snippet": self.source_text_snippet
        }


class MissingDocumentValidator:
    """Validates that all mandatory documents are present"""
    
    # Mandatory document types for claim submission
    MANDATORY_DOCUMENTS = {
        "discharge_summary": "Discharge Summary",
        "operative_note": "Operative Note",
        "itemized_bill": "Itemized Bill",
        "insurance_card": "Insurance Card",
        "identity_proof": "Identity Proof"
    }
    
    @classmethod
    def validate(cls, documents: List[Dict[str, Any]], claim_data: Dict[str, Any]) -> List[ValidationFinding]:
        """
        Validate that all mandatory documents are present.
        
        Args:
            documents: List of uploaded documents
            claim_data: Claim data including document types
            
        Returns:
            List of validation findings
        """
        findings = []
        
        # Get present document types
        present_types = {doc.get("document_type", "").lower() for doc in documents}
        
        # Check for missing mandatory documents
        for doc_type, doc_name in cls.MANDATORY_DOCUMENTS.items():
            if doc_type not in present_types:
                findings.append(ValidationFinding(
                    severity=ValidationSeverity.CRITICAL.value,
                    category=ValidationCategory.MISSING_DOCUMENT.value,
                    confidence=1.0,
                    affected_document=doc_name,
                    affected_field="document_type",
                    explanation=f"Mandatory document '{doc_name}' is missing from the claim submission.",
                    recommended_fix=f"Upload the {doc_name} document to proceed with claim submission."
                ))
        
        logger.info(f"[MISSING_DOCUMENT_VALIDATION] Checked {len(cls.MANDATORY_DOCUMENTS)} mandatory docs, {len(findings)} missing")
        
        return findings


class MissingDiagnosisValidator:
    """Validates that diagnosis information is present and complete"""
    
    @classmethod
    def validate(cls, clinical_data: Dict[str, Any], document_id: str = None) -> List[ValidationFinding]:
        """
        Validate that diagnosis information is present.
        
        Args:
            clinical_data: Normalized clinical extraction data
            document_id: Source document ID for traceability
            
        Returns:
            List of validation findings
        """
        findings = []
        
        # Check for primary diagnosis
        diagnosis = clinical_data.get("diagnosis")
        if not diagnosis or diagnosis.strip() == "":
            findings.append(ValidationFinding(
                severity=ValidationSeverity.CRITICAL.value,
                category=ValidationCategory.MISSING_DIAGNOSIS.value,
                confidence=1.0,
                affected_document="Clinical Document",
                affected_field="diagnosis",
                explanation="Primary diagnosis is missing from the clinical data.",
                recommended_fix="Ensure the diagnosis field is properly extracted from the medical document.",
                source_document_id=document_id
            ))
        
        # Check for ICD codes
        icd_codes = clinical_data.get("icd_codes")
        if not icd_codes or icd_codes.strip() == "":
            findings.append(ValidationFinding(
                severity=ValidationSeverity.HIGH.value,
                category=ValidationCategory.MISSING_DIAGNOSIS.value,
                confidence=0.9,
                affected_document="Clinical Document",
                affected_field="icd_codes",
                explanation="ICD diagnosis codes are missing from the clinical data.",
                recommended_fix="Ensure ICD codes are present in the medical document for proper claim processing.",
                source_document_id=document_id
            ))
        
        logger.info(f"[MISSING_DIAGNOSIS_VALIDATION] Checked diagnosis data, {len(findings)} findings")
        
        return findings


class MissingSignatureValidator:
    """Validates that required signatures are present"""
    
    # Signature keywords to look for in documents
    SIGNATURE_KEYWORDS = [
        "signature",
        "signed",
        "sign",
        "authorized",
        "approved",
        "attending physician",
        "treating doctor"
    ]
    
    @classmethod
    def validate(cls, ocr_text: str, document_id: str = None, document_type: str = None) -> List[ValidationFinding]:
        """
        Validate that required signatures are present in documents.
        
        Args:
            ocr_text: OCR text from document
            document_id: Source document ID
            document_type: Type of document being validated
            
        Returns:
            List of validation findings
        """
        findings = []
        
        if not ocr_text:
            return findings
        
        text_lower = ocr_text.lower()
        
        # Check for signature presence
        signature_found = any(keyword in text_lower for keyword in cls.SIGNATURE_KEYWORDS)
        
        if not signature_found:
            findings.append(ValidationFinding(
                severity=ValidationSeverity.HIGH.value,
                category=ValidationCategory.MISSING_SIGNATURE.value,
                confidence=0.85,
                affected_document=document_type or "Document",
                affected_field="signature",
                explanation="No signature detected in the document. Required signatures may be missing.",
                recommended_fix="Ensure the document is properly signed before submission.",
                source_document_id=document_id
            ))
        
        logger.info(f"[MISSING_SIGNATURE_VALIDATION] Checked for signatures, {len(findings)} findings")
        
        return findings


class MissingAuthorizationValidator:
    """Validates that required authorizations are present"""
    
    AUTHORIZATION_KEYWORDS = [
        "authorization",
        "pre-authorization",
        "pre authorization",
        "approval",
        "approved",
        "sanctioned",
        "tpa approval",
        "insurance approval"
    ]
    
    @classmethod
    def validate(cls, clinical_data: Dict[str, Any], ocr_text: str = None, document_id: str = None) -> List[ValidationFinding]:
        """
        Validate that required authorizations are present.
        
        Args:
            clinical_data: Normalized clinical data
            ocr_text: OCR text for additional validation
            document_id: Source document ID
            
        Returns:
            List of validation findings
        """
        findings = []
        
        # Check for authorization in clinical data
        has_authorization = False
        
        # Check in OCR text if available
        if ocr_text:
            text_lower = ocr_text.lower()
            has_authorization = any(keyword in text_lower for keyword in cls.AUTHORIZATION_KEYWORDS)
        
        # For high-value claims, authorization is critical
        bill_amount = clinical_data.get("bill_amount")
        if bill_amount and float(bill_amount) > 50000:  # Threshold for high-value claims
            if not has_authorization:
                findings.append(ValidationFinding(
                    severity=ValidationSeverity.CRITICAL.value,
                    category=ValidationCategory.MISSING_AUTHORIZATION.value,
                    confidence=0.9,
                    affected_document="Claim Documents",
                    affected_field="authorization",
                    explanation=f"High-value claim (₹{bill_amount}) requires pre-authorization from insurance provider.",
                    recommended_fix="Obtain pre-authorization from the insurance provider before claim submission.",
                    source_document_id=document_id
                ))
        
        logger.info(f"[MISSING_AUTHORIZATION_VALIDATION] Checked authorization, {len(findings)} findings")
        
        return findings


class CodingInconsistencyValidator:
    """Validates coding consistency (ICD/CPT codes)"""
    
    # Basic ICD-10 pattern
    ICD_PATTERN = r'^[A-Z][0-9][A-Z0-9](?:\.[A-Z0-9])?$'
    # Basic CPT pattern (5-digit numeric)
    CPT_PATTERN = r'^\d{5}$'
    
    @classmethod
    def validate(cls, clinical_data: Dict[str, Any], document_id: str = None) -> List[ValidationFinding]:
        """
        Validate ICD and CPT coding consistency.
        
        Args:
            clinical_data: Normalized clinical data
            document_id: Source document ID
            
        Returns:
            List of validation findings
        """
        findings = []
        
        # Validate ICD codes
        icd_codes = clinical_data.get("icd_codes")
        if icd_codes:
            # Handle comma-separated codes
            codes = [code.strip() for code in str(icd_codes).split(",")]
            for code in codes:
                if not re.match(cls.ICD_PATTERN, code, re.IGNORECASE):
                    findings.append(ValidationFinding(
                        severity=ValidationSeverity.HIGH.value,
                        category=ValidationCategory.CODING_INCONSISTENCY.value,
                        confidence=0.85,
                        affected_document="Clinical Document",
                        affected_field="icd_codes",
                        explanation=f"ICD code '{code}' does not follow standard ICD-10 format.",
                        recommended_fix="Verify the ICD code format. Standard ICD-10 codes follow pattern: A00-Z99 with optional decimal.",
                        source_document_id=document_id,
                        source_text_snippet=code
                    ))
        
        # Validate CPT codes
        cpt_codes = clinical_data.get("cpt_codes")
        if cpt_codes:
            codes = [code.strip() for code in str(cpt_codes).split(",")]
            for code in codes:
                if not re.match(cls.CPT_PATTERN, code):
                    findings.append(ValidationFinding(
                        severity=ValidationSeverity.HIGH.value,
                        category=ValidationCategory.CODING_INCONSISTENCY.value,
                        confidence=0.85,
                        affected_document="Clinical Document",
                        affected_field="cpt_codes",
                        explanation=f"CPT code '{code}' does not follow standard 5-digit format.",
                        recommended_fix="Verify the CPT code format. Standard CPT codes are 5 digits.",
                        source_document_id=document_id,
                        source_text_snippet=code
                    ))
        
        # Check for diagnosis-procedure mismatch
        diagnosis = clinical_data.get("diagnosis")
        procedure = clinical_data.get("procedure")
        if diagnosis and procedure:
            # Basic check: if procedure is mentioned but no ICD codes
            if not icd_codes:
                findings.append(ValidationFinding(
                    severity=ValidationSeverity.MEDIUM.value,
                    category=ValidationCategory.CODING_INCONSISTENCY.value,
                    confidence=0.7,
                    affected_document="Clinical Document",
                    affected_field="icd_codes",
                    explanation="Procedure is documented but no ICD diagnosis codes are present.",
                    recommended_fix="Add appropriate ICD codes corresponding to the documented procedure.",
                    source_document_id=document_id
                ))
        
        logger.info(f"[CODING_INCONSISTENCY_VALIDATION] Checked coding, {len(findings)} findings")
        
        return findings


class PatientMismatchValidator:
    """Validates patient information consistency across documents"""
    
    @classmethod
    def validate(cls, clinical_data_list: List[Dict[str, Any]], claim_data: Dict[str, Any]) -> List[ValidationFinding]:
        """
        Validate patient information consistency across multiple documents.
        
        Args:
            clinical_data_list: List of clinical data from different documents
            claim_data: Master claim data
            
        Returns:
            List of validation findings
        """
        findings = []
        
        if len(clinical_data_list) < 2:
            return findings
        
        # Compare patient names across documents
        patient_names = [data.get("patient_name", "").strip().lower() for data in clinical_data_list if data.get("patient_name")]
        unique_names = set(patient_names)
        
        if len(unique_names) > 1:
            findings.append(ValidationFinding(
                severity=ValidationSeverity.CRITICAL.value,
                category=ValidationCategory.PATIENT_MISMATCH.value,
                confidence=0.95,
                affected_document="Multiple Documents",
                affected_field="patient_name",
                explanation=f"Patient name mismatch detected across documents: {', '.join(unique_names)}.",
                recommended_fix="Verify that all documents belong to the same patient. Correct patient names as needed.",
                source_text_snippet=f"Found names: {', '.join(unique_names)}"
            ))
        
        # Compare UHID/MRN across documents
        uhids = [data.get("uhid", "").strip() for data in clinical_data_list if data.get("uhid")]
        unique_uhids = set(uhids)
        
        if len(unique_uhids) > 1:
            findings.append(ValidationFinding(
                severity=ValidationSeverity.CRITICAL.value,
                category=ValidationCategory.PATIENT_MISMATCH.value,
                confidence=0.95,
                affected_document="Multiple Documents",
                affected_field="uhid",
                explanation=f"UHID mismatch detected across documents: {', '.join(unique_uhids)}.",
                recommended_fix="Verify that all documents have the correct UHID for the patient.",
                source_text_snippet=f"Found UHIDs: {', '.join(unique_uhids)}"
            ))
        
        logger.info(f"[PATIENT_MISMATCH_VALIDATION] Checked patient consistency, {len(findings)} findings")
        
        return findings


class DateInconsistencyValidator:
    """Validates date consistency across documents"""
    
    @classmethod
    def validate(cls, clinical_data: Dict[str, Any], document_id: str = None) -> List[ValidationFinding]:
        """
        Validate date consistency within clinical data.
        
        Args:
            clinical_data: Normalized clinical data
            document_id: Source document ID
            
        Returns:
            List of validation findings
        """
        findings = []
        
        admission_date = clinical_data.get("admission_date")
        discharge_date = clinical_data.get("discharge_date")
        operation_date = clinical_data.get("operation_date")
        
        # Parse dates if they're strings
        def parse_date(date_str):
            if not date_str:
                return None
            try:
                return date_parser.parse(str(date_str))
            except:
                return None
        
        admission_parsed = parse_date(admission_date)
        discharge_parsed = parse_date(discharge_date)
        operation_parsed = parse_date(operation_date)
        
        # Check admission before discharge
        if admission_parsed and discharge_parsed:
            if admission_parsed > discharge_parsed:
                findings.append(ValidationFinding(
                    severity=ValidationSeverity.CRITICAL.value,
                    category=ValidationCategory.DATE_INCONSISTENCY.value,
                    confidence=1.0,
                    affected_document="Clinical Document",
                    affected_field="admission_date",
                    explanation=f"Admission date ({admission_date}) is after discharge date ({discharge_date}).",
                    recommended_fix="Verify and correct the admission and discharge dates.",
                    source_document_id=document_id,
                    source_text_snippet=f"Admission: {admission_date}, Discharge: {discharge_date}"
                ))
        
        # Check operation date within admission period
        if operation_parsed and admission_parsed and discharge_parsed:
            if operation_parsed < admission_parsed or operation_parsed > discharge_parsed:
                findings.append(ValidationFinding(
                    severity=ValidationSeverity.HIGH.value,
                    category=ValidationCategory.DATE_INCONSISTENCY.value,
                    confidence=0.9,
                    affected_document="Clinical Document",
                    affected_field="operation_date",
                    explanation=f"Operation date ({operation_date}) is outside admission period ({admission_date} to {discharge_date}).",
                    recommended_fix="Verify the operation date falls within the admission period.",
                    source_document_id=document_id,
                    source_text_snippet=f"Operation: {operation_date}, Admission: {admission_date}, Discharge: {discharge_date}"
                ))
        
        # Check for future dates
        now = datetime.now(timezone.utc)
        for field_name, date_value in [("admission_date", admission_date), ("discharge_date", discharge_date), ("operation_date", operation_date)]:
            if date_value:
                parsed = parse_date(date_value)
                if parsed and parsed > now:
                    findings.append(ValidationFinding(
                        severity=ValidationSeverity.HIGH.value,
                        category=ValidationCategory.DATE_INCONSISTENCY.value,
                        confidence=0.95,
                        affected_document="Clinical Document",
                        affected_field=field_name,
                        explanation=f"{field_name} ({date_value}) is in the future.",
                        recommended_fix="Verify the date is correct and not a future date.",
                        source_document_id=document_id,
                        source_text_snippet=f"{field_name}: {date_value}"
                    ))
        
        logger.info(f"[DATE_INCONSISTENCY_VALIDATION] Checked date consistency, {len(findings)} findings")
        
        return findings


class DuplicateBillingValidator:
    """Validates for duplicate billing items"""
    
    @classmethod
    def validate(cls, clinical_data: Dict[str, Any], ocr_text: str = None, document_id: str = None) -> List[ValidationFinding]:
        """
        Validate for duplicate billing items.
        
        Args:
            clinical_data: Normalized clinical data
            ocr_text: OCR text for additional validation
            document_id: Source document ID
            
        Returns:
            List of validation findings
        """
        findings = []
        
        # Check for duplicate invoice numbers
        invoice_number = clinical_data.get("invoice_number")
        if invoice_number:
            # In a real implementation, this would check against a database of previous claims
            # For now, we'll check if the invoice number appears multiple times in the text
            if ocr_text:
                invoice_count = ocr_text.upper().count(str(invoice_number).upper())
                if invoice_count > 3:  # Reasonable threshold
                    findings.append(ValidationFinding(
                        severity=ValidationSeverity.HIGH.value,
                        category=ValidationCategory.DUPLICATE_BILLING.value,
                        confidence=0.7,
                        affected_document="Bill Document",
                        affected_field="invoice_number",
                        explanation=f"Invoice number '{invoice_number}' appears multiple times in the document.",
                        recommended_fix="Verify this is not a duplicate submission. Check for duplicate claims.",
                        source_document_id=document_id,
                        source_text_snippet=invoice_number
                    ))
        
        # Check for duplicate procedure codes
        cpt_codes = clinical_data.get("cpt_codes")
        if cpt_codes:
            codes = [code.strip() for code in str(cpt_codes).split(",")]
            unique_codes = set(codes)
            if len(codes) != len(unique_codes):
                findings.append(ValidationFinding(
                    severity=ValidationSeverity.MEDIUM.value,
                    category=ValidationCategory.DUPLICATE_BILLING.value,
                    confidence=0.85,
                    affected_document="Clinical Document",
                    affected_field="cpt_codes",
                    explanation=f"Duplicate CPT codes detected: {cpt_codes}",
                    recommended_fix="Remove duplicate CPT codes from the claim.",
                    source_document_id=document_id,
                    source_text_snippet=cpt_codes
                ))
        
        logger.info(f"[DUPLICATE_BILLING_VALIDATION] Checked for duplicates, {len(findings)} findings")
        
        return findings


class DocumentCompletenessValidator:
    """Validates document completeness (discharge summary, operative note)"""
    
    # Required sections in discharge summary
    DISCHARGE_SUMMARY_REQUIRED_SECTIONS = [
        "admission",
        "discharge",
        "diagnosis",
        "treatment",
        "medication"
    ]
    
    # Required sections in operative note
    OPERATIVE_NOTE_REQUIRED_SECTIONS = [
        "pre-operative",
        "procedure",
        "post-operative",
        "complications"
    ]
    
    @classmethod
    def validate(cls, ocr_text: str, document_type: str, document_id: str = None) -> List[ValidationFinding]:
        """
        Validate document completeness based on type.
        
        Args:
            ocr_text: OCR text from document
            document_type: Type of document
            document_id: Source document ID
            
        Returns:
            List of validation findings
        """
        findings = []
        
        if not ocr_text:
            return findings
        
        text_lower = ocr_text.lower()
        
        if document_type == "discharge_summary":
            missing_sections = []
            for section in cls.DISCHARGE_SUMMARY_REQUIRED_SECTIONS:
                if section not in text_lower:
                    missing_sections.append(section)
            
            if missing_sections:
                findings.append(ValidationFinding(
                    severity=ValidationSeverity.HIGH.value,
                    category=ValidationCategory.DOCUMENT_INCOMPLETE.value,
                    confidence=0.8,
                    affected_document="Discharge Summary",
                    affected_field="document_sections",
                    explanation=f"Discharge summary is missing required sections: {', '.join(missing_sections)}.",
                    recommended_fix="Ensure the discharge summary includes all required sections for complete documentation.",
                    source_document_id=document_id
                ))
        
        elif document_type == "operative_note":
            missing_sections = []
            for section in cls.OPERATIVE_NOTE_REQUIRED_SECTIONS:
                if section not in text_lower:
                    missing_sections.append(section)
            
            if missing_sections:
                findings.append(ValidationFinding(
                    severity=ValidationSeverity.HIGH.value,
                    category=ValidationCategory.DOCUMENT_INCOMPLETE.value,
                    confidence=0.8,
                    affected_document="Operative Note",
                    affected_field="document_sections",
                    explanation=f"Operative note is missing required sections: {', '.join(missing_sections)}.",
                    recommended_fix="Ensure the operative note includes all required sections for complete documentation.",
                    source_document_id=document_id
                ))
        
        logger.info(f"[DOCUMENT_COMPLETENESS_VALIDATION] Checked {document_type}, {len(findings)} findings")
        
        return findings


class MissingCredentialsValidator:
    """Validates doctor credentials are present"""
    
    CREDENTIAL_KEYWORDS = [
        "registration number",
        "medical council",
        "license",
        "qualification",
        "degrees",
        "md",
        "ms",
        "mbbs"
    ]
    
    @classmethod
    def validate(cls, clinical_data: Dict[str, Any], ocr_text: str = None, document_id: str = None) -> List[ValidationFinding]:
        """
        Validate that doctor credentials are present.
        
        Args:
            clinical_data: Normalized clinical data
            ocr_text: OCR text for additional validation
            document_id: Source document ID
            
        Returns:
            List of validation findings
        """
        findings = []
        
        # Check if doctor information is present
        doctor = clinical_data.get("doctor")
        if not doctor or doctor.strip() == "":
            findings.append(ValidationFinding(
                severity=ValidationSeverity.HIGH.value,
                category=ValidationCategory.MISSING_CREDENTIALS.value,
                confidence=0.9,
                affected_document="Clinical Document",
                affected_field="doctor",
                explanation="Attending/treating doctor information is missing.",
                recommended_fix="Ensure the attending doctor's name and credentials are documented.",
                source_document_id=document_id
            ))
        
        # Check for credentials in OCR text
        if ocr_text:
            text_lower = ocr_text.lower()
            has_credentials = any(keyword in text_lower for keyword in cls.CREDENTIAL_KEYWORDS)
            
            if not has_credentials:
                findings.append(ValidationFinding(
                    severity=ValidationSeverity.MEDIUM.value,
                    category=ValidationCategory.MISSING_CREDENTIALS.value,
                    confidence=0.7,
                    affected_document="Clinical Document",
                    affected_field="doctor_credentials",
                    explanation="Doctor credentials (registration number, qualifications) not found in document.",
                    recommended_fix="Ensure doctor's registration number and qualifications are documented.",
                    source_document_id=document_id
                ))
        
        logger.info(f"[MISSING_CREDENTIALS_VALIDATION] Checked doctor credentials, {len(findings)} findings")
        
        return findings


class MissingIdentifiersValidator:
    """Validates hospital identifiers are present"""
    
    @classmethod
    def validate(cls, clinical_data: Dict[str, Any], document_id: str = None) -> List[ValidationFinding]:
        """
        Validate that hospital identifiers are present.
        
        Args:
            clinical_data: Normalized clinical data
            document_id: Source document ID
            
        Returns:
            List of validation findings
        """
        findings = []
        
        # Check for hospital name
        hospital = clinical_data.get("hospital")
        if not hospital or hospital.strip() == "":
            findings.append(ValidationFinding(
                severity=ValidationSeverity.HIGH.value,
                category=ValidationCategory.MISSING_IDENTIFIERS.value,
                confidence=0.9,
                affected_document="Clinical Document",
                affected_field="hospital",
                explanation="Hospital name is missing from the document.",
                recommended_fix="Ensure the hospital name is clearly documented.",
                source_document_id=document_id
            ))
        
        # Check for patient identifiers
        uhid = clinical_data.get("uhid")
        mrn = clinical_data.get("mrn")
        
        if not uhid and not mrn:
            findings.append(ValidationFinding(
                severity=ValidationSeverity.HIGH.value,
                category=ValidationCategory.MISSING_IDENTIFIERS.value,
                confidence=0.9,
                affected_document="Clinical Document",
                affected_field="patient_identifiers",
                explanation="Patient identifiers (UHID/MRN) are missing from the document.",
                recommended_fix="Ensure patient UHID or MRN is documented for proper identification.",
                source_document_id=document_id
            ))
        
        logger.info(f"[MISSING_IDENTIFIERS_VALIDATION] Checked hospital identifiers, {len(findings)} findings")
        
        return findings
