import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { CheckCircle, Clock, Loader2, AlertCircle, ChevronRight } from 'lucide-react';
import { apiClient } from '../services/api';

interface ProcessingStage {
  id: string;
  name: string;
  status: 'completed' | 'processing' | 'waiting' | 'error';
  message?: string;
  timestamp?: string;
}

export const ClaimProcessingPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [stages, setStages] = useState<ProcessingStage[]>([
    { id: 'upload', name: 'Uploading Documents', status: 'completed', message: 'Documents uploaded successfully' },
    { id: 'ocr', name: 'OCR Processing', status: 'waiting', message: 'Waiting to start' },
    { id: 'classification', name: 'Document Classification', status: 'waiting', message: 'Waiting to start' },
    { id: 'extraction', name: 'Clinical Field Extraction', status: 'waiting', message: 'Waiting to start' },
    { id: 'assembly', name: 'Claim Assembly', status: 'waiting', message: 'Waiting to start' },
    { id: 'completed', name: 'Completed', status: 'waiting', message: 'Waiting to start' }
  ]);
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [estimatedTime, setEstimatedTime] = useState<number | null>(null);
  const [startTime, setStartTime] = useState<number>(Date.now());
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Get document ID from URL state or query params
    const params = new URLSearchParams(location.search);
    const docId = params.get('documentId') || location.state?.documentId;
    
    if (docId) {
      setDocumentId(docId);
      startSSEConnection(docId);
    } else {
      setError('No document ID provided');
    }

    // Cleanup SSE connection on unmount
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [location]);

  const startSSEConnection = (docId: string) => {
    const token = localStorage.getItem('auth_token');
    const sseUrl = `/api/v1/sse/jobs/stream?document_id=${docId}&token=${token}`;
    
    const eventSource = new EventSource(sseUrl);
    
    eventSourceRef.current = eventSource;
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.event === 'job_update') {
          handleJobUpdate(data.data);
        } else if (data.event === 'heartbeat') {
          // Keep connection alive
          // SSE heartbeat received
        } else if (data.event === 'error') {
          console.error('SSE error:', data.data);
          setError(data.data.message);
        }
      } catch (err) {
        console.error('Error parsing SSE message:', err);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      setError('Connection to server lost. Please refresh the page.');
      eventSource.close();
    };
  };

  const handleJobUpdate = (jobData: any) => {
    const newStages = [...stages];
    
    // Map job types to stages
    const jobTypeToStage: Record<string, number> = {
      'upload': 0,
      'ocr': 1,
      'classification': 2,
      'extraction': 3,
      'claim_assembly': 4
    };
    
    const stageIndex = jobTypeToStage[jobData.job_type];
    
    if (stageIndex !== undefined) {
      if (jobData.status === 'running') {
        newStages[stageIndex] = {
          ...newStages[stageIndex],
          status: 'processing',
          message: `${newStages[stageIndex].name} in progress...`
        };
      } else if (jobData.status === 'completed') {
        newStages[stageIndex] = {
          ...newStages[stageIndex],
          status: 'completed',
          message: `${newStages[stageIndex].name} completed`,
          timestamp: jobData.updated_at
        };
        
        // Update next stage to processing if not the last stage
        if (stageIndex < newStages.length - 2) {
          newStages[stageIndex + 1] = {
            ...newStages[stageIndex + 1],
            status: 'processing',
            message: `${newStages[stageIndex + 1].name} in progress...`
          };
        }
      } else if (jobData.status === 'failed') {
        newStages[stageIndex] = {
          ...newStages[stageIndex],
          status: 'error',
          message: jobData.error_message || `${newStages[stageIndex].name} failed`
        };
        setError(jobData.error_message || 'Processing failed');
      }
    }
    
    // Check if all stages are completed
    const allCompleted = newStages.every(stage => stage.status === 'completed');
    if (allCompleted && stageIndex === 4) {
      newStages[5] = {
        ...newStages[5],
        status: 'completed',
        message: 'Processing complete'
      };
      
      // Redirect to claim review after delay
      setTimeout(() => {
        navigate('/claim-review', { state: { documentId } });
      }, 2000);
    }
    
    // Update estimated time
    const elapsed = (Date.now() - startTime) / 1000;
    const completedStages = newStages.filter(s => s.status === 'completed').length;
    const totalStages = newStages.length;
    
    if (elapsed > 0 && !allCompleted) {
      const avgTimePerStage = elapsed / Math.max(completedStages, 1);
      const remainingStages = totalStages - completedStages;
      setEstimatedTime(Math.ceil(avgTimePerStage * remainingStages));
    } else {
      setEstimatedTime(null);
    }
    
    setStages(newStages);
  };

  const getStageIcon = (stage: ProcessingStage) => {
    switch (stage.status) {
      case 'completed':
        return <CheckCircle size={24} className="text-green-500" />;
      case 'processing':
        return <Loader2 size={24} className="text-blue-500 animate-spin" />;
      case 'error':
        return <AlertCircle size={24} className="text-red-500" />;
      default:
        return <Clock size={24} className="text-gray-500" />;
    }
  };

  const getStageColor = (stage: ProcessingStage) => {
    switch (stage.status) {
      case 'completed':
        return 'border-green-500 bg-green-500/10';
      case 'processing':
        return 'border-blue-500 bg-blue-500/10';
      case 'error':
        return 'border-red-500 bg-red-500/10';
      default:
        return 'border-gray-700 bg-gray-800/50';
    }
  };

  const getTextColor = (stage: ProcessingStage) => {
    switch (stage.status) {
      case 'completed':
        return 'text-green-400';
      case 'processing':
        return 'text-blue-400';
      case 'error':
        return 'text-red-400';
      default:
        return 'text-gray-500';
    }
  };

  if (error) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}>
        <div style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '12px',
          padding: '40px',
          textAlign: 'center',
          maxWidth: '400px'
        }}>
          <AlertCircle size={48} style={{ color: '#ef4444', marginBottom: '20px' }} />
          <h2 style={{ color: '#ffffff', marginBottom: '12px', fontSize: '1.5rem' }}>Processing Error</h2>
          <p style={{ color: '#94a3b8', marginBottom: '24px' }}>{error}</p>
          <button
            onClick={() => navigate('/documents')}
            style={{
              background: 'rgba(239, 68, 68, 0.2)',
              color: '#ef4444',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              padding: '12px 24px',
              borderRadius: '8px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Return to Documents
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
      padding: '40px 20px'
    }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '48px' }}>
          <h1 style={{
            color: '#ffffff',
            fontSize: '2rem',
            fontWeight: 800,
            marginBottom: '12px',
            background: 'linear-gradient(135deg, #00f2fe 0%, #4facfe 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Processing Your Claim
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '1.1rem' }}>
            Status: Processing in progress...
          </p>
        </div>

        {/* Progress Stages */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {stages.map((stage, index) => (
            <div key={stage.id} style={{ position: 'relative' }}>
              {/* Stage Card */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '20px',
                padding: '24px',
                borderRadius: '12px',
                border: `2px solid ${stage.status === 'completed' ? '#22c55e' : stage.status === 'processing' ? '#3b82f6' : stage.status === 'error' ? '#ef4444' : '#374151'}`,
                background: stage.status === 'completed' ? 'rgba(34, 197, 94, 0.1)' : stage.status === 'processing' ? 'rgba(59, 130, 246, 0.1)' : stage.status === 'error' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(30, 41, 59, 0.5)',
                transition: 'all 0.3s ease'
              }}>
                {/* Icon */}
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: stage.status === 'completed' ? 'rgba(34, 197, 94, 0.2)' : stage.status === 'processing' ? 'rgba(59, 130, 246, 0.2)' : stage.status === 'error' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(75, 85, 99, 0.3)'
                }}>
                  {getStageIcon(stage)}
                </div>

                {/* Content */}
                <div style={{ flex: 1 }}>
                  <div style={{
                    color: '#ffffff',
                    fontSize: '1.1rem',
                    fontWeight: 600,
                    marginBottom: '4px'
                  }}>
                    {stage.name}
                  </div>
                  <div style={{
                    color: stage.status === 'completed' ? '#22c55e' : stage.status === 'processing' ? '#3b82f6' : stage.status === 'error' ? '#ef4444' : '#64748b',
                    fontSize: '0.9rem'
                  }}>
                    {stage.message}
                  </div>
                </div>

                {/* Chevron for next stage */}
                {index < stages.length - 1 && (
                  <ChevronRight size={20} style={{ color: '#475569' }} />
                )}
              </div>

              {/* Connector Line */}
              {index < stages.length - 1 && (
                <div style={{
                  position: 'absolute',
                  left: '48px',
                  top: '100%',
                  transform: 'translateY(-50%)',
                  width: '2px',
                  height: '16px',
                  background: stage.status === 'completed' ? '#22c55e' : '#374151',
                  marginLeft: '24px'
                }} />
              )}
            </div>
          ))}
        </div>

        {/* Footer Info */}
        <div style={{
          marginTop: '48px',
          textAlign: 'center',
          padding: '24px',
          background: 'rgba(30, 41, 59, 0.5)',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '8px' }}>
            Document ID: {documentId || 'Loading...'}
          </p>
          <p style={{ color: '#64748b', fontSize: '0.85rem' }}>
            This page will automatically redirect to Claim Review once processing is complete.
          </p>
        </div>
      </div>
    </div>
  );
};
