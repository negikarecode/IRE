import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { 
  FileText, Eye, Download, Edit2, CheckCircle, AlertCircle,
  User, Building2, Activity, DollarSign, Calendar,
  Loader2, X, Save, Clock
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
  document_type?: string;
  processing_status: string;
  pages?: number;
  classification_confidence?: number;
  file_size_bytes?: number;
}

interface OCRResult {
  raw_text?: string;
  ocr_confidence?: number;
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
  const [ocrResult, setOcrResult] = useState<OCRResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');
  const [showOCRModal, setShowOCRModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [approved, setApproved] = useState(false);

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const pathParts = location.pathname.split('/');
    const pathId = params.claimId || (pathParts[pathParts.length - 1] !== 'claim-review' ? pathParts[pathParts.length - 1] : null);
    
    const targetId = pathId || searchParams.get('claimId') || searchParams.get('documentId') || location.state?.claimId || location.state?.documentId;

    if (targetId) {
      setRecordId(targetId);
      loadRecordData(targetId);
    } else {
      setError('No document ID or claim ID provided');
      setLoading(false);
    }
  }, [location, params]);

  const loadRecordData = async (targetId: string) => {
    try {
      setLoading(true);
      setError(null);

      let fetchedClaim: any = null;
      let docId = targetId;

      // First try fetching claim record by ID from database
      try {
        fetchedClaim = await apiClient.getClaimById(targetId);
        if (fetchedClaim) {
          setClaimData(fetchedClaim);
          if (fetchedClaim.document_id) {
            docId = fetchedClaim.document_id;
          }
        }
      } catch (claimErr) {
        console.log('Claim not found directly by ID, attempting document fetch...', claimErr);
      }

      // Then fetch document record by ID from database
      try {
        const docData = await apiClient.getDocument(docId);
        setDocument(docData);
        
        // If claim wasn't fetched yet, check if document has linked claim_id
        if (!fetchedClaim && docData?.claim_id) {
          try {
            fetchedClaim = await apiClient.getClaimById(docData.claim_id);
            setClaimData(fetchedClaim);
          } catch (_) {}
        }
      } catch (docErr) {
        if (!fetchedClaim) {
          setError(`Database record '${targetId}' not found`);
          setLoading(false);
          return;
        }
      }

      // Try fetching clinical extraction if available
      try {
        const clinical = await apiClient.getClinicalExtraction(docId);
        setClinicalData(clinical);
      } catch (_) {
        setClinicalData(null);
      }

      setLoading(false);
    } catch (err: any) {
      console.error('Error loading record data:', err);
      setError('Failed to load database record');
      setLoading(false);
    }
  };

  const handleEditField = (field: string, value: string) => {
    setEditingField(field);
    setEditValue(value);
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

  const handleApprove = () => {
    setApproved(true);
    setTimeout(() => {
      if (onNavigateTab) {
        onNavigateTab('claims');
      } else {
        navigate('/documents');
      }
    }, 1500);
  };

  const getMissingFields = () => {
    if (!clinicalData) return [];
    const requiredFields = ['patient_name', 'uhid', 'diagnosis', 'procedure', 'insurance_company', 'bill_amount'];
    return requiredFields.filter(field => !clinicalData[field as keyof ClinicalData]);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '60vh', gap: '16px' }}>
        <Loader2 size={48} className="animate-spin" style={{ color: '#00f2fe' }} />
        <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>Loading claim & document record from database...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 20px', maxWidth: '600px', margin: '0 auto' }}>
        <AlertCircle size={52} style={{ color: '#ef4444', marginBottom: '16px' }} />
        <h2 style={{ color: '#ffffff', fontSize: '1.4rem', fontWeight: 800, marginBottom: '8px' }}>Error Loading Claim Record</h2>
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
          Upload New Claim PDF
        </button>
      </div>
    );
  }

  const isOcrFinished = clinicalData && Object.keys(clinicalData).length > 0 && document?.processing_status === 'completed';

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
            Claim Review & Database Audit
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', margin: 0 }}>
            Persistent Database Record: <span style={{ color: '#00f2fe', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{claimData?.external_claim_ref || claimData?.id || recordId}</span>
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

      {/* OCR IN PROGRESS / UNFINISHED BANNER */}
      {!isOcrFinished && (
        <div style={{
          background: 'rgba(15, 23, 42, 0.9)',
          border: '1px solid rgba(0, 242, 254, 0.3)',
          borderRadius: '16px',
          padding: '28px 32px',
          marginBottom: '28px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ background: 'rgba(16, 185, 129, 0.2)', borderRadius: '50%', padding: '6px', color: '#10b981', display: 'flex' }}>
                <CheckCircle size={22} />
              </div>
              <div>
                <h3 style={{ color: '#ffffff', fontSize: '1.15rem', fontWeight: 800, margin: 0 }}>Upload complete</h3>
                <p style={{ color: '#94a3b8', fontSize: '0.84rem', margin: '2px 0 0 0' }}>File securely persisted in database storage.</p>
              </div>
            </div>
            <span className="badge badge-cyan" style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', fontSize: '0.85rem', background: 'rgba(0,242,254,0.15)', color: '#00f2fe', border: '1px solid rgba(0,242,254,0.4)', borderRadius: '20px', fontWeight: 700 }}>
              <Loader2 size={14} className="animate-spin" /> OCR Processing...
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600 }}>OCR Status</div>
              <div style={{ color: '#00f2fe', fontWeight: 700, fontSize: '0.95rem', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Loader2 size={14} className="animate-spin" /> Extracting text...
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600 }}>Estimated time remaining</div>
              <div style={{ color: '#ffffff', fontWeight: 700, fontSize: '0.95rem', marginTop: '4px', fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Clock size={15} style={{ color: '#f59e0b' }} /> ~5 - 10 seconds
              </div>
            </div>

            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ color: '#94a3b8', fontSize: '0.8rem', fontWeight: 600 }}>Linked Database Records</div>
              <div style={{ color: '#10b981', fontWeight: 700, fontSize: '0.88rem', marginTop: '4px' }}>
                Document & Claim Created
              </div>
            </div>
          </div>

          {/* Database Record Details */}
          {claimData && (
            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '18px', borderRadius: '10px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', fontSize: '0.84rem' }}>
              <div>
                <span style={{ color: '#64748b' }}>Claim Reference: </span>
                <span style={{ color: '#00f2fe', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{claimData.external_claim_ref || claimData.id}</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Document File: </span>
                <span style={{ color: '#ffffff', fontWeight: 600 }}>{claimData.document_filename || document?.original_filename || 'Hospital Claim Document'}</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Claim Status: </span>
                <span style={{ color: '#f59e0b', fontWeight: 700 }}>{claimData.status || 'UPLOADED'}</span>
              </div>
              <div>
                <span style={{ color: '#64748b' }}>Hospital ID: </span>
                <span style={{ color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>{claimData.hospital_id || document?.hospital_id || 'hosp_01'}</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Document Info Card */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.6)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '24px'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>Claim ID</div>
            <div style={{ color: '#00f2fe', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{claimData?.id || recordId}</div>
          </div>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>Document ID</div>
            <div style={{ color: '#ffffff', fontFamily: 'var(--font-mono)' }}>{document?.id || claimData?.document_id || 'N/A'}</div>
          </div>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>Filename</div>
            <div style={{ color: '#ffffff' }}>{document?.original_filename || claimData?.document_filename || 'Hospital Document'}</div>
          </div>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>File Size</div>
            <div style={{ color: '#ffffff', fontFamily: 'var(--font-mono)' }}>
              {document?.file_size_bytes ? `${(document.file_size_bytes / 1024).toFixed(1)} KB` : 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {approved ? (
        <div style={{
          background: 'rgba(16, 185, 129, 0.1)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '12px',
          padding: '48px',
          textAlign: 'center'
        }}>
          <CheckCircle size={64} style={{ color: '#10b981', marginBottom: '16px' }} />
          <h2 style={{ color: '#ffffff', fontSize: '1.5rem', fontWeight: 800, marginBottom: '8px' }}>
            Data Approved & Ready
          </h2>
          <p style={{ color: '#94a3b8' }}>Redirecting to Claims Work Queue...</p>
        </div>
      ) : (
        <>
          {/* Clinical Data Sections */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
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
                              padding: '8px 12px',
                              borderRadius: '6px',
                              flex: 1
                            }}
                          />
                          <button
                            onClick={handleSaveField}
                            disabled={saving}
                            style={{
                              background: '#10b981',
                              color: '#ffffff',
                              border: 'none',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '0.8rem',
                              fontWeight: 600
                            }}
                          >
                            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                          </button>
                          <button
                            onClick={() => setEditingField(null)}
                            style={{
                              background: 'transparent',
                              color: '#ef4444',
                              border: '1px solid rgba(239, 68, 68, 0.3)',
                              padding: '6px 12px',
                              borderRadius: '6px',
                              cursor: 'pointer',
                              fontSize: '0.8rem'
                            }}
                          >
                            <X size={14} />
                          </button>
                        </>
                      ) : (
                        <>
                          <span style={{ color: clinicalData?.[field as keyof ClinicalData] ? '#ffffff' : '#64748b', fontStyle: clinicalData?.[field as keyof ClinicalData] ? 'normal' : 'italic' }}>
                            {clinicalData?.[field as keyof ClinicalData] ? String(clinicalData[field as keyof ClinicalData]) : 'Pending OCR extraction...'}
                          </span>
                          <button
                            onClick={() => handleEditField(field, String(clinicalData?.[field as keyof ClinicalData] || ''))}
                            style={{ background: 'none', border: 'none', color: '#00f2fe', cursor: 'pointer', padding: '2px' }}
                          >
                            <Edit2 size={14} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
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
                    <span style={{ color: clinicalData?.[field as keyof ClinicalData] ? '#ffffff' : '#64748b', fontStyle: clinicalData?.[field as keyof ClinicalData] ? 'normal' : 'italic' }}>
                      {clinicalData?.[field as keyof ClinicalData] ? String(clinicalData[field as keyof ClinicalData]) : 'Pending OCR extraction...'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '16px' }}>
            <button
              onClick={handleApprove}
              style={{
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                color: '#ffffff',
                border: 'none',
                padding: '12px 32px',
                borderRadius: '8px',
                fontWeight: 700,
                fontSize: '1rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 4px 14px rgba(16, 185, 129, 0.4)'
              }}
            >
              <CheckCircle size={20} />
              Approve Database Claim Record
            </button>
          </div>
        </>
      )}
    </div>
  );
};
