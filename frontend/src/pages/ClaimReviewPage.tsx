import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  FileText, Eye, Download, Edit2, CheckCircle, AlertCircle,
  User, Building2, Activity, DollarSign, Calendar,
  Loader2, X, Save
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
  document_type?: string;
  processing_status: string;
  pages?: number;
  classification_confidence?: number;
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
  const [documentId, setDocumentId] = useState<string | null>(null);
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
    const params = new URLSearchParams(location.search);
    const docId = params.get('documentId') || location.state?.documentId;
    
    if (docId) {
      setDocumentId(docId);
      loadDocumentData(docId);
    } else {
      setError('No document ID provided');
      setLoading(false);
    }
  }, [location]);

  const loadDocumentData = async (docId: string) => {
    try {
      setLoading(true);
      const [docData, clinical] = await Promise.all([
        apiClient.getDocument(docId),
        apiClient.getClinicalExtraction(docId)
      ]);
      
      setDocument(docData);
      setClinicalData(clinical);
      setLoading(false);
    } catch (err: any) {
      console.error('Error loading document data:', err);
      setError('Failed to load document data');
      setLoading(false);
    }
  };

  const handleEditField = (field: string, value: string) => {
    setEditingField(field);
    setEditValue(value);
  };

  const handleSaveField = async () => {
    if (!editingField || !documentId) return;
    
    setSaving(true);
    try {
      // Update clinical data field (API call would go here)
      setClinicalData(prev => ({ ...prev, [editingField]: editValue }));
      setEditingField(null);
      setEditValue('');
    } catch (err) {
      console.error('Error saving field:', err);
    }
    setSaving(false);
  };

  const handleDownloadDocument = async () => {
    if (!document) return;
    // Download logic would go here
    // Download document action
  };

  const handleApprove = () => {
    setApproved(true);
    // Navigate to next step after approval
    setTimeout(() => {
      navigate('/documents');
    }, 1500);
  };

  const getMissingFields = () => {
    if (!clinicalData) return [];
    const requiredFields = ['patient_name', 'uhid', 'diagnosis', 'procedure', 'insurance_company', 'bill_amount'];
    return requiredFields.filter(field => !clinicalData[field as keyof ClinicalData]);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <Loader2 size={48} className="animate-spin" style={{ color: '#00f2fe' }} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <AlertCircle size={48} style={{ color: '#ef4444', marginBottom: '16px' }} />
        <h2 style={{ color: '#ffffff', marginBottom: '8px' }}>Error Loading Data</h2>
        <p style={{ color: '#94a3b8' }}>{error}</p>
        <button
          onClick={() => navigate('/documents')}
          style={{
            background: 'rgba(0, 242, 254, 0.1)',
            color: '#00f2fe',
            border: '1px solid rgba(0, 242, 254, 0.3)',
            padding: '12px 24px',
            borderRadius: '8px',
            marginTop: '16px',
            cursor: 'pointer'
          }}
        >
          Return to Documents
        </button>
      </div>
    );
  }

  const missingFields = getMissingFields();

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{
          color: '#ffffff',
          fontSize: '2rem',
          fontWeight: 800,
          marginBottom: '8px',
          background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          Claim Review
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '1rem' }}>
          Verify extracted clinical data before AI analysis
        </p>
      </div>

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
            <div style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>Document ID</div>
            <div style={{ color: '#00f2fe', fontWeight: 700, fontFamily: 'monospace' }}>{documentId}</div>
          </div>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>Filename</div>
            <div style={{ color: '#ffffff' }}>{document?.original_filename}</div>
          </div>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>Document Type</div>
            <div style={{ color: '#ffffff' }}>{document?.document_type || 'Unknown'}</div>
          </div>
          <div>
            <div style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 600, marginBottom: '4px' }}>OCR Confidence</div>
            <div style={{ color: document?.classification_confidence && document.classification_confidence > 0.7 ? '#10b981' : '#f59e0b', fontWeight: 700 }}>
              {document?.classification_confidence ? `${(document.classification_confidence * 100).toFixed(0)}%` : 'N/A'}
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
            Data Approved
          </h2>
          <p style={{ color: '#94a3b8' }}>Redirecting to documents...</p>
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
                          <span style={{ color: clinicalData?.[field as keyof ClinicalData] ? '#ffffff' : '#64748b', flex: 1 }}>
                            {clinicalData?.[field as keyof ClinicalData] || 'Not extracted'}
                          </span>
                          <button
                            onClick={() => handleEditField(field, clinicalData?.[field as keyof ClinicalData] || '')}
                            style={{
                              background: 'transparent',
                              color: '#00f2fe',
                              border: 'none',
                              padding: '4px',
                              cursor: 'pointer'
                            }}
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

            {/* Insurance Information */}
            <div style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              padding: '24px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Building2 size={20} style={{ color: '#00f2fe' }} />
                <h3 style={{ color: '#ffffff', fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Insurance Information</h3>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[
                  { field: 'insurance_company', label: 'Insurance Company' },
                  { field: 'policy_number', label: 'Policy Number' },
                  { field: 'bill_amount', label: 'Bill Amount' },
                  { field: 'invoice_number', label: 'Invoice Number' }
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
                          <button onClick={handleSaveField} disabled={saving} style={{ background: '#10b981', color: '#ffffff', border: 'none', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>
                            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                          </button>
                          <button onClick={() => setEditingField(null)} style={{ background: 'transparent', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem' }}>
                            <X size={14} />
                          </button>
                        </>
                      ) : (
                        <>
                          <span style={{ color: clinicalData?.[field as keyof ClinicalData] ? '#ffffff' : '#64748b', flex: 1 }}>
                            {field === 'bill_amount' && clinicalData?.[field as keyof ClinicalData] 
                              ? `₹${clinicalData[field as keyof ClinicalData]?.toFixed(2)}`
                              : clinicalData?.[field as keyof ClinicalData] || 'Not extracted'}
                          </span>
                          <button onClick={() => handleEditField(field, clinicalData?.[field as keyof ClinicalData]?.toString() || '')} style={{ background: 'transparent', color: '#00f2fe', border: 'none', padding: '4px', cursor: 'pointer' }}>
                            <Edit2 size={14} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Medical Information */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            padding: '24px',
            marginBottom: '24px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <Activity size={20} style={{ color: '#00f2fe' }} />
              <h3 style={{ color: '#ffffff', fontSize: '1.1rem', fontWeight: 700, margin: 0 }}>Medical Information</h3>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
              {[
                { field: 'diagnosis', label: 'Diagnosis' },
                { field: 'procedure', label: 'Procedure' },
                { field: 'hospital', label: 'Hospital' },
                { field: 'doctor', label: 'Doctor' },
                { field: 'department', label: 'Department' },
                { field: 'admission_date', label: 'Admission Date' },
                { field: 'discharge_date', label: 'Discharge Date' },
                { field: 'length_of_stay', label: 'Length of Stay (days)' }
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
                        <button onClick={handleSaveField} disabled={saving} style={{ background: '#10b981', color: '#ffffff', border: 'none', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>
                          {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                        </button>
                        <button onClick={() => setEditingField(null)} style={{ background: 'transparent', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '6px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem' }}>
                          <X size={14} />
                        </button>
                      </>
                    ) : (
                      <>
                        <span style={{ color: clinicalData?.[field as keyof ClinicalData] ? '#ffffff' : '#64748b', flex: 1 }}>
                          {clinicalData?.[field as keyof ClinicalData] || 'Not extracted'}
                        </span>
                        <button onClick={() => handleEditField(field, clinicalData?.[field as keyof ClinicalData]?.toString() || '')} style={{ background: 'transparent', color: '#00f2fe', border: 'none', padding: '4px', cursor: 'pointer' }}>
                          <Edit2 size={14} />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Missing Fields Warning */}
          {missingFields.length > 0 && (
            <div style={{
              background: 'rgba(245, 158, 11, 0.1)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '12px',
              padding: '20px',
              marginBottom: '24px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <AlertCircle size={20} style={{ color: '#f59e0b' }} />
                <h3 style={{ color: '#ffffff', fontSize: '1rem', fontWeight: 700, margin: 0 }}>Missing Required Fields</h3>
              </div>
              <div style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
                The following required fields could not be extracted: {missingFields.join(', ')}
              </div>
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button
              onClick={() => setShowOCRModal(true)}
              style={{
                background: 'rgba(0, 242, 254, 0.1)',
                color: '#00f2fe',
                border: '1px solid rgba(0, 242, 254, 0.3)',
                padding: '12px 24px',
                borderRadius: '8px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <Eye size={18} /> View OCR Text
            </button>
            <button
              onClick={handleDownloadDocument}
              style={{
                background: 'rgba(16, 185, 129, 0.1)',
                color: '#10b981',
                border: '1px solid rgba(16, 185, 129, 0.3)',
                padding: '12px 24px',
                borderRadius: '8px',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <Download size={18} /> Download Original
            </button>
            <button
              onClick={handleApprove}
              disabled={missingFields.length > 0}
              style={{
                background: missingFields.length > 0 ? 'rgba(255, 255, 255, 0.1)' : 'linear-gradient(135deg, #10b981, #00f2fe)',
                color: missingFields.length > 0 ? '#64748b' : '#000000',
                border: missingFields.length > 0 ? '1px solid rgba(255, 255, 255, 0.2)' : 'none',
                padding: '12px 32px',
                borderRadius: '8px',
                fontWeight: 700,
                cursor: missingFields.length > 0 ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <CheckCircle size={18} /> Approve & Continue
            </button>
          </div>
        </>
      )}

      {/* OCR Modal */}
      {showOCRModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            borderRadius: '12px',
            padding: '32px',
            maxWidth: '800px',
            maxHeight: '80vh',
            overflowY: 'auto',
            width: '90%'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ color: '#ffffff', fontSize: '1.2rem', fontWeight: 700, margin: 0 }}>OCR Extracted Text</h3>
              <button onClick={() => setShowOCRModal(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '24px' }}>✕</button>
            </div>
            <div style={{
              background: 'rgba(0, 0, 0, 0.3)',
              padding: '20px',
              borderRadius: '8px',
              color: '#cbd5e1',
              fontSize: '0.9rem',
              lineHeight: 1.6,
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}>
              {ocrResult?.raw_text || 'No OCR text available'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClaimReviewPage;
