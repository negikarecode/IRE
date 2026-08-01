import React, { useState, useEffect } from 'react';
import { Upload, FileSpreadsheet, Search, Download, Eye, Trash2, RefreshCw, Clock, CheckCircle, AlertCircle, Loader2, FileText, Image as ImageIcon, Edit2, ChevronDown } from 'lucide-react';
import { apiClient } from '../services/api';
import { claimStore } from '../services/store';

interface Document {
  id: string;
  hospital_id: string;
  uploaded_by: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  storage_location: string;
  processing_status: string;
  upload_timestamp: string;
  pages?: number;
  document_type?: string;
  classification_confidence?: number;
  is_manually_classified?: number;
}

export const DocumentsPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [editingClassification, setEditingClassification] = useState<Document | null>(null);

  const user = claimStore.getUser();

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setIsLoading(true);
    setError('');
    try {
      const docs = await apiClient.getDocuments();
      setDocuments(docs);
    } catch (err: any) {
      console.error('Failed to load documents:', err);
      setError(err.message || 'Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await apiClient.deleteDocument(documentId);
      setDocuments(prev => prev.filter(d => d.id !== documentId));
    } catch (err: any) {
      console.error('Failed to delete document:', err);
      alert(err.message || 'Failed to delete document');
    }
  };

  const handleDownload = (doc: Document) => {
    // Create download link
    const link = document.createElement('a');
    link.href = `/api/v1/documents/${doc.id}/download`;
    link.download = doc.original_filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePreview = (doc: Document) => {
    setSelectedDoc(doc);
  };

  const handleReplace = (doc: Document) => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.jpg,.jpeg,.png,.tiff,.tif';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        try {
          await apiClient.uploadDocument(file);
          await loadDocuments();
          alert('Document replaced successfully');
        } catch (err: any) {
          console.error('Failed to replace document:', err);
          alert(err.message || 'Failed to replace document');
        }
      }
    };
    input.click();
  };

  const handleClassificationUpdate = async (doc: Document, newType: string) => {
    try {
      await apiClient.updateDocumentClassification(doc.id, newType, 1.0);
      await loadDocuments();
      setEditingClassification(null);
    } catch (err: any) {
      console.error('Failed to update classification:', err);
      alert(err.message || 'Failed to update classification');
    }
  };

  const getDocumentTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'discharge_summary': 'Discharge Summary',
      'operative_note': 'Operative Note',
      'final_bill': 'Final Bill',
      'prescription': 'Prescription',
      'authorization_letter': 'Authorization Letter',
      'investigation_report': 'Investigation Report',
      'lab_report': 'Lab Report',
      'radiology_report': 'Radiology Report',
      'insurance_form': 'Insurance Form',
      'consent_form': 'Consent Form',
      'unknown': 'Unknown',
      'medical_document': 'Medical Document'
    };
    return labels[type] || type;
  };

  const filteredDocs = documents.filter(d => 
    d.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getProcessingStatus = (status: string) => {
    switch (status) {
      case 'pending':
        return { label: 'Uploading', icon: Loader2, color: '#f59e0b' };
      case 'processing':
        return { label: 'OCR Running', icon: Loader2, color: '#3b82f6' };
      case 'completed':
        return { label: 'Completed', icon: CheckCircle, color: '#10b981' };
      case 'failed':
        return { label: 'Failed', icon: AlertCircle, color: '#ef4444' };
      default:
        return { label: 'Unknown', icon: Clock, color: '#64748b' };
    }
  };

  const getFileIcon = (mime_type: string) => {
    if (mime_type.startsWith('image/')) {
      return ImageIcon;
    }
    return FileText;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div>
      <div className="kpi-row" style={{ marginBottom: '24px' }}>
        <div className="kpi-box">
          <div className="kpi-label">Total Documents</div>
          <div className="kpi-num">{documents.length}</div>
          <div className="kpi-trend">Hospital Files</div>
        </div>
        <div className="kpi-box">
          <div className="kpi-label">Processing</div>
          <div className="kpi-num">{documents.filter(d => d.processing_status === 'processing').length}</div>
          <div className="kpi-trend">OCR Running</div>
        </div>
        <div className="kpi-box">
          <div className="kpi-label">Completed</div>
          <div className="kpi-num">{documents.filter(d => d.processing_status === 'completed').length}</div>
          <div className="kpi-trend">Ready for Review</div>
        </div>
      </div>

      <div className="card-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(15, 23, 42, 0.6)', padding: '8px 16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)', width: '350px' }}>
            <Search size={18} color="#64748b" />
            <input 
              type="text" 
              placeholder="Search documents by filename..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: '#ffffff', outline: 'none', width: '100%' }}
            />
          </div>

          <button 
            onClick={loadDocuments}
            style={{ background: 'rgba(255, 255, 255, 0.1)', color: '#ffffff', border: '1px solid rgba(255, 255, 255, 0.2)', padding: '10px 18px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <RefreshCw size={18} /> Refresh
          </button>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '64px 20px' }}>
            <Loader2 size={48} color="#00f2fe" className="animate-spin" style={{ margin: '0 auto 16px auto' }} />
            <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Loading documents...</p>
          </div>
        ) : error ? (
          <div style={{ textAlign: 'center', padding: '64px 20px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '12px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
            <AlertCircle size={48} color="#ef4444" style={{ margin: '0 auto 16px auto' }} />
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ffffff', margin: '0 0 8px 0' }}>Error Loading Documents</h3>
            <p style={{ color: '#ef4444', fontSize: '0.9rem' }}>{error}</p>
            <button 
              onClick={loadDocuments}
              style={{ marginTop: '16px', background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '10px 20px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer' }}
            >
              Retry
            </button>
          </div>
        ) : filteredDocs.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' }}>
            {filteredDocs.map(doc => {
              const status = getProcessingStatus(doc.processing_status);
              const StatusIcon = status.icon;
              const FileIcon = getFileIcon(doc.mime_type);
              
              return (
                <div 
                  key={doc.id}
                  style={{
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '12px',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '16px'
                  }}
                >
                  {/* Header */}
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                    <div style={{ 
                      width: '48px', 
                      height: '48px', 
                      borderRadius: '10px', 
                      background: 'rgba(0, 242, 254, 0.1)', 
                      color: '#00f2fe', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      flexShrink: 0
                    }}>
                      <FileIcon size={24} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <h4 style={{ 
                        fontSize: '0.95rem', 
                        fontWeight: 700, 
                        color: '#ffffff', 
                        margin: '0 0 4px 0',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}>
                        {doc.original_filename}
                      </h4>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: '#64748b' }}>
                        <Clock size={14} />
                        {formatDate(doc.upload_timestamp)}
                      </div>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    gap: '8px', 
                    padding: '8px 12px', 
                    borderRadius: '8px', 
                    background: `${status.color}20`,
                    border: `1px solid ${status.color}40`
                  }}>
                    <StatusIcon size={16} color={status.color} className={doc.processing_status === 'processing' ? 'animate-spin' : ''} />
                    <span style={{ color: status.color, fontSize: '0.85rem', fontWeight: 600 }}>
                      {status.label}
                    </span>
                  </div>

                  {/* Details */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.85rem' }}>
                    <div>
                      <div style={{ color: '#64748b', marginBottom: '4px' }}>Pages</div>
                      <div style={{ color: '#ffffff', fontWeight: 600 }}>
                        {doc.pages !== undefined && doc.pages !== null ? doc.pages : '-'}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: '#64748b', marginBottom: '4px' }}>Document Type</div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ color: '#ffffff', fontWeight: 600 }}>
                          {getDocumentTypeLabel(doc.document_type || 'Unknown')}
                        </div>
                        {doc.classification_confidence !== undefined && doc.classification_confidence > 0 && (
                          <span style={{ 
                            fontSize: '0.75rem', 
                            color: doc.classification_confidence > 0.7 ? '#10b981' : doc.classification_confidence > 0.4 ? '#f59e0b' : '#ef4444',
                            background: `${doc.classification_confidence > 0.7 ? '#10b981' : doc.classification_confidence > 0.4 ? '#f59e0b' : '#ef4444'}20`,
                            padding: '2px 6px',
                            borderRadius: '4px'
                          }}>
                            {(doc.classification_confidence * 100).toFixed(0)}%
                          </span>
                        )}
                        {doc.is_manually_classified === 1 && (
                          <span style={{ fontSize: '0.75rem', color: '#00f2fe' }}>✓ Manual</span>
                        )}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: '#64748b', marginBottom: '4px' }}>Size</div>
                      <div style={{ color: '#ffffff', fontWeight: 600 }}>
                        {formatFileSize(doc.file_size_bytes)}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: '#64748b', marginBottom: '4px' }}>Format</div>
                      <div style={{ color: '#ffffff', fontWeight: 600 }}>
                        {doc.mime_type.split('/')[1]?.toUpperCase() || 'FILE'}
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    <button
                      onClick={() => handlePreview(doc)}
                      style={{
                        flex: 1,
                        minWidth: '80px',
                        background: 'rgba(0, 242, 254, 0.1)',
                        color: '#00f2fe',
                        border: '1px solid rgba(0, 242, 254, 0.3)',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <Eye size={16} /> Preview
                    </button>
                    <button
                      onClick={() => setEditingClassification(doc)}
                      style={{
                        flex: 1,
                        minWidth: '80px',
                        background: 'rgba(59, 130, 246, 0.1)',
                        color: '#3b82f6',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <Edit2 size={16} /> Classify
                    </button>
                    <button
                      onClick={() => handleDownload(doc)}
                      style={{
                        flex: 1,
                        minWidth: '80px',
                        background: 'rgba(16, 185, 129, 0.1)',
                        color: '#10b981',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <Download size={16} /> Download
                    </button>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      style={{
                        flex: 1,
                        minWidth: '80px',
                        background: 'rgba(239, 68, 68, 0.1)',
                        color: '#ef4444',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px'
                      }}
                    >
                      <Trash2 size={16} /> Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '64px 20px', background: 'rgba(15,23,42,0.4)', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.08)' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'rgba(0,242,254,0.1)', color: '#00f2fe', margin: '0 auto 16px auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileSpreadsheet size={28} />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ffffff', margin: '0 0 6px 0' }}>
              No documents uploaded yet
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.88rem', maxWidth: '440px', margin: '0 auto 20px auto', lineHeight: 1.5 }}>
              Upload medical documents to begin AI processing and claim review.
            </p>
          </div>
        )}
      </div>

      {/* Classification Edit Modal */}
      {editingClassification && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.95)', padding: '30px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.1)', width: '500px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ color: '#ffffff', margin: 0 }}>Edit Document Classification</h3>
              <button onClick={() => setEditingClassification(null)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '24px' }}>✕</button>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <div style={{ color: '#64748b', marginBottom: '8px', fontSize: '0.9rem' }}>Current Classification</div>
              <div style={{ color: '#ffffff', fontWeight: 600, fontSize: '1.1rem' }}>
                {getDocumentTypeLabel(editingClassification.document_type || 'Unknown')}
              </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <div style={{ color: '#64748b', marginBottom: '8px', fontSize: '0.9rem' }}>Select New Classification</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                {[
                  'discharge_summary', 'operative_note', 'final_bill', 'prescription',
                  'authorization_letter', 'investigation_report', 'lab_report',
                  'radiology_report', 'insurance_form', 'consent_form', 'unknown'
                ].map(type => (
                  <button
                    key={type}
                    onClick={() => handleClassificationUpdate(editingClassification, type)}
                    style={{
                      background: editingClassification.document_type === type ? 'rgba(0, 242, 254, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                      color: editingClassification.document_type === type ? '#00f2fe' : '#ffffff',
                      border: editingClassification.document_type === type ? '1px solid rgba(0, 242, 254, 0.5)' : '1px solid rgba(255, 255, 255, 0.1)',
                      padding: '10px 12px',
                      borderRadius: '6px',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      cursor: 'pointer',
                      textAlign: 'left'
                    }}
                  >
                    {getDocumentTypeLabel(type)}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={() => setEditingClassification(null)}
              style={{
                width: '100%',
                background: 'rgba(255, 255, 255, 0.1)',
                color: '#ffffff',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                padding: '12px',
                borderRadius: '8px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {selectedDoc && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.95)', padding: '30px', borderRadius: '12px', border: '1px solid rgba(255, 255, 255, 0.1)', width: '600px', maxHeight: '80vh', overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ color: '#ffffff', margin: 0 }}>Document Preview</h3>
              <button onClick={() => setSelectedDoc(null)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '24px' }}>✕</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '4px' }}>Filename</div>
                <div style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff' }}>{selectedDoc.original_filename}</div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '4px' }}>Document ID</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#00f2fe', wordBreak: 'break-all' }}>{selectedDoc.id}</div>
                </div>
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '4px' }}>File Size</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#ffffff' }}>{formatFileSize(selectedDoc.file_size_bytes)}</div>
                </div>
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '4px' }}>MIME Type</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#ffffff' }}>{selectedDoc.mime_type}</div>
                </div>
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '4px' }}>Pages</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#ffffff' }}>{selectedDoc.pages !== undefined && selectedDoc.pages !== null ? selectedDoc.pages : 'Not processed'}</div>
                </div>
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '4px' }}>Document Type</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#ffffff' }}>{selectedDoc.document_type || 'Unknown (OCR pending)'}</div>
                </div>
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '4px' }}>Upload Time</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#ffffff' }}>{formatDate(selectedDoc.upload_timestamp)}</div>
                </div>
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
                  <div style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '4px' }}>Processing Status</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600, color: '#ffffff' }}>{selectedDoc.processing_status}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentsPage;
