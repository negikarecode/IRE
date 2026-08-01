import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, Enum, Text, Boolean, Index
import enum
from app.core.database import Base

class DocumentType(str, enum.Enum):
    DISCHARGE_SUMMARY = "discharge_summary"
    OPERATIVE_NOTE = "operative_note"
    FINAL_BILL = "final_bill"
    PRESCRIPTION = "prescription"
    AUTHORIZATION_LETTER = "authorization_letter"
    INVESTIGATION_REPORT = "investigation_report"
    LAB_REPORT = "lab_report"
    RADIOLOGY_REPORT = "radiology_report"
    INSURANCE_FORM = "insurance_form"
    CONSENT_FORM = "consent_form"
    UNKNOWN = "unknown"

class DocumentClaimStatus(str, enum.Enum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"

class ProcessingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ClaimModel(Base):
    __tablename__ = "claims"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True)
    patient_id = Column(String(64), nullable=False, index=True)
    hospital_id = Column(String(64), nullable=True, index=True)
    external_claim_ref = Column(String(128), nullable=False, index=True)
    status = Column(String(64), default="INGESTED", index=True)
    amount = Column(Float, default=0.0)
    raw_payload = Column(JSON, nullable=False)
    adjudication_output = Column(JSON, nullable=True)
    
    # Soft delete and audit tracking
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_claims_tenant_status", "tenant_id", "status"),
        Index("idx_claims_hospital_status", "hospital_id", "status"),
        Index("idx_claims_hospital_patient", "hospital_id", "patient_id"),
    )

class VirusScanStatus(str, enum.Enum):
    PENDING = "pending"
    SCANNING = "scanning"
    CLEAN = "clean"
    INFECTED = "infected"
    ERROR = "error"
    SKIPPED = "skipped"

class RetentionPolicy(str, enum.Enum):
    PERMANENT = "permanent"
    DAYS_30 = "30_days"
    DAYS_90 = "90_days"
    DAYS_180 = "180_days"
    DAYS_365 = "365_days"
    CUSTOM = "custom"

class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(64), nullable=False, index=True)
    uploaded_by = Column(String(64), nullable=False, index=True)
    claim_id = Column(String(64), nullable=True, index=True)
    original_filename = Column(String(255), nullable=False)
    internal_filename = Column(String(255), nullable=False, unique=True)  # Unique internal filename
    mime_type = Column(String(128), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    storage_location = Column(String(512), nullable=False)
    checksum = Column(String(64), nullable=False)  # SHA-256 checksum
    processing_status = Column(String(32), default=ProcessingStatus.PENDING.value, index=True)
    pages = Column(Integer, nullable=True)
    document_type = Column(String(64), nullable=True)
    classification_confidence = Column(Float, nullable=True)
    is_manually_classified = Column(Integer, default=0)  # 0 = auto, 1 = manual
    upload_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Security and compliance fields
    virus_scan_status = Column(String(32), default=VirusScanStatus.PENDING.value, index=True)
    virus_scan_timestamp = Column(DateTime(timezone=True), nullable=True)
    virus_scan_engine = Column(String(64), nullable=True)  # e.g., "clamav", "aws-guardduty"
    
    # Retention policy
    retention_policy = Column(String(32), default=RetentionPolicy.PERMANENT.value)
    retention_until = Column(DateTime(timezone=True), nullable=True)  # For custom retention
    marked_for_deletion = Column(Integer, default=0)  # 0 = no, 1 = yes
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Access control
    access_count = Column(Integer, default=0)  # Track download/access count
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed_by = Column(String(64), nullable=True)
    created_by = Column(String(64), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_docs_hospital_claim", "hospital_id", "claim_id"),
        Index("idx_docs_hospital_status", "hospital_id", "processing_status"),
        Index("idx_docs_hospital_type", "hospital_id", "document_type"),
    )

class OCRResultModel(Base):
    __tablename__ = "ocr_results"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(64), nullable=False, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    raw_text = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    page_count = Column(Integer, nullable=True)
    detected_language = Column(String(10), nullable=True)
    processing_status = Column(String(32), default=ProcessingStatus.PENDING.value, index=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_ocr_doc_hosp", "document_id", "hospital_id"),
        Index("idx_ocr_hosp_status", "hospital_id", "processing_status"),
    )

class ClinicalExtractionModel(Base):
    __tablename__ = "clinical_extractions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(64), nullable=False, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    
    # Patient Information
    patient_name = Column(String(255), nullable=True)
    uhid = Column(String(64), nullable=True)
    mrn = Column(String(64), nullable=True)
    age = Column(String(32), nullable=True)
    gender = Column(String(32), nullable=True)
    
    # Dates
    admission_date = Column(String(64), nullable=True)
    discharge_date = Column(String(64), nullable=True)
    operation_date = Column(String(64), nullable=True)
    length_of_stay = Column(Integer, nullable=True)
    
    # Hospital Information
    hospital = Column(String(255), nullable=True)
    doctor = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    
    # Medical Information
    diagnosis = Column(Text, nullable=True)
    icd_codes = Column(JSON, nullable=True)  # Array of ICD codes
    procedure = Column(Text, nullable=True)
    cpt_codes = Column(JSON, nullable=True)  # Array of CPT codes
    medicines = Column(JSON, nullable=True)  # Array of medicines
    implants = Column(JSON, nullable=True)  # Array of implants
    
    # Insurance Information
    insurance_company = Column(String(255), nullable=True)
    policy_number = Column(String(128), nullable=True)
    bill_amount = Column(Float, nullable=True)
    invoice_number = Column(String(128), nullable=True)
    
    # Metadata
    extraction_confidence = Column(Float, nullable=True)
    extraction_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_clinical_doc_hosp", "document_id", "hospital_id"),
        Index("idx_clinical_hosp_mrn", "hospital_id", "mrn"),
    )

class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class JobType(str, enum.Enum):
    UPLOAD = "upload"
    OCR = "ocr"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    CLAIM_ASSEMBLY = "claim_assembly"

class JobModel(Base):
    __tablename__ = "jobs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(64), nullable=False, index=True)
    job_type = Column(String(32), nullable=False, index=True)
    status = Column(String(32), default=JobStatus.QUEUED.value, index=True)
    
    # Job payload and results
    payload = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Document/Entity reference
    document_id = Column(String(64), nullable=True, index=True)
    claim_id = Column(String(64), nullable=True, index=True)
    
    # Retry tracking
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timing
    queued_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_time_seconds = Column(Float, nullable=True)
    
    # Metadata
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_jobs_hosp_status", "hospital_id", "status"),
        Index("idx_jobs_hosp_type", "hospital_id", "job_type"),
    )

class NormalizationMethod(str, enum.Enum):
    DATE_ISO = "date_iso"
    DOCTOR_NAME_CLEAN = "doctor_name_clean"
    DIAGNOSIS_STANDARDIZE = "diagnosis_standardize"
    PROCEDURE_CODE_UPPER = "procedure_code_upper"
    INSURANCE_ALIAS = "insurance_alias"
    AMOUNT_DECIMAL = "amount_decimal"
    TEXT_TRIM = "text_trim"
    TEXT_CASE = "text_case"
    CUSTOM = "custom"

class ValidationSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class ValidationCategory(str, enum.Enum):
    MISSING_DOCUMENT = "missing_document"
    MISSING_DIAGNOSIS = "missing_diagnosis"
    MISSING_SIGNATURE = "missing_signature"
    MISSING_AUTHORIZATION = "missing_authorization"
    CODING_INCONSISTENCY = "coding_inconsistency"
    PATIENT_MISMATCH = "patient_mismatch"
    DATE_INCONSISTENCY = "date_inconsistency"
    DUPLICATE_BILLING = "duplicate_billing"
    DOCUMENT_INCOMPLETE = "document_incomplete"
    MISSING_CREDENTIALS = "missing_credentials"
    MISSING_IDENTIFIERS = "missing_identifiers"
    OTHER = "other"

class ValidationFindingModel(Base):
    __tablename__ = "validation_findings"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(64), nullable=False, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    document_id = Column(String(64), nullable=True, index=True)  # Source document
    
    # Finding details
    severity = Column(String(32), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category = Column(String(64), nullable=False, index=True)  # Validation category
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Affected elements
    affected_document = Column(String(255), nullable=True)  # Document type/name
    affected_field = Column(String(128), nullable=True)  # Field name
    
    # Finding details
    explanation = Column(Text, nullable=False)  # Human-readable explanation
    recommended_fix = Column(Text, nullable=True)  # Recommended action
    
    # Source traceability
    source_document_id = Column(String(64), nullable=True)  # Trace back to source
    source_page_number = Column(Integer, nullable=True)  # Page number if applicable
    source_text_snippet = Column(Text, nullable=True)  # Relevant text snippet
    
    # Status
    status = Column(String(32), default="open", index=True)  # open, acknowledged, fixed, dismissed
    acknowledged_by = Column(String(64), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    fixed_by = Column(String(64), nullable=True)
    fixed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    validation_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ValidationSummaryModel(Base):
    __tablename__ = "validation_summaries"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(64), nullable=False, unique=True, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    
    # Summary statistics
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    
    # Overall status
    overall_status = Column(String(32), default="pending")  # pending, passed, failed, review_required
    overall_confidence = Column(Float, nullable=True)  # Average confidence of all findings
    
    # Validation metadata
    validated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    validated_by = Column(String(64), nullable=True)  # System or user ID
    validation_version = Column(String(32), nullable=True)  # Version of validation rules
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class CodingReviewSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class CodingReviewCategory(str, enum.Enum):
    INVALID_CODE = "invalid_code"
    DELETED_CODE = "deleted_code"
    MISSING_MODIFIER = "missing_modifier"
    CODE_COMBINATION = "code_combination"
    DIAGNOSIS_PROCEDURE_MISMATCH = "diagnosis_procedure_mismatch"
    BUNDLING_ISSUE = "bundling_issue"
    MEDICAL_NECESSITY = "medical_necessity"
    MODIFIER_ISSUE = "modifier_issue"
    OTHER = "other"

class CodingReviewFindingModel(Base):
    __tablename__ = "coding_review_findings"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(64), nullable=False, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    document_id = Column(String(64), nullable=True, index=True)
    
    # Code information
    code_type = Column(String(32), nullable=False, index=True)  # ICD, CPT, HCPCS
    code_value = Column(String(32), nullable=False, index=True)  # The actual code
    modifier = Column(String(32), nullable=True)  # Modifier if applicable
    
    # Finding details
    severity = Column(String(32), nullable=False, index=True)
    category = Column(String(64), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    
    # Issue and recommendation
    detected_issue = Column(Text, nullable=False)
    correct_coding_recommendation = Column(Text, nullable=True)
    reference_document = Column(String(255), nullable=True)  # Source document
    
    # Financial impact
    expected_financial_impact = Column(Float, nullable=True)  # Positive or negative impact
    impact_currency = Column(String(8), default="INR")
    
    # Medical evidence traceability
    medical_evidence = Column(JSON, nullable=True)  # Extracted evidence supporting finding
    evidence_source_document_id = Column(String(64), nullable=True)
    evidence_text_snippet = Column(Text, nullable=True)
    evidence_page_number = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(32), default="open", index=True)  # open, acknowledged, fixed, dismissed
    acknowledged_by = Column(String(64), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    fixed_by = Column(String(64), nullable=True)
    fixed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    review_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_by = Column(String(64), nullable=True)  # System or user ID
    review_version = Column(String(32), nullable=True)  # Version of coding rules
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class CodingReviewSummaryModel(Base):
    __tablename__ = "coding_review_summaries"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(64), nullable=False, unique=True, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    
    # Summary statistics
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    
    # Code-specific statistics
    icd_codes_reviewed = Column(Integer, default=0)
    cpt_codes_reviewed = Column(Integer, default=0)
    hcpcs_codes_reviewed = Column(Integer, default=0)
    
    # Financial impact summary
    total_financial_impact = Column(Float, nullable=True)
    impact_currency = Column(String(8), default="INR")
    
    # Overall status
    overall_status = Column(String(32), default="pending")  # pending, passed, failed, review_required
    overall_confidence = Column(Float, nullable=True)
    
    # Review metadata
    reviewed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    reviewed_by = Column(String(64), nullable=True)
    review_version = Column(String(32), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class DenialRiskScore(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DenialPredictionModel(Base):
    __tablename__ = "denial_predictions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(64), nullable=False, unique=True, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    
    # Prediction results
    denial_probability = Column(Float, nullable=False)  # 0.0 to 1.0
    risk_score = Column(String(32), nullable=False, index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    confidence = Column(Float, nullable=False)  # Overall confidence in prediction
    
    # Financial impact
    estimated_financial_exposure = Column(Float, nullable=True)
    exposure_currency = Column(String(8), default="INR")
    claim_amount = Column(Float, nullable=True)  # Original claim amount
    
    # Predicted denial reasons
    predicted_denial_reasons = Column(JSON, nullable=True)  # List of reasons with weights
    
    # Contributing factors
    contributing_factors = Column(JSON, nullable=True)  # Top factors with explanations
    
    # Risk factor scores
    missing_documentation_score = Column(Float, nullable=True)
    authorization_score = Column(Float, nullable=True)
    coding_score = Column(Float, nullable=True)
    insurance_rules_score = Column(Float, nullable=True)
    historical_patterns_score = Column(Float, nullable=True)
    clinical_inconsistencies_score = Column(Float, nullable=True)
    
    # Metadata
    prediction_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    prediction_model_version = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class RevenueLeakageCategory(str, enum.Enum):
    UNDERBILLING = "underbilling"
    MISSING_PROCEDURE = "missing_procedure"
    MISSING_MODIFIER = "missing_modifier"
    MISSED_DIAGNOSIS = "missed_diagnosis"
    MISSING_IMPLANT = "missing_implant"
    INCOMPLETE_CHARGES = "incomplete_charges"
    INCORRECT_CODING = "incorrect_coding"
    OTHER = "other"

class RevenueLeakageFindingModel(Base):
    __tablename__ = "revenue_leakage_findings"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(64), nullable=False, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    document_id = Column(String(64), nullable=True, index=True)
    
    # Finding details
    category = Column(String(64), nullable=False, index=True)
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Revenue impact
    estimated_recoverable_revenue = Column(Float, nullable=True)
    revenue_currency = Column(String(8), default="INR")
    
    # Finding details
    description = Column(Text, nullable=False)
    recommended_correction = Column(Text, nullable=True)
    
    # Evidence and traceability
    supporting_evidence = Column(JSON, nullable=True)
    affected_document = Column(String(255), nullable=True)
    affected_code = Column(String(32), nullable=True)  # CPT/ICD code if applicable
    
    # Source traceability
    source_document_id = Column(String(64), nullable=True)
    source_page_number = Column(Integer, nullable=True)
    source_text_snippet = Column(Text, nullable=True)
    
    # Status
    status = Column(String(32), default="open", index=True)  # open, acknowledged, recovered, dismissed
    acknowledged_by = Column(String(64), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    recovered_by = Column(String(64), nullable=True)
    recovered_at = Column(DateTime(timezone=True), nullable=True)
    recovered_amount = Column(Float, nullable=True)
    
    # Metadata
    detection_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    detection_model_version = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class RevenueLeakageSummaryModel(Base):
    __tablename__ = "revenue_leakage_summaries"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(64), nullable=False, unique=True, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    
    # Summary statistics
    total_findings = Column(Integer, default=0)
    total_recoverable_revenue = Column(Float, nullable=True)
    revenue_currency = Column(String(8), default="INR")
    
    # Category breakdown
    underbilling_count = Column(Integer, default=0)
    missing_procedure_count = Column(Integer, default=0)
    missing_modifier_count = Column(Integer, default=0)
    missed_diagnosis_count = Column(Integer, default=0)
    missing_implant_count = Column(Integer, default=0)
    incomplete_charges_count = Column(Integer, default=0)
    incorrect_coding_count = Column(Integer, default=0)
    
    # Recovery tracking
    recovered_amount = Column(Float, default=0.0)
    recovery_percentage = Column(Float, nullable=True)
    
    # Metadata
    detection_timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    detection_model_version = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ClaimChangeStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EDITED = "edited"
    APPROVED = "approved"

class CorrectedClaimPreviewModel(Base):
    __tablename__ = "corrected_claim_previews"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    claim_id = Column(String(64), nullable=False, unique=True, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    
    # Original claim data
    original_claim_data = Column(JSON, nullable=False)
    
    # Corrected claim data
    corrected_claim_data = Column(JSON, nullable=True)
    
    # AI recommendations that led to corrections
    ai_recommendations = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(32), default="pending", index=True)  # pending, approved, rejected
    
    # Approval tracking
    approved_by = Column(String(64), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Change summary
    total_changes = Column(Integer, default=0)
    accepted_changes = Column(Integer, default=0)
    rejected_changes = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ClaimChangeModel(Base):
    __tablename__ = "claim_changes"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    preview_id = Column(String(64), nullable=False, index=True)
    claim_id = Column(String(64), nullable=False, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    
    # Change details
    field_name = Column(String(128), nullable=False, index=True)  # e.g., 'icd_codes', 'cpt_codes', 'bill_amount'
    original_value = Column(Text, nullable=True)
    corrected_value = Column(Text, nullable=True)
    change_type = Column(String(32), nullable=False)  # add, modify, delete
    
    # Source of change
    source = Column(String(64), nullable=False)  # validation, coding_review, revenue_leakage, manual
    source_finding_id = Column(String(64), nullable=True)  # ID of the AI finding that triggered this change
    
    # Status
    status = Column(String(32), default="pending", index=True)  # pending, accepted, rejected, edited, approved
    
    # Approval tracking
    accepted_by = Column(String(64), nullable=True)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(String(64), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    edited_by = Column(String(64), nullable=True)
    edited_at = Column(DateTime(timezone=True), nullable=True)
    edited_value = Column(Text, nullable=True)  # User's edited value
    
    # AI recommendation reference
    ai_recommendation = Column(JSON, nullable=True)  # Full AI recommendation that led to this change
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class NormalizationModel(Base):
    __tablename__ = "normalizations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(64), nullable=False, index=True)
    hospital_id = Column(String(64), nullable=False, index=True)
    field_name = Column(String(128), nullable=False, index=True)  # e.g., 'patient_name', 'diagnosis'
    field_type = Column(String(64), nullable=False, index=True)  # e.g., 'date', 'text', 'amount'
    
    # Original and normalized values
    original_value = Column(Text, nullable=False)
    normalized_value = Column(Text, nullable=True)
    
    # Metadata
    normalization_method = Column(String(64), nullable=False)
    confidence = Column(Float, nullable=True)  # Confidence in the normalization
    applied_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Additional context
    context = Column(JSON, nullable=True)  # Additional context for the normalization
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class DocumentClaimModel(Base):
    __tablename__ = "document_claims"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(64), nullable=False, index=True)
    claim_number = Column(String(128), nullable=False, unique=True, index=True)
    status = Column(String(32), default=DocumentClaimStatus.DRAFT.value, index=True)
    
    # Required document types for a complete claim
    required_document_types = Column(JSON, nullable=True)  # Array of required types
    missing_document_types = Column(JSON, nullable=True)  # Array of missing types
    
    # Metadata
    created_by = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
