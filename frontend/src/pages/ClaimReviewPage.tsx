import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { 
  FileText, CheckCircle, AlertCircle, User, Activity, Loader2, X, Save, Clock,
  RefreshCw, ShieldCheck, ArrowRight, Layers, FileCode, Check
} from 'lucide-react';
import { apiClient } from '../services/api';

interface ClinicalData {
  patient_name?: string;
  uhid?: string;
  mrn?: string;
  age?: string;
  gender?: string;
  admission_date?: string;
  discharge_date?: string;
  operation_date?: string;
  length_of_stay?: number;
  hospital?: string;
  doctor?: string;
  department?: string;
  diagnosis?: string;
  icd_codes?: any[];
  procedure?: string;
  cpt_codes?: any[];
  medicines?: any[];
  implants?: any[];
  insurance_company?: string;
  policy_number?: string;
  bill_amount?: number;
  invoice_number?: string;
  extraction_confidence?: number;
}

interface Document {
  id: string;
  original_filename: string;
  hospital_id?: string;
  uploaded_by?: string;
  document_type?: string;
  processing_status: string;
  mime_type?: string;
  file_size_bytes?: number;
  pages?: number;
  upload_timestamp?: string;
  created_at?: string;
}

interface ClaimReviewPageProps {
  onNavigateTab?: (tab: string) => void;
}

export const ClaimReviewPage: React.FC<ClaimReviewPageProps> = ({ onNavigateTab }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const params = useParams<{ claimId?: string }>();
  
  const [recordId, setRecordId] = useState<string | null>(null);
  const [claimData, setClaimData] = useState<any | null>(null);
  const [document, setDocument] = useState<Document | null>(null);
  const [clinicalData, setClinicalData] = useState<ClinicalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [isRetryingOCR, setIsRetryingOCR] = useState(false);
  const [isRunningReview, setIsRunningReview] = useState(false);

  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const pathParts = location.pathname.split('/');
    const pathId = params.claimId || (pathParts[pathParts.length - 1] !== 'claim-review' ? pathParts[pathParts.length - 1] : null);
    
    const targetId = pathId || searchParams.get('claimId') || searchParams.get('documentId') || location.state?.claimId || location.state?.documentId;

    if (targetId) {
      setRecordId(targetId);
      loadRecordData(targetId, false);

      // Start live polling every 3 seconds while loading / processing
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = setInterval(() => {
        loadRecordData(targetId, true);
      }, 3000);
    } else {
      setError('No document ID or claim ID provided');
      setLoading(false);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [location, params]);

  const loadRecordData = async (targetId: string, isSilentPoll: boolean = false) => {
    try {
      if (!isSilentPoll) setLoading(true);
      setError(null);

      let fetchedClaim: any = null;
      let docId = targetId;

      // Try fetching claim record by ID
      try {
        fetchedClaim = await apiClient.getClaimById(targetId);
        if (fetchedClaim) {
          setClaimData(fetchedClaim);
          if (fetchedClaim.document_id) {
            docId = fetchedClaim.document_id;
          }
        }
      } catch (_) {}

      // Fetch document record by ID
      let docData: any = null;
      try {
        docData = await apiClient.getDocument(docId);
        setDocument(docData);
        
        if (!fetchedClaim && docData?.claim_id) {
          try {
            fetchedClaim = await apiClient.getClaimById(docData.claim_id);
            setClaimData(fetchedClaim);
          } catch (_) {}
        }
      } catch (docErr) {
        if (!fetchedClaim && !isSilentPoll) {
          setError(`Record '${targetId}' not found in database`);
          setLoading(false);
          return;
        }
      }

      // Try fetching clinical extraction
      try {
        const clinical = await apiClient.getClinicalExtraction(docId);
        if (clinical && Object.keys(clinical).length > 0) {
          setClinicalData(clinical);
        } else {
          setClinicalData(null);
        }
      } catch (_) {
        setClinicalData(null);
      }

      // Stop live polling if document processing reached terminal status
      const status = docData?.processing_status;
      if (status === 'completed' || status === 'failed') {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      }

      if (!isSilentPoll) setLoading(false);
    } catch (err: any) {
      console.error('Error loading record data:', err);
      if (!isSilentPoll) {
        setError('Failed to load record from database');
        setLoading(false);
      }
    }
  };

  const handleRetryOCR = async () => {
    if (!document?.id) return;
    setIsRetryingOCR(true);
    try {
      await apiClient.retryOCR(document.id);
      if (recordId) {
        loadRecordData(recordId, false);
      }
    } catch (err: any) {
      alert(`OCR Retry error: ${err.message || 'Failed to trigger OCR retry'}`);
    }
    setIsRetryingOCR(false);
  };

  const handleStartAIReview = async () => {
    if (!claimData?.id) return;
    setIsRunningReview(true);
    try {
      await apiClient.runAIReview(claimData.id);
      if (recordId) {
        await loadRecordData(recordId, false);
      }
    } catch (err: any) {
      alert(`AI Review error: ${err.message || 'Failed to start AI compliance review'}`);
    }
    setIsRunningReview(false);
  };

  const handleSaveField = async () => {
    if (!editingField || !recordId) return;
    
    setSaving(true);
    try {
      setClinicalData(prev => ({ ...prev, [editingField]: editValue }));
      setEditingField(null);
      setEditValue('');
    } catch (err) {
      console.error('Error saving field:', err);
    }
    setSaving(false);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '—';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—';
    try {
      return new Date(dateStr).toLocaleString();
    } catch (_) {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '60vh', gap: '16px' }}>
        <Loader2 size={48} className="animate-spin" style={{ color: '#00f2fe' }} />
        <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>Loading persistent database record...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', maxWidth: '600px', margin: '0 auto' }}>
        <AlertCircle size={52} style={{ color: '#ef4444', marginBottom: '16px' }} />
        <h2 style={{ color: '#ffffff', fontSize: '1.4rem', fontWeight: 800, marginBottom: '8px' }}>Error Loading Record</h2>
        <p style={{ color: '#94a3b8', fontSize: '0.92rem', marginBottom: '24px' }}>{error}</p>
        <button
          onClick={() => {
            if (onNavigateTab) onNavigateTab('upload-claim');
            else navigate('/documents');
          }}
          style={{
            background: 'linear-gradient(135deg, #00f2fe, #4facfe)',
            color: '#000000',
            border: 'none',
            padding: '12px 24px',
            borderRadius: '8px',
            fontWeight: 800,
            cursor: 'pointer'
          }}
        >
          Upload New Claim Document
        </button>
      </div>
    );
  }

  // State Machine Calculations
  const ocrStatus = document?.processing_status || 'pending';
  const claimStatus = claimData?.status || 'UPLOADED';

  const isOcrCompleted = ocrStatus === 'completed';
  const isOcrFailed = ocrStatus === 'failed';
  const isOcrRunning = ocrStatus === 'processing';
  const isOcrQueued = ocrStatus === 'pending';

  const isReviewRunning = claimStatus === 'RUNNING_AI' || claimStatus === 'PROCESSING_REVIEW';
  const isReviewCompleted = claimStatus === 'VALIDATED' || claimStatus === 'REVIEWED' || claimStatus === 'APPROVED';

  // Determine current timeline active step index (0 to 5)
  let currentStepIndex = 0;
  if (isReviewCompleted) currentStepIndex = 5;
  else if (isReviewRunning) currentStepIndex = 4;
  else if (isOcrCompleted) currentStepIndex = 3;
  else if (isOcrRunning) currentStepIndex = 2;
  else if (isOcrQueued) currentStepIndex = 1;
  else currentStepIndex = 0;

  const timelineSteps = [
    { label: 'Upload Complete', status: 'completed' },
    { label: 'OCR Queued', status: currentStepIndex > 1 ? 'completed' : currentStepIndex === 1 ? 'running' : 'waiting' },
    { label: 'OCR Running', status: currentStepIndex > 2 ? 'completed' : currentStepIndex === 2 ? 'running' : 'waiting' },
    { label: 'OCR Completed', status: currentStepIndex > 3 ? 'completed' : currentStepIndex === 3 ? 'running' : isOcrFailed ? 'failed' : 'waiting' },
    { label: 'AI Compliance Review', status: currentStepIndex > 4 ? 'completed' : currentStepIndex === 4 ? 'running' : 'waiting' },
    { label: 'Review Ready', status: currentStepIndex === 5 ? 'completed' : 'waiting' }
  ];

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{
            color: '#ffffff',
            fontSize: '1.8rem',
            fontWeight: 800,
            marginBottom: '4px',
            background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Claim Review & Workspace
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: 0 }}>
            Claim Reference: <span style={{ color: '#00f2fe', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{claimData?.external_claim_ref || claimData?.id || recordId}</span>
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={() => {
              if (onNavigateTab) onNavigateTab('claims');
              else navigate('/claims');
            }}
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              color: '#ffffff',
              padding: '8px 16px',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
          >
            ← Claims Queue
          </button>
        </div>
      </div>

      {/* UPLOAD SUCCESS CARD & TIMELINE GRID */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px', marginBottom: '28px' }}>
        
        {/* Upload Success & Current Status */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.8)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          gap: '16px'
        }}>
          <div>
            <div style={{ fontSize: '0.82rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', fontWeight: 700, marginBottom: '12px' }}>
              Upload Status & Checkpoints
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#10b981', fontWeight: 600, fontSize: '0.92rem' }}>
                <CheckCircle size={18} /> ✓ File Uploaded
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#10b981', fontWeight: 600, fontSize: '0.92rem' }}>
                <ShieldCheck size={18} /> ✓ Stored Securely
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#10b981', fontWeight: 600, fontSize: '0.92rem' }}>
                <FileText size={18} /> ✓ Claim Record Created
              </div>
            </div>
          </div>

          <div style={{ background: 'rgba(0, 0, 0, 0.3)', padding: '16px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
            <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase' }}>Current Status</div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '6px' }}>
              <span style={{ 
                color: isOcrCompleted ? '#10b981' : isOcrFailed ? '#ef4444' : isOcrRunning ? '#00f2fe' : '#f59e0b', 
                fontWeight: 800, 
                fontSize: '1.05rem',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                {(isOcrRunning || isReviewRunning) && <Loader2 size={16} className="animate-spin" />}
                {isOcrFailed ? 'OCR Failed' : isOcrCompleted ? 'OCR Completed' : isOcrRunning ? 'OCR Running' : 'Waiting for OCR...'}
              </span>

              {isOcrFailed && (
                <button
                  onClick={handleRetryOCR}
                  disabled={isRetryingOCR}
                  style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid rgba(239, 68, 68, 0.5)',
                    color: '#ef4444',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  {isRetryingOCR ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />} Retry OCR
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Vertical Workflow Timeline */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.8)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          padding: '24px'
        }}>
          <div style={{ fontSize: '0.82rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', fontWeight: 700, marginBottom: '16px' }}>
            Processing Workflow Timeline
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {timelineSteps.map((step, idx) => {
              const isDone = step.status === 'completed';
              const isRunning = step.status === 'running';
              const isFailed = step.status === 'failed';

              return (
                <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: isDone ? 'rgba(16, 185, 129, 0.2)' : isRunning ? 'rgba(0, 242, 254, 0.2)' : isFailed ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                    border: `2px solid ${isDone ? '#10b981' : isRunning ? '#00f2fe' : isFailed ? '#ef4444' : 'rgba(255, 255, 255, 0.2)'}`,
                    color: isDone ? '#10b981' : isRunning ? '#00f2fe' : isFailed ? '#ef4444' : '#64748b',
                    fontSize: '0.75rem',
                    fontWeight: 800
                  }}>
                    {isDone ? <Check size={14} /> : isRunning ? <Loader2 size={12} className="animate-spin" /> : idx + 1}
                  </div>

                  <span style={{ 
                    color: isDone ? '#10b981' : isRunning ? '#00f2fe' : isFailed ? '#ef4444' : '#64748b',
                    fontWeight: isRunning || isDone ? 700 : 500,
                    fontSize: '0.88rem'
                  }}>
                    {step.label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

      </div>

      {/* METADATA CARDS (RESTORED CLEAN TWO-COLUMN LAYOUT) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '28px' }}>
        
        {/* Document Section */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <h3 style={{ color: '#00f2fe', fontSize: '1rem', fontWeight: 800, margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileText size={18} /> Document Metadata
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', fontSize: '0.86rem' }}>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>Filename</div>
              <div style={{ color: '#ffffff', fontWeight: 600, marginTop: '2px', wordBreak: 'break-all' }}>{document?.original_filename || claimData?.document_filename || '—'}</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>Upload Time</div>
              <div style={{ color: '#ffffff', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{formatDate(document?.upload_timestamp || document?.created_at || claimData?.created_at)}</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>File Size</div>
              <div style={{ color: '#ffffff', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{formatFileSize(document?.file_size_bytes)}</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>Pages</div>
              <div style={{ color: '#ffffff', marginTop: '2px' }}>{document?.pages ?? '—'}</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>Document Type</div>
              <div style={{ color: '#ffffff', marginTop: '2px' }}>{document?.document_type || 'Unclassified'}</div>
            </div>
          </div>
        </div>

        {/* Claim Section */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '12px',
          padding: '20px'
        }}>
          <h3 style={{ color: '#00f2fe', fontSize: '1rem', fontWeight: 800, margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} /> Claim Record
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', fontSize: '0.86rem' }}>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>Claim ID</div>
              <div style={{ color: '#00f2fe', fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{claimData?.id || recordId || '—'}</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>Hospital ID</div>
              <div style={{ color: '#ffffff', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{claimData?.hospital_id || document?.hospital_id || '—'}</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>Status</div>
              <div style={{ color: isOcrCompleted ? '#10b981' : '#f59e0b', fontWeight: 700, marginTop: '2px' }}>{claimStatus}</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>Created By</div>
              <div style={{ color: '#ffffff', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{claimData?.created_by || document?.uploaded_by || 'System'}</div>
            </div>
            <div>
              <div style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>Created At</div>
              <div style={{ color: '#ffffff', fontFamily: 'var(--font-mono)', marginTop: '2px' }}>{formatDate(claimData?.created_at)}</div>
            </div>
          </div>
        </div>

      </div>

      {/* PATIENT & CLINICAL DATA SECTIONS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '28px' }}>
        
        {/* Patient Information */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '12px',
          padding: '24px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <User size={20} style={{ color: '#00f2fe' }} />
            <h3 style={{ color: '#ffffff', fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Patient Information</h3>
          </div>

          {!isOcrCompleted ? (
            <div style={{ padding: '32px 16px', textAlign: 'center', background: 'rgba(0, 0, 0, 0.2)', borderRadius: '10px', border: '1px dashed rgba(255, 255, 255, 0.1)' }}>
              <Clock size={32} style={{ color: '#f59e0b', marginBottom: '10px' }} />
              <div style={{ color: '#ffffff', fontWeight: 700, fontSize: '0.95rem' }}>Patient Information</div>
              <p style={{ color: '#94a3b8', fontSize: '0.84rem', margin: '4px 0 0 0' }}>Waiting for OCR extraction...</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { field: 'patient_name', label: 'Patient Name' },
                { field: 'uhid', label: 'UHID' },
                { field: 'mrn', label: 'MRN' },
                { field: 'age', label: 'Age' },
                { field: 'gender', label: 'Gender' }
              ].map(({ field, label }) => (
                <div key={field}>
                  <div style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>{label}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {editingField === field ? (
                      <>
                        <input
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          style={{
                            background: 'rgba(0, 242, 254, 0.1)',
                            border: '1px solid rgba(0, 242, 254, 0.3)',
                            color: '#ffffff',
                            padding: '6px 10px',
                            borderRadius: '6px',
                            flex: 1
                          }}
                        />
                        <button
                          onClick={handleSaveField}
                          disabled={saving}
                          style={{ background: '#10b981', color: '#ffffff', border: 'none', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer' }}
                        >
                          {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                        </button>
                        <button
                          onClick={() => setEditingField(null)}
                          style={{ background: 'transparent', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer' }}
                        >
                          <X size={14} />
                        </button>
                      </>
                    ) : (
                      <span style={{ color: clinicalData?.[field as keyof ClinicalData] ? '#ffffff' : '#64748b' }}>
                        {clinicalData?.[field as keyof ClinicalData] ? String(clinicalData[field as keyof ClinicalData]) : '—'}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Clinical Details */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '12px',
          padding: '24px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Activity size={20} style={{ color: '#00f2fe' }} />
            <h3 style={{ color: '#ffffff', fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Clinical Details</h3>
          </div>

          {!isOcrCompleted ? (
            <div style={{ padding: '32px 16px', textAlign: 'center', background: 'rgba(0, 0, 0, 0.2)', borderRadius: '10px', border: '1px dashed rgba(255, 255, 255, 0.1)' }}>
              <Clock size={32} style={{ color: '#f59e0b', marginBottom: '10px' }} />
              <div style={{ color: '#ffffff', fontWeight: 700, fontSize: '0.95rem' }}>Clinical Details</div>
              <p style={{ color: '#94a3b8', fontSize: '0.84rem', margin: '4px 0 0 0' }}>Waiting for OCR extraction...</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {[
                { field: 'hospital', label: 'Hospital' },
                { field: 'doctor', label: 'Attending Doctor' },
                { field: 'department', label: 'Department' },
                { field: 'diagnosis', label: 'Primary Diagnosis' },
                { field: 'procedure', label: 'Procedure Performed' }
              ].map(({ field, label }) => (
                <div key={field}>
                  <div style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>{label}</div>
                  <span style={{ color: clinicalData?.[field as keyof ClinicalData] ? '#ffffff' : '#64748b' }}>
                    {clinicalData?.[field as keyof ClinicalData] ? String(clinicalData[field as keyof ClinicalData]) : '—'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>

      {/* ACTION BUTTON (DISABLED UNTIL OCR FINISHES) */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '16px' }}>
        <button
          onClick={handleStartAIReview}
          disabled={!isOcrCompleted || isRunningReview}
          title={!isOcrCompleted ? "Available after OCR completes." : "Start AI compliance review on extracted clinical data"}
          style={{
            background: isOcrCompleted 
              ? 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)' 
              : 'rgba(255, 255, 255, 0.08)',
            color: isOcrCompleted ? '#000000' : '#64748b',
            border: isOcrCompleted ? 'none' : '1px solid rgba(255, 255, 255, 0.1)',
            padding: '14px 32px',
            borderRadius: '10px',
            fontWeight: 800,
            fontSize: '1rem',
            cursor: isOcrCompleted ? 'pointer' : 'not-allowed',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            boxShadow: isOcrCompleted ? '0 4px 16px rgba(0, 242, 254, 0.3)' : 'none',
            transition: 'all 0.2s ease'
          }}
        >
          {isRunningReview ? (
            <>
              <Loader2 size={20} className="animate-spin" /> Running AI Review...
            </>
          ) : (
            <>
              <ShieldCheck size={20} /> Start AI Compliance Review
            </>
          )}
        </button>
      </div>

    </div>
  );
};
