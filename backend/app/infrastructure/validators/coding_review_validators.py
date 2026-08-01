import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.infrastructure.db.models.claim import CodingReviewSeverity, CodingReviewCategory

logger = logging.getLogger("coding_review_validators")


class CodingReviewFinding:
    """Represents a single coding review finding"""
    
    def __init__(
        self,
        code_type: str,
        code_value: str,
        severity: str,
        category: str,
        confidence: float,
        detected_issue: str,
        correct_coding_recommendation: Optional[str] = None,
        reference_document: Optional[str] = None,
        expected_financial_impact: Optional[float] = None,
        modifier: Optional[str] = None,
        medical_evidence: Optional[Dict[str, Any]] = None,
        evidence_source_document_id: Optional[str] = None,
        evidence_text_snippet: Optional[str] = None,
        evidence_page_number: Optional[int] = None
    ):
        self.code_type = code_type
        self.code_value = code_value
        self.modifier = modifier
        self.severity = severity
        self.category = category
        self.confidence = confidence
        self.detected_issue = detected_issue
        self.correct_coding_recommendation = correct_coding_recommendation
        self.reference_document = reference_document
        self.expected_financial_impact = expected_financial_impact
        self.medical_evidence = medical_evidence
        self.evidence_source_document_id = evidence_source_document_id
        self.evidence_text_snippet = evidence_text_snippet
        self.evidence_page_number = evidence_page_number
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code_type": self.code_type,
            "code_value": self.code_value,
            "modifier": self.modifier,
            "severity": self.severity,
            "category": self.category,
            "confidence": self.confidence,
            "detected_issue": self.detected_issue,
            "correct_coding_recommendation": self.correct_coding_recommendation,
            "reference_document": self.reference_document,
            "expected_financial_impact": self.expected_financial_impact,
            "medical_evidence": self.medical_evidence,
            "evidence_source_document_id": self.evidence_source_document_id,
            "evidence_text_snippet": self.evidence_text_snippet,
            "evidence_page_number": self.evidence_page_number
        }


class ICDCodeValidator:
    """Validates ICD codes for validity and deleted codes"""
    
    # Sample ICD-10 valid code patterns (in production, this would be a comprehensive database)
    ICD_10_PATTERN = r'^[A-Z][0-9][A-Z0-9](?:\.[A-Z0-9]{1,4})?$'
    
    # Sample deleted/invalid codes (in production, this would be from official ICD database)
    DELETED_ICD_CODES = {
        # Example deleted codes - in production, use official WHO database
        "V87.0",  # Deleted in ICD-10
        "E950.0"  # Example deleted code
    }
    
    @classmethod
    def validate(
        cls,
        icd_codes: List[str],
        clinical_data: Dict[str, Any],
        document_id: str = None
    ) -> List[CodingReviewFinding]:
        """
        Validate ICD codes.
        
        Args:
            icd_codes: List of ICD codes to validate
            clinical_data: Normalized clinical data for evidence
            document_id: Source document ID
            
        Returns:
            List of coding review findings
        """
        findings = []
        
        for code in icd_codes:
            code = code.strip().upper()
            
            # Check code format
            if not re.match(cls.ICD_10_PATTERN, code):
                findings.append(CodingReviewFinding(
                    code_type="ICD",
                    code_value=code,
                    severity=CodingReviewSeverity.CRITICAL.value,
                    category=CodingReviewCategory.INVALID_CODE.value,
                    confidence=0.95,
                    detected_issue=f"ICD code '{code}' does not follow valid ICD-10 format.",
                    correct_coding_recommendation="Verify the ICD code format. Valid ICD-10 codes follow pattern: A00-Z99 with optional decimal.",
                    reference_document="ICD-10-CM Official Guidelines",
                    expected_financial_impact=-5000.0,  # Estimated claim denial impact
                    medical_evidence={
                        "extracted_code": code,
                        "diagnosis_text": clinical_data.get("diagnosis", "")
                    },
                    evidence_source_document_id=document_id,
                    evidence_text_snippet=clinical_data.get("diagnosis", "")[:200]
                ))
                continue
            
            # Check for deleted codes
            if code in cls.DELETED_ICD_CODES:
                findings.append(CodingReviewFinding(
                    code_type="ICD",
                    code_value=code,
                    severity=CodingReviewSeverity.CRITICAL.value,
                    category=CodingReviewCategory.DELETED_CODE.value,
                    confidence=1.0,
                    detected_issue=f"ICD code '{code}' has been deleted and is no longer valid.",
                    correct_coding_recommendation="Use the current valid ICD code for this diagnosis. Refer to ICD-10-CM official coding guidelines.",
                    reference_document="ICD-10-CM Official Guidelines",
                    expected_financial_impact=-10000.0,  # Claim denial impact
                    medical_evidence={
                        "extracted_code": code,
                        "diagnosis_text": clinical_data.get("diagnosis", "")
                    },
                    evidence_source_document_id=document_id,
                    evidence_text_snippet=clinical_data.get("diagnosis", "")[:200]
                ))
        
        logger.info(f"[ICD_VALIDATION] Reviewed {len(icd_codes)} codes, {len(findings)} findings")
        
        return findings


class CPTCodeValidator:
    """Validates CPT codes for validity and modifiers"""
    
    # CPT code pattern (5 digits)
    CPT_PATTERN = r'^\d{5}$'
    
    # Sample valid CPT code ranges (in production, use AMA CPT database)
    VALID_CPT_RANGES = [
        (10000, 69999),  # Surgery
        (70000, 79999),  # Radiology
        (80000, 89999),  # Pathology/Laboratory
        (90000, 99999),  # Medicine
        (99201, 99499),  # Evaluation and Management
    ]
    
    # Common CPT modifiers
    COMMON_MODIFIERS = {
        "25": "Significant, separately identifiable evaluation and management service",
        "50": "Bilateral procedure",
        "51": "Multiple procedures",
        "52": "Reduced services",
        "59": "Distinct procedural service",
        "76": "Repeat procedure by same physician",
        "77": "Repeat procedure by another physician",
        "78": "Unplanned return to operating/procedure room",
        "79": "Unrelated procedure by same physician",
        "80": "Unrelated procedure by different physician",
        "91": "Repeat clinical diagnostic laboratory test",
        "99": "Multiple modifiers"
    }
    
    @classmethod
    def validate(
        cls,
        cpt_codes: List[str],
        clinical_data: Dict[str, Any],
        document_id: str = None
    ) -> List[CodingReviewFinding]:
        """
        Validate CPT codes and modifiers.
        
        Args:
            cpt_codes: List of CPT codes (may include modifiers)
            clinical_data: Normalized clinical data for evidence
            document_id: Source document ID
            
        Returns:
            List of coding review findings
        """
        findings = []
        
        for code_entry in cpt_codes:
            # Parse code and modifier (format: "12345" or "12345-25")
            if "-" in str(code_entry):
                code, modifier = str(code_entry).split("-", 1)
                code = code.strip()
                modifier = modifier.strip()
            else:
                code = str(code_entry).strip()
                modifier = None
            
            # Check code format
            if not re.match(cls.CPT_PATTERN, code):
                findings.append(CodingReviewFinding(
                    code_type="CPT",
                    code_value=code,
                    modifier=modifier,
                    severity=CodingReviewSeverity.CRITICAL.value,
                    category=CodingReviewCategory.INVALID_CODE.value,
                    confidence=0.95,
                    detected_issue=f"CPT code '{code}' does not follow valid 5-digit format.",
                    correct_coding_recommendation="Verify the CPT code. Valid CPT codes are 5 digits.",
                    reference_document="AMA CPT Codebook",
                    expected_financial_impact=-8000.0,
                    medical_evidence={
                        "extracted_code": code,
                        "procedure_text": clinical_data.get("procedure", "")
                    },
                    evidence_source_document_id=document_id,
                    evidence_text_snippet=clinical_data.get("procedure", "")[:200]
                ))
                continue
            
            # Check if code is in valid range
            code_num = int(code)
            is_valid_range = any(low <= code_num <= high for low, high in cls.VALID_CPT_RANGES)
            
            if not is_valid_range:
                findings.append(CodingReviewFinding(
                    code_type="CPT",
                    code_value=code,
                    modifier=modifier,
                    severity=CodingReviewSeverity.HIGH.value,
                    category=CodingReviewCategory.INVALID_CODE.value,
                    confidence=0.8,
                    detected_issue=f"CPT code '{code}' is not in a valid CPT code range.",
                    correct_coding_recommendation="Verify the CPT code is current and valid. Refer to AMA CPT Codebook.",
                    reference_document="AMA CPT Codebook",
                    expected_financial_impact=-6000.0,
                    medical_evidence={
                        "extracted_code": code,
                        "procedure_text": clinical_data.get("procedure", "")
                    },
                    evidence_source_document_id=document_id,
                    evidence_text_snippet=clinical_data.get("procedure", "")[:200]
                ))
            
            # Check modifier validity
            if modifier and modifier not in cls.COMMON_MODIFIERS:
                findings.append(CodingReviewFinding(
                    code_type="CPT",
                    code_value=code,
                    modifier=modifier,
                    severity=CodingReviewSeverity.MEDIUM.value,
                    category=CodingReviewCategory.MODIFIER_ISSUE.value,
                    confidence=0.7,
                    detected_issue=f"Modifier '{modifier}' is not a recognized CPT modifier.",
                    correct_coding_recommendation=f"Verify modifier '{modifier}' is appropriate. Common modifiers: {', '.join(list(cls.COMMON_MODIFIERS.keys())[:5])}...",
                    reference_document="AMA CPT Modifiers Guidelines",
                    expected_financial_impact=-2000.0,
                    medical_evidence={
                        "extracted_code": code,
                        "modifier": modifier,
                        "procedure_text": clinical_data.get("procedure", "")
                    },
                    evidence_source_document_id=document_id,
                    evidence_text_snippet=clinical_data.get("procedure", "")[:200]
                ))
        
        logger.info(f"[CPT_VALIDATION] Reviewed {len(cpt_codes)} codes, {len(findings)} findings")
        
        return findings


class CodeCombinationValidator:
    """Validates code combinations for conflicts and incompatibilities"""
    
    # Mutually exclusive code pairs (simplified for demo)
    MUTUALLY_EXCLUSIVE_PAIRS = [
        ("47562", "47563"),  # Laparoscopic cholecystectomy variants
        ("19120", "19125"),  # Breast excision variants
    ]
    
    # Codes that cannot be billed together
    INCOMPATIBLE_COMBINATIONS = [
        ("99213", "99214"),  # Different E/M levels for same encounter
        ("99214", "99215"),
    ]
    
    @classmethod
    def validate(
        cls,
        cpt_codes: List[str],
        clinical_data: Dict[str, Any],
        document_id: str = None
    ) -> List[CodingReviewFinding]:
        """
        Validate code combinations.
        
        Args:
            cpt_codes: List of CPT codes
            clinical_data: Normalized clinical data for evidence
            document_id: Source document ID
            
        Returns:
            List of coding review findings
        """
        findings = []
        
        # Extract clean codes (remove modifiers)
        clean_codes = []
        for code_entry in cpt_codes:
            if "-" in str(code_entry):
                clean_codes.append(str(code_entry).split("-")[0].strip())
            else:
                clean_codes.append(str(code_entry).strip())
        
        # Check for mutually exclusive pairs
        for code1, code2 in cls.MUTUALLY_EXCLUSIVE_PAIRS:
            if code1 in clean_codes and code2 in clean_codes:
                findings.append(CodingReviewFinding(
                    code_type="CPT",
                    code_value=f"{code1}+{code2}",
                    severity=CodingReviewSeverity.CRITICAL.value,
                    category=CodingReviewCategory.CODE_COMBINATION.value,
                    confidence=0.9,
                    detected_issue=f"CPT codes {code1} and {code2} are mutually exclusive and cannot be billed together.",
                    correct_coding_recommendation=f"Choose the most appropriate code between {code1} and {code2} based on the procedure performed.",
                    reference_document="CPT Codebook - Mutually Exclusive Rules",
                    expected_financial_impact=-12000.0,
                    medical_evidence={
                        "conflicting_codes": [code1, code2],
                        "procedure_text": clinical_data.get("procedure", "")
                    },
                    evidence_source_document_id=document_id,
                    evidence_text_snippet=clinical_data.get("procedure", "")[:200]
                ))
        
        # Check for incompatible combinations
        for code1, code2 in cls.INCOMPATIBLE_COMBINATIONS:
            if code1 in clean_codes and code2 in clean_codes:
                findings.append(CodingReviewFinding(
                    code_type="CPT",
                    code_value=f"{code1}+{code2}",
                    severity=CodingReviewSeverity.HIGH.value,
                    category=CodingReviewCategory.CODE_COMBINATION.value,
                    confidence=0.85,
                    detected_issue=f"CPT codes {code1} and {code2} represent different service levels and should not be billed together for the same encounter.",
                    correct_coding_recommendation=f"Select the appropriate single E/M code based on the complexity of the encounter.",
                    reference_document="CPT E/M Guidelines",
                    expected_financial_impact=-4000.0,
                    medical_evidence={
                        "conflicting_codes": [code1, code2],
                        "procedure_text": clinical_data.get("procedure", "")
                    },
                    evidence_source_document_id=document_id,
                    evidence_text_snippet=clinical_data.get("procedure", "")[:200]
                ))
        
        logger.info(f"[CODE_COMBINATION_VALIDATION] Reviewed combinations, {len(findings)} findings")
        
        return findings


class DiagnosisProcedureCompatibilityValidator:
    """Validates diagnosis-procedure compatibility"""
    
    # Sample diagnosis-procedure mappings (in production, use comprehensive database)
    DIAGNOSIS_PROCEDURE_MAP = {
        # Cholecystitis -> Cholecystectomy
        "K80": ["47562", "47563", "47564"],
        # Appendicitis -> Appendectomy
        "K35": ["44950", "44960"],
        # Cataract -> Cataract extraction
        "H25": ["66982", "66984"],
        # Hernia -> Hernia repair
        "K40": ["49505", "49507"],
    }
    
    @classmethod
    def validate(
        cls,
        icd_codes: List[str],
        cpt_codes: List[str],
        clinical_data: Dict[str, Any],
        document_id: str = None
    ) -> List[CodingReviewFinding]:
        """
        Validate diagnosis-procedure compatibility.
        
        Args:
            icd_codes: List of ICD codes
            cpt_codes: List of CPT codes
            clinical_data: Normalized clinical data for evidence
            document_id: Source document ID
            
        Returns:
            List of coding review findings
        """
        findings = []
        
        # Extract clean CPT codes
        clean_cpt_codes = []
        for code_entry in cpt_codes:
            if "-" in str(code_entry):
                clean_cpt_codes.append(str(code_entry).split("-")[0].strip())
            else:
                clean_cpt_codes.append(str(code_entry).strip())
        
        # Extract ICD code base (first 3 characters before decimal)
        icd_bases = [code.split(".")[0] for code in icd_codes]
        
        # Check for compatible procedures
        for icd_base in icd_bases:
            if icd_base in cls.DIAGNOSIS_PROCEDURE_MAP:
                expected_procedures = cls.DIAGNOSIS_PROCEDURE_MAP[icd_base]
                has_compatible_procedure = any(cpt in clean_cpt_codes for cpt in expected_procedures)
                
                if not has_compatible_procedure and clean_cpt_codes:
                    findings.append(CodingReviewFinding(
                        code_type="ICD-CPT",
                        code_value=icd_base,
                        severity=CodingReviewSeverity.HIGH.value,
                        category=CodingReviewCategory.DIAGNOSIS_PROCEDURE_MISMATCH.value,
                        confidence=0.75,
                        detected_issue=f"Diagnosis ICD-{icd_base} does not have a compatible procedure code. Expected procedures: {', '.join(expected_procedures)}.",
                        correct_coding_recommendation=f"Verify the procedure codes match the diagnosis. Consider adding appropriate procedure codes or reviewing the diagnosis.",
                        reference_document="ICD-10-CM Official Guidelines - Coding Conventions",
                        expected_financial_impact=-7000.0,
                        medical_evidence={
                            "diagnosis_code": icd_base,
                            "diagnosis_text": clinical_data.get("diagnosis", ""),
                            "procedure_codes": clean_cpt_codes,
                            "expected_procedures": expected_procedures
                        },
                        evidence_source_document_id=document_id,
                        evidence_text_snippet=f"Diagnosis: {clinical_data.get('diagnosis', '')[:100]}... Procedure: {clinical_data.get('procedure', '')[:100]}"
                    ))
        
        logger.info(f"[DX_PROC_COMPATIBILITY] Reviewed {len(icd_codes)} diagnoses, {len(findings)} findings")
        
        return findings


class BundlingValidator:
    """Validates for bundling issues"""
    
    # Bundled code pairs (component code cannot be billed with comprehensive code)
    BUNDLED_PAIRS = [
        ("47562", "47563"),  # Laparoscopic cholecystectomy components
        ("19120", "19125"),  # Breast excision components
        ("49505", "49507"),  # Hernia repair components
    ]
    
    @classmethod
    def validate(
        cls,
        cpt_codes: List[str],
        clinical_data: Dict[str, Any],
        document_id: str = None
    ) -> List[CodingReviewFinding]:
        """
        Validate for bundling issues.
        
        Args:
            cpt_codes: List of CPT codes
            clinical_data: Normalized clinical data for evidence
            document_id: Source document ID
            
        Returns:
            List of coding review findings
        """
        findings = []
        
        # Extract clean codes
        clean_codes = []
        for code_entry in cpt_codes:
            if "-" in str(code_entry):
                clean_codes.append(str(code_entry).split("-")[0].strip())
            else:
                clean_codes.append(str(code_entry).strip())
        
        # Check for bundled pairs
        for comprehensive, component in cls.BUNDLED_PAIRS:
            if comprehensive in clean_codes and component in clean_codes:
                findings.append(CodingReviewFinding(
                    code_type="CPT",
                    code_value=f"{comprehensive}+{component}",
                    severity=CodingReviewSeverity.HIGH.value,
                    category=CodingReviewCategory.BUNDLING_ISSUE.value,
                    confidence=0.9,
                    detected_issue=f"CPT code {component} is bundled into {comprehensive} and cannot be billed separately.",
                    correct_coding_recommendation=f"Remove the component code {component} as it is included in the comprehensive code {comprehensive}.",
                    reference_document="CPT Codebook - Bundling Rules",
                    expected_financial_impact=-5000.0,
                    medical_evidence={
                        "comprehensive_code": comprehensive,
                        "component_code": component,
                        "procedure_text": clinical_data.get("procedure", "")
                    },
                    evidence_source_document_id=document_id,
                    evidence_text_snippet=clinical_data.get("procedure", "")[:200]
                ))
        
        logger.info(f"[BUNDLING_VALIDATION] Reviewed bundling, {len(findings)} findings")
        
        return findings


class MedicalNecessityValidator:
    """Validates medical necessity for procedures"""
    
    # Procedures requiring specific documentation for medical necessity
    MEDICAL_NECESSITY_REQUIREMENTS = {
        "47562": {
            "required_diagnosis": ["K80", "K81"],  # Cholecystitis, Cholelithiasis
            "required_evidence": ["ultrasound", "gallbladder", "stones", "inflammation"],
            "documentation": "Pre-operative imaging showing gallstones and inflammation"
        },
        "49505": {
            "required_diagnosis": ["K40"],  # Hernia
            "required_evidence": ["hernia", "bulge", "pain", "discomfort"],
            "documentation": "Physical examination findings documenting hernia"
        }
    }
    
    @classmethod
    def validate(
        cls,
        cpt_codes: List[str],
        icd_codes: List[str],
        clinical_data: Dict[str, Any],
        ocr_text: str = None,
        document_id: str = None
    ) -> List[CodingReviewFinding]:
        """
        Validate medical necessity for procedures.
        
        Args:
            cpt_codes: List of CPT codes
            icd_codes: List of ICD codes
            clinical_data: Normalized clinical data
            ocr_text: OCR text for evidence search
            document_id: Source document ID
            
        Returns:
            List of coding review findings
        """
        findings = []
        
        # Extract clean CPT codes
        clean_cpt_codes = []
        for code_entry in cpt_codes:
            if "-" in str(code_entry):
                clean_cpt_codes.append(str(code_entry).split("-")[0].strip())
            else:
                clean_cpt_codes.append(str(code_entry).strip())
        
        # Extract ICD code bases
        icd_bases = [code.split(".")[0] for code in icd_codes]
        
        # Check medical necessity for each procedure
        for cpt_code in clean_cpt_codes:
            if cpt_code in cls.MEDICAL_NECESSITY_REQUIREMENTS:
                requirements = cls.MEDICAL_NECESSITY_REQUIREMENTS[cpt_code]
                required_diagnoses = requirements["required_diagnosis"]
                required_evidence = requirements["required_evidence"]
                
                # Check if required diagnosis is present
                has_required_diagnosis = any(dx in icd_bases for dx in required_diagnoses)
                
                if not has_required_diagnosis:
                    findings.append(CodingReviewFinding(
                        code_type="CPT",
                        code_value=cpt_code,
                        severity=CodingReviewSeverity.HIGH.value,
                        category=CodingReviewCategory.MEDICAL_NECESSITY.value,
                        confidence=0.8,
                        detected_issue=f"CPT code {cpt_code} lacks medical necessity documentation. Required diagnosis not found.",
                        correct_coding_recommendation=f"Add appropriate diagnosis code from {required_diagnoses} or provide additional documentation supporting medical necessity.",
                        reference_document="Medicare Coverage Guidelines",
                        expected_financial_impact=-15000.0,
                        medical_evidence={
                            "procedure_code": cpt_code,
                            "required_diagnoses": required_diagnoses,
                            "found_diagnoses": icd_bases,
                            "diagnosis_text": clinical_data.get("diagnosis", "")
                        },
                        evidence_source_document_id=document_id,
                        evidence_text_snippet=clinical_data.get("diagnosis", "")[:200]
                    ))
                    continue
                
                # Check for required evidence in OCR text
                if ocr_text:
                    ocr_lower = ocr_text.lower()
                    evidence_found = any(evidence in ocr_lower for evidence in required_evidence)
                    
                    if not evidence_found:
                        findings.append(CodingReviewFinding(
                            code_type="CPT",
                            code_value=cpt_code,
                            severity=CodingReviewSeverity.MEDIUM.value,
                            category=CodingReviewCategory.MEDICAL_NECESSITY.value,
                            confidence=0.7,
                            detected_issue=f"CPT code {cpt_code} may lack sufficient documentation. Required: {requirements['documentation']}.",
                            correct_coding_recommendation=f"Ensure documentation includes: {requirements['documentation']}",
                            reference_document="Medicare Coverage Guidelines",
                            expected_financial_impact=-3000.0,
                            medical_evidence={
                                "procedure_code": cpt_code,
                                "required_evidence": required_evidence,
                                "evidence_found": False,
                                "diagnosis_text": clinical_data.get("diagnosis", "")
                            },
                            evidence_source_document_id=document_id,
                            evidence_text_snippet=ocr_text[:300] if ocr_text else ""
                        ))
        
        logger.info(f"[MEDICAL_NECESSITY_VALIDATION] Reviewed {len(clean_cpt_codes)} procedures, {len(findings)} findings")
        
        return findings
