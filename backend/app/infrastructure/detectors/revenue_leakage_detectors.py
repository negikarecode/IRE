import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.infrastructure.db.models.claim import RevenueLeakageCategory

logger = logging.getLogger("revenue_leakage_detectors")


class LeakageFinding:
    """Represents a single revenue leakage finding"""
    
    def __init__(
        self,
        category: str,
        confidence: float,
        estimated_recoverable_revenue: Optional[float],
        description: str,
        recommended_correction: str,
        supporting_evidence: Dict[str, Any] = None,
        affected_document: Optional[str] = None,
        affected_code: Optional[str] = None,
        source_document_id: Optional[str] = None,
        source_text_snippet: Optional[str] = None
    ):
        self.category = category
        self.confidence = confidence
        self.estimated_recoverable_revenue = estimated_recoverable_revenue
        self.description = description
        self.recommended_correction = recommended_correction
        self.supporting_evidence = supporting_evidence or {}
        self.affected_document = affected_document
        self.affected_code = affected_code
        self.source_document_id = source_document_id
        self.source_text_snippet = source_text_snippet
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "estimated_recoverable_revenue": self.estimated_recoverable_revenue,
            "description": self.description,
            "recommended_correction": self.recommended_correction,
            "supporting_evidence": self.supporting_evidence,
            "affected_document": self.affected_document,
            "affected_code": self.affected_code,
            "source_document_id": self.source_document_id,
            "source_text_snippet": self.source_text_snippet
        }


class UnderbillingDetector:
    """Detects underbilling issues"""
    
    # Standard procedure costs (simplified - in production, use comprehensive database)
    STANDARD_PROCEDURE_COSTS = {
        "47562": 45000,  # Laparoscopic cholecystectomy
        "47563": 55000,  # Laparoscopic cholecystectomy with cholangiography
        "49505": 35000,  # Hernia repair
        "49507": 45000,  # Hernia repair with mesh
        "19120": 25000,  # Breast excision
        "19125": 35000,  # Breast excision with lymph node removal
        "66982": 40000,  # Cataract extraction
        "66984": 50000,  # Cataract extraction with IOL
    }
    
    @classmethod
    def detect(cls, clinical_data: Dict[str, Any], claim_amount: Any = None, document_id: str = None) -> List[LeakageFinding]:
        """
        Detect underbilling issues.
        
        Args:
            clinical_data: Normalized clinical data
            claim_amount: Claim amount for comparison
            document_id: Source document ID
            
        Returns:
            List of leakage findings
        """
        findings = []
        
        cpt_codes = clinical_data.get("cpt_codes", "")
        if not cpt_codes:
            return findings
        
        # Parse CPT codes
        codes = [code.strip() for code in str(cpt_codes).split(",")]
        
        for code in codes:
            # Extract base code (remove modifiers)
            base_code = code.split("-")[0].strip() if "-" in code else code
            
            if base_code in cls.STANDARD_PROCEDURE_COSTS:
                standard_cost = cls.STANDARD_PROCEDURE_COSTS[base_code]
                
                # If claim amount is provided, compare
                if claim_amount:
                    try:
                        amount = float(claim_amount)
                        # Simple check: if claim amount is significantly lower than standard cost
                        if amount < standard_cost * 0.5:  # 50% threshold
                            recoverable = standard_cost - amount
                            findings.append(LeakageFinding(
                                category=RevenueLeakageCategory.UNDERBILLING.value,
                                confidence=0.7,
                                estimated_recoverable_revenue=recoverable,
                                description=f"Claim amount (₹{amount}) appears significantly underbilled for procedure {base_code}. Standard cost: ₹{standard_cost}.",
                                recommended_correction=f"Review claim amount for procedure {base_code}. Consider increasing to standard rate of ₹{standard_cost}.",
                                supporting_evidence={
                                    "procedure_code": base_code,
                                    "claimed_amount": amount,
                                    "standard_cost": standard_cost,
                                    "variance": standard_cost - amount,
                                    "variance_percentage": ((standard_cost - amount) / standard_cost) * 100
                                },
                                affected_code=base_code,
                                source_document_id=document_id
                            ))
                    except (ValueError, TypeError):
                        pass
        
        logger.info(f"[UNDERBILLING_DETECTION] Reviewed {len(codes)} codes, {len(findings)} findings")
        
        return findings


class MissingProcedureDetector:
    """Detects missing procedures based on clinical evidence"""
    
    # Procedure-diagnosis mappings
    PROCEDURE_DIAGNOSIS_MAP = {
        "K80": ["47562", "47563"],  # Cholecystitis -> Cholecystectomy
        "K35": ["44950", "44960"],  # Appendicitis -> Appendectomy
        "H25": ["66982", "66984"],  # Cataract -> Cataract extraction
        "K40": ["49505", "49507"],  # Hernia -> Hernia repair
        "I21": ["92941", "92942"],  # MI -> Cardiac catheterization
    }
    
    # Procedure costs for revenue estimation
    PROCEDURE_COSTS = {
        "47562": 45000,
        "47563": 55000,
        "44950": 30000,
        "44960": 40000,
        "66982": 40000,
        "66984": 50000,
        "49505": 35000,
        "49507": 45000,
        "92941": 35000,
        "92942": 45000,
    }
    
    @classmethod
    def detect(cls, clinical_data: Dict[str, Any], ocr_text: str = None, document_id: str = None) -> List[LeakageFinding]:
        """
        Detect missing procedures based on clinical evidence.
        
        Args:
            clinical_data: Normalized clinical data
            ocr_text: OCR text for additional evidence
            document_id: Source document ID
            
        Returns:
            List of leakage findings
        """
        findings = []
        
        icd_codes = clinical_data.get("icd_codes", "")
        cpt_codes = clinical_data.get("cpt_codes", "")
        procedure_text = clinical_data.get("procedure", "")
        
        if not icd_codes:
            return findings
        
        # Parse ICD codes
        icd_bases = [code.split(".")[0] for code in str(icd_codes).split(",")]
        
        # Parse CPT codes
        cpt_list = []
        if cpt_codes:
            cpt_list = [code.split("-")[0].strip() if "-" in code else code.strip() for code in str(cpt_codes).split(",")]
        
        # Check for missing procedures based on diagnosis
        for icd_base in icd_bases:
            if icd_base in cls.PROCEDURE_DIAGNOSIS_MAP:
                expected_procedures = cls.PROCEDURE_DIAGNOSIS_MAP[icd_base]
                has_procedure = any(cpt in cpt_list for cpt in expected_procedures)
                
                # Also check OCR text for procedure evidence
                procedure_mentioned = False
                if ocr_text and procedure_text:
                    ocr_lower = ocr_text.lower()
                    procedure_lower = procedure_text.lower()
                    # Check if procedure is mentioned in text
                    for proc in expected_procedures:
                        if str(proc) in ocr_lower or "surgery" in ocr_lower or "operation" in ocr_lower:
                            procedure_mentioned = True
                            break
                
                if not has_procedure and (procedure_mentioned or procedure_text):
                    # Calculate potential revenue loss
                    potential_revenue = sum(cls.PROCEDURE_COSTS.get(proc, 0) for proc in expected_procedures)
                    
                    findings.append(LeakageFinding(
                        category=RevenueLeakageCategory.MISSING_PROCEDURE.value,
                        confidence=0.75,
                        estimated_recoverable_revenue=potential_revenue,
                        description=f"Diagnosis ICD-{icd_base} suggests procedure(s) {', '.join(expected_procedures)} but no corresponding CPT codes found. Procedure documented in clinical notes.",
                        recommended_correction=f"Add appropriate CPT code(s) from {', '.join(expected_procedures)} based on the documented procedure.",
                        supporting_evidence={
                            "diagnosis_code": icd_base,
                            "expected_procedures": expected_procedures,
                            "found_procedures": cpt_list,
                            "procedure_text": procedure_text,
                            "potential_revenue": potential_revenue
                        },
                        affected_document="Clinical Document",
                        source_document_id=document_id,
                        source_text_snippet=procedure_text[:200] if procedure_text else ""
                    ))
        
        logger.info(f"[MISSING_PROCEDURE_DETECTION] Reviewed {len(icd_bases)} diagnoses, {len(findings)} findings")
        
        return findings


class MissingModifierDetector:
    """Detects missing modifiers that could increase reimbursement"""
    
    # Modifiers that increase reimbursement
    REVENUE_INCREASING_MODIFIERS = {
        "50": {"description": "Bilateral procedure", "multiplier": 1.5},
        "51": {"description": "Multiple procedures", "multiplier": 1.2},
        "22": {"description": "Increased procedural services", "multiplier": 1.3},
        "62": {"description": "Two surgeons", "multiplier": 1.5},
    }
    
    # Procedures commonly requiring modifiers
    PROCEDURES_REQUIRING_MODIFIERS = {
        "19120": ["50"],  # Breast excision often bilateral
        "19125": ["50"],
        "49505": ["50"],  # Hernia repair often bilateral
        "49507": ["50"],
    }
    
    @classmethod
    def detect(cls, clinical_data: Dict[str, Any], ocr_text: str = None, document_id: str = None) -> List[LeakageFinding]:
        """
        Detect missing modifiers.
        
        Args:
            clinical_data: Normalized clinical data
            ocr_text: OCR text for evidence
            document_id: Source document ID
            
        Returns:
            List of leakage findings
        """
        findings = []
        
        cpt_codes = clinical_data.get("cpt_codes", "")
        if not cpt_codes:
            return findings
        
        # Parse CPT codes with modifiers
        code_entries = []
        for code_entry in str(cpt_codes).split(","):
            code_entry = code_entry.strip()
            if "-" in code_entry:
                code, modifier = code_entry.split("-", 1)
                code_entries.append({"code": code.strip(), "modifier": modifier.strip()})
            else:
                code_entries.append({"code": code_entry.strip(), "modifier": None})
        
        # Check for procedures that commonly require modifiers
        for entry in code_entries:
            code = entry["code"]
            current_modifier = entry["modifier"]
            
            if code in cls.PROCEDURES_REQUIRING_MODIFIERS:
                required_modifiers = cls.PROCEDURES_REQUIRING_MODIFIERS[code]
                
                for required_mod in required_modifiers:
                    if current_modifier != required_mod:
                        # Check OCR text for bilateral evidence
                        bilateral_evidence = False
                        if ocr_text:
                            ocr_lower = ocr_text.lower()
                            bilateral_keywords = ["bilateral", "both sides", "left and right", "two"]
                            bilateral_evidence = any(keyword in ocr_lower for keyword in bilateral_keywords)
                        
                        if bilateral_evidence:
                            mod_info = cls.REVENUE_INCREASING_MODIFIERS[required_mod]
                            # Estimate revenue increase (simplified)
                            base_cost = 30000  # Placeholder
                            potential_increase = base_cost * (mod_info["multiplier"] - 1)
                            
                            findings.append(LeakageFinding(
                                category=RevenueLeakageCategory.MISSING_MODIFIER.value,
                                confidence=0.7,
                                estimated_recoverable_revenue=potential_increase,
                                description=f"Procedure {code} appears to be bilateral based on clinical documentation but modifier {required_mod} ({mod_info['description']}) is missing.",
                                recommended_correction=f"Add modifier {required_mod} to CPT code {code} to indicate bilateral procedure and increase reimbursement.",
                                supporting_evidence={
                                    "procedure_code": code,
                                    "current_modifier": current_modifier,
                                    "recommended_modifier": required_mod,
                                    "modifier_description": mod_info["description"],
                                    "revenue_multiplier": mod_info["multiplier"],
                                    "estimated_increase": potential_increase,
                                    "bilateral_evidence": bilateral_evidence
                                },
                                affected_code=code,
                                source_document_id=document_id,
                                source_text_snippet=ocr_text[:200] if ocr_text else ""
                            ))
        
        logger.info(f"[MISSING_MODIFIER_DETECTION] Reviewed {len(code_entries)} codes, {len(findings)} findings")
        
        return findings


class MissedDiagnosisDetector:
    """Detects missed diagnoses that could affect reimbursement"""
    
    # Common secondary diagnoses that increase reimbursement
    COMORBIDITY_DIAGNOSES = {
        "E11": {"description": "Type 2 diabetes", "revenue_impact": 5000},
        "I10": {"description": "Hypertension", "revenue_impact": 3000},
        "E78": {"description": "Hyperlipidemia", "revenue_impact": 2000},
        "I50": {"description": "Heart failure", "revenue_impact": 8000},
        "J44": {"description": "COPD", "revenue_impact": 6000},
    }
    
    @classmethod
    def detect(cls, clinical_data: Dict[str, Any], ocr_text: str = None, document_id: str = None) -> List[LeakageFinding]:
        """
        Detect missed comorbidities.
        
        Args:
            clinical_data: Normalized clinical data
            ocr_text: OCR text for evidence
            document_id: Source document ID
            
        Returns:
            List of leakage findings
        """
        findings = []
        
        icd_codes = clinical_data.get("icd_codes", "")
        if not icd_codes:
            return findings
        
        # Parse ICD codes
        icd_bases = [code.split(".")[0] for code in str(icd_codes).split(",")]
        
        # Check OCR text for comorbidity evidence
        missed_comorbidities = []
        if ocr_text:
            ocr_lower = ocr_text.lower()
            
            for icd_base, info in cls.COMORBIDITY_DIAGNOSES.items():
                if icd_base not in icd_bases:
                    # Check if comorbidity is mentioned in text
                    keywords = info["description"].lower().split()
                    if any(keyword in ocr_lower for keyword in keywords):
                        missed_comorbidities.append((icd_base, info))
        
        for icd_base, info in missed_comorbidities:
            findings.append(LeakageFinding(
                category=RevenueLeakageCategory.MISSED_DIAGNOSIS.value,
                confidence=0.65,
                estimated_recoverable_revenue=info["revenue_impact"],
                description=f"Comorbidity {info['description']} (ICD-{icd_base}) is mentioned in clinical documentation but not coded. This could increase reimbursement.",
                recommended_correction=f"Add ICD code {icd_base} for {info['description']} as a secondary diagnosis to capture comorbidity reimbursement.",
                supporting_evidence={
                    "diagnosis_code": icd_base,
                    "diagnosis_description": info["description"],
                    "revenue_impact": info["revenue_impact"],
                    "evidence_in_text": True
                },
                affected_code=icd_base,
                source_document_id=document_id,
                source_text_snippet=ocr_text[:200] if ocr_text else ""
            ))
        
        logger.info(f"[MISSED_DIAGNOSIS_DETECTION] Reviewed {len(icd_bases)} codes, {len(findings)} findings")
        
        return findings


class MissingImplantDetector:
    """Detects missing implants that should be billed"""
    
    # Common implants and their costs
    IMPLANT_COSTS = {
        "stent": {"cost": 25000, "cpt_codes": ["37236", "37237"]},
        "pacemaker": {"cost": 80000, "cpt_codes": ["33206", "33207"]},
        "iol": {"cost": 15000, "cpt_codes": ["66984"]},
        "mesh": {"cost": 10000, "cpt_codes": ["49507"]},
        "joint": {"cost": 100000, "cpt_codes": ["27130", "27132"]},
    }
    
    @classmethod
    def detect(cls, clinical_data: Dict[str, Any], ocr_text: str = None, document_id: str = None) -> List[LeakageFinding]:
        """
        Detect missing implants.
        
        Args:
            clinical_data: Normalized clinical data
            ocr_text: OCR text for evidence
            document_id: Source document ID
            
        Returns:
            List of leakage findings
        """
        findings = []
        
        implants = clinical_data.get("implants", "")
        cpt_codes = clinical_data.get("cpt_codes", "")
        
        # Parse CPT codes
        cpt_list = []
        if cpt_codes:
            cpt_list = [code.split("-")[0].strip() if "-" in code else code.strip() for code in str(cpt_codes).split(",")]
        
        # Check OCR text for implant evidence
        if ocr_text:
            ocr_lower = ocr_text.lower()
            
            for implant_type, info in cls.IMPLANT_COSTS.items():
                # Check if implant is mentioned in text
                if implant_type in ocr_lower:
                    # Check if corresponding CPT code is present
                    has_cpt = any(cpt in cpt_list for cpt in info["cpt_codes"])
                    
                    if not has_cpt:
                        findings.append(LeakageFinding(
                            category=RevenueLeakageCategory.MISSING_IMPLANT.value,
                            confidence=0.8,
                            estimated_recoverable_revenue=info["cost"],
                            description=f"Implant ({implant_type}) is documented in clinical notes but corresponding CPT code(s) {', '.join(info['cpt_codes'])} are missing.",
                            recommended_correction=f"Add appropriate CPT code(s) from {', '.join(info['cpt_codes'])} to capture implant reimbursement.",
                            supporting_evidence={
                                "implant_type": implant_type,
                                "implant_cost": info["cost"],
                                "required_cpt_codes": info["cpt_codes"],
                                "found_cpt_codes": cpt_list,
                                "evidence_in_text": True
                            },
                            affected_document="Clinical Document",
                            source_document_id=document_id,
                            source_text_snippet=ocr_text[:200] if ocr_text else ""
                        ))
        
        logger.info(f"[MISSING_IMPLANT_DETECTION] Reviewed, {len(findings)} findings")
        
        return findings


class IncompleteChargesDetector:
    """Detects incomplete charges"""
    
    @classmethod
    def detect(cls, clinical_data: Dict[str, Any], claim_amount: Any = None, document_id: str = None) -> List[LeakageFinding]:
        """
        Detect incomplete charges.
        
        Args:
            clinical_data: Normalized clinical data
            claim_amount: Claim amount
            document_id: Source document ID
            
        Returns:
            List of leakage findings
        """
        findings = []
        
        # Check if claim amount is missing or zero
        if not claim_amount:
            findings.append(LeakageFinding(
                category=RevenueLeakageCategory.INCOMPLETE_CHARGES.value,
                confidence=0.9,
                estimated_recoverable_revenue=None,
                description="Claim amount is missing or not provided.",
                recommended_correction="Add claim amount to ensure proper reimbursement processing.",
                supporting_evidence={
                    "claim_amount": claim_amount,
                    "clinical_data_present": bool(clinical_data)
                },
                affected_document="Claim Document",
                source_document_id=document_id
            ))
        else:
            try:
                amount = float(claim_amount)
                if amount == 0:
                    findings.append(LeakageFinding(
                        category=RevenueLeakageCategory.INCOMPLETE_CHARGES.value,
                        confidence=0.95,
                        estimated_recoverable_revenue=None,
                        description="Claim amount is zero, indicating incomplete charges.",
                        recommended_correction="Review and update claim amount to reflect actual charges.",
                        supporting_evidence={
                            "claim_amount": amount
                        },
                        affected_document="Claim Document",
                        source_document_id=document_id
                    ))
            except (ValueError, TypeError):
                findings.append(LeakageFinding(
                    category=RevenueLeakageCategory.INCOMPLETE_CHARGES.value,
                    confidence=0.8,
                    estimated_recoverable_revenue=None,
                    description=f"Claim amount '{claim_amount}' is invalid, indicating incomplete charges.",
                    recommended_correction="Review and correct claim amount.",
                    supporting_evidence={
                        "claim_amount": claim_amount
                    },
                    affected_document="Claim Document",
                    source_document_id=document_id
                ))
        
        # Check for missing bill amount in clinical data
        bill_amount = clinical_data.get("bill_amount")
        if not bill_amount:
            findings.append(LeakageFinding(
                category=RevenueLeakageCategory.INCOMPLETE_CHARGES.value,
                confidence=0.7,
                estimated_recoverable_revenue=None,
                description="Bill amount is missing from clinical data.",
                recommended_correction="Add bill amount to clinical data for accurate charge capture.",
                supporting_evidence={
                    "bill_amount": bill_amount
                },
                affected_document="Clinical Document",
                source_document_id=document_id
            ))
        
        logger.info(f"[INCOMPLETE_CHARGES_DETECTION] {len(findings)} findings")
        
        return findings


class IncorrectCodingDetector:
    """Detects incorrect coding that reduces reimbursement"""
    
    # Common coding errors that reduce reimbursement
    UNDERCODED_PROCEDURES = {
        "47562": {"correct": "47563", "reason": "Cholecystectomy with cholangiography", "revenue_difference": 10000},
        "49505": {"correct": "49507", "reason": "Hernia repair with mesh", "revenue_difference": 10000},
        "66982": {"correct": "66984", "reason": "Cataract extraction with IOL", "revenue_difference": 10000},
    }
    
    @classmethod
    def detect(cls, clinical_data: Dict[str, Any], ocr_text: str = None, document_id: str = None) -> List[LeakageFinding]:
        """
        Detect incorrect coding.
        
        Args:
            clinical_data: Normalized clinical data
            ocr_text: OCR text for evidence
            document_id: Source document ID
            
        Returns:
            List of leakage findings
        """
        findings = []
        
        cpt_codes = clinical_data.get("cpt_codes", "")
        if not cpt_codes:
            return findings
        
        # Parse CPT codes
        code_entries = []
        for code_entry in str(cpt_codes).split(","):
            code_entry = code_entry.strip()
            if "-" in code_entry:
                code = code_entry.split("-")[0].strip()
            else:
                code = code_entry.strip()
            code_entries.append(code)
        
        # Check for undercoded procedures
        for code in code_entries:
            if code in cls.UNDERCODED_PROCEDURES:
                correct_info = cls.UNDERCODED_PROCEDURES[code]
                
                # Check OCR text for evidence of correct procedure
                evidence_present = False
                if ocr_text:
                    ocr_lower = ocr_text.lower()
                    # Check for keywords suggesting the more complex procedure
                    if "cholangiography" in ocr_lower and code == "47562":
                        evidence_present = True
                    elif "mesh" in ocr_lower and code == "49505":
                        evidence_present = True
                    elif "iol" in ocr_lower or "lens" in ocr_lower and code == "66982":
                        evidence_present = True
                
                if evidence_present:
                    findings.append(LeakageFinding(
                        category=RevenueLeakageCategory.INCORRECT_CODING.value,
                        confidence=0.75,
                        estimated_recoverable_revenue=correct_info["revenue_difference"],
                        description=f"CPT code {code} may be undercoded. Clinical evidence suggests {correct_info['reason']} (code {correct_info['correct']}) was performed.",
                        recommended_correction=f"Update CPT code from {code} to {correct_info['correct']} to capture correct reimbursement for {correct_info['reason']}.",
                        supporting_evidence={
                            "current_code": code,
                            "recommended_code": correct_info["correct"],
                            "reason": correct_info["reason"],
                            "revenue_difference": correct_info["revenue_difference"],
                            "evidence_in_text": True
                        },
                        affected_code=code,
                        source_document_id=document_id,
                        source_text_snippet=ocr_text[:200] if ocr_text else ""
                    ))
        
        logger.info(f"[INCORRECT_CODING_DETECTION] Reviewed {len(code_entries)} codes, {len(findings)} findings")
        
        return findings
