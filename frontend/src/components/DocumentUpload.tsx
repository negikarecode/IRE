import React, { useState, useCallback, useRef } from 'react';
import { UploadCloud, X, FileText, Image as ImageIcon, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import { apiClient } from '../services/api';

interface UploadFile {
  id: string;
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

interface DocumentUploadProps {
  onUploadComplete?: (documentId: string, claimId: string) => void;
  hospitalId?: string;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadComplete, hospitalId }) => {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const ALLOWED_MIME_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/tiff',
    'image/tif'
  ];

  const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB

  const validateFile = (file: File): { valid: boolean; error?: string } => {
    if (!ALLOWED_MIME_TYPES.includes(file.type)) {
      return {
        valid: false,
        error: `Unsupported file type: ${file.type}. Allowed: PDF, JPG, PNG, TIFF`
      };
    }

    if (file.size > MAX_FILE_SIZE) {
      return {
        valid: false,
        error: `File size exceeds ${MAX_FILE_SIZE / (1024 * 1024)} MB limit`
      };
    }

    return { valid: true };
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    addFiles(selectedFiles);
  };

  const addFiles = (newFiles: File[]) => {
    const uploadFiles: UploadFile[] = newFiles.map(file => {
      const validation = validateFile(file);
      return {
        id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        file,
        progress: 0,
        status: validation.valid ? 'pending' : 'error',
        error: validation.error
      };
    });

    setFiles(prev => [...prev, ...uploadFiles]);

    // Start uploading valid files
    uploadFiles.forEach(uploadFile => {
      if (uploadFile.status === 'pending') {
        uploadSingleFile(uploadFile);
      }
    });
  };

  const uploadSingleFile = async (uploadFile: UploadFile) => {
    setFiles(prev => prev.map(f => 
      f.id === uploadFile.id ? { ...f, status: 'uploading', progress: 0 } : f
    ));

    try {
      const formData = new FormData();
      formData.append('file', uploadFile.file);

      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          setFiles(prev => prev.map(f => 
            f.id === uploadFile.id ? { ...f, progress } : f
          ));
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 201) {
          const raw = JSON.parse(xhr.responseText);
          const response = raw.data || raw;
          const docId = response.document_id || response.id;
          const claimId = response.claim_id || docId;
          setFiles(prev => prev.map(f => 
            f.id === uploadFile.id ? { ...f, status: 'success', progress: 100 } : f
          ));
          if (onUploadComplete) {
            onUploadComplete(docId, claimId);
          }
          window.location.href = `/claim-review/${claimId}`;
        } else {
          let errMsg = 'Upload failed';
          try {
            const error = JSON.parse(xhr.responseText);
            errMsg = error.message || error.detail?.message || (typeof error.detail === 'string' ? error.detail : 'Upload failed');
          } catch (_) {}
          setFiles(prev => prev.map(f => 
            f.id === uploadFile.id ? { ...f, status: 'error', error: errMsg } : f
          ));
        }
      });

      xhr.addEventListener('error', () => {
        setFiles(prev => prev.map(f => 
          f.id === uploadFile.id ? { ...f, status: 'error', error: 'Network error during upload' } : f
        ));
      });

      xhr.open('POST', '/api/v1/documents/upload');
      xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('auth_token') || ''}`);
      if (hospitalId) {
        xhr.setRequestHeader('X-Hospital-ID', hospitalId);
      }
      xhr.send(formData);

    } catch (error) {
      console.error('Upload error:', error);
      setFiles(prev => prev.map(f => 
        f.id === uploadFile.id ? { ...f, status: 'error', error: 'Upload failed' } : f
      ));
    }
  };

  const retryUpload = (uploadFile: UploadFile) => {
    uploadSingleFile(uploadFile);
  };

  const cancelUpload = (uploadFile: UploadFile) => {
    setFiles(prev => prev.filter(f => f.id !== uploadFile.id));
  };

  const removeFile = (uploadFile: UploadFile) => {
    setFiles(prev => prev.filter(f => f.id !== uploadFile.id));
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <ImageIcon size={24} />;
    }
    return <FileText size={24} />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div style={{ width: '100%' }}>
      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? '#00f2fe' : 'rgba(255, 255, 255, 0.2)'}`,
          borderRadius: '16px',
          padding: '48px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          background: isDragging ? 'rgba(0, 242, 254, 0.05)' : 'rgba(15, 23, 42, 0.4)',
          transition: 'all 0.2s'
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.jpg,.jpeg,.png,.tiff,.tif"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
        <UploadCloud size={48} color="#00f2fe" style={{ marginBottom: '16px' }} />
        <h3 style={{ color: '#ffffff', fontSize: '1.1rem', fontWeight: 700, marginBottom: '8px' }}>
          {isDragging ? 'Drop files here' : 'Upload Medical Documents'}
        </h3>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '16px' }}>
          Drag and drop files here, or click to browse
        </p>
        <p style={{ color: '#64748b', fontSize: '0.8rem' }}>
          Supported formats: PDF, JPG, PNG, TIFF (Max 50 MB per file)
        </p>
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <h4 style={{ color: '#ffffff', fontSize: '0.95rem', fontWeight: 600, marginBottom: '16px' }}>
            Uploading {files.length} file{files.length !== 1 ? 's' : ''}
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {files.map(uploadFile => (
              <div
                key={uploadFile.id}
                style={{
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '12px',
                  padding: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px'
                }}
              >
                {/* File Icon */}
                <div style={{ color: '#00f2fe' }}>
                  {getFileIcon(uploadFile.file)}
                </div>

                {/* File Info */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: '#ffffff', fontSize: '0.9rem', fontWeight: 600, marginBottom: '4px' }}>
                    {uploadFile.file.name}
                  </div>
                  <div style={{ color: '#64748b', fontSize: '0.8rem' }}>
                    {formatFileSize(uploadFile.file.size)}
                  </div>

                  {/* Progress Bar */}
                  {uploadFile.status === 'uploading' && (
                    <div style={{ marginTop: '8px' }}>
                      <div style={{
                        height: '4px',
                        background: 'rgba(255, 255, 255, 0.1)',
                        borderRadius: '2px',
                        overflow: 'hidden'
                      }}>
                        <div style={{
                          height: '100%',
                          width: `${uploadFile.progress}%`,
                          background: 'linear-gradient(90deg, #00f2fe, #7c3aed)',
                          borderRadius: '2px',
                          transition: 'width 0.2s'
                        }} />
                      </div>
                      <div style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '4px' }}>
                        {uploadFile.progress}% uploaded
                      </div>
                    </div>
                  )}

                  {/* Error Message */}
                  {uploadFile.status === 'error' && uploadFile.error && (
                    <div style={{
                      color: '#ef4444',
                      fontSize: '0.8rem',
                      marginTop: '8px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px'
                    }}>
                      <AlertCircle size={14} />
                      {uploadFile.error}
                    </div>
                  )}
                </div>

                {/* Status Icon */}
                <div>
                  {uploadFile.status === 'pending' && (
                    <Loader2 size={20} color="#64748b" className="animate-spin" />
                  )}
                  {uploadFile.status === 'uploading' && (
                    <Loader2 size={20} color="#00f2fe" className="animate-spin" />
                  )}
                  {uploadFile.status === 'success' && (
                    <CheckCircle size={20} color="#10b981" />
                  )}
                  {uploadFile.status === 'error' && (
                    <AlertCircle size={20} color="#ef4444" />
                  )}
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', gap: '8px' }}>
                  {uploadFile.status === 'error' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        retryUpload(uploadFile);
                      }}
                      style={{
                        background: 'transparent',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        color: '#94a3b8',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        cursor: 'pointer'
                      }}
                    >
                      Retry
                    </button>
                  )}
                  {(uploadFile.status === 'error' || uploadFile.status === 'success') && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile(uploadFile);
                      }}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: '#64748b',
                        padding: '6px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center'
                      }}
                    >
                      <X size={18} />
                    </button>
                  )}
                  {uploadFile.status === 'uploading' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        cancelUpload(uploadFile);
                      }}
                      style={{
                        background: 'transparent',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        color: '#ef4444',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '0.8rem',
                        cursor: 'pointer'
                      }}
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;
