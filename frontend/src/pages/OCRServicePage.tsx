import React, { useState } from 'react';
import { Layers, FileText, Cpu, CheckCircle, Table, Languages, Scan, RefreshCw } from 'lucide-react';

export const OCRServicePage: React.FC = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [ocrResult, setOcrResult] = useState<any | null>(null);

  const handleSimulateOCR = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
    }, 1000);
  };

  return (
    <div>
      <div className="kpi-row">
        <div className="kpi-box">
          <div className="kpi-label">Average Confidence Score</div>
          <div className="kpi-num">-</div>
          <div className="kpi-trend">No documents processed yet</div>
        </div>
        <div className="kpi-box">
          <div className="kpi-label">Processing Latency</div>
          <div className="kpi-num">-</div>
          <div className="kpi-trend">Async Queue Active</div>
        </div>
        <div className="kpi-box">
          <div className="kpi-label">Language Detection</div>
          <div className="kpi-num">-</div>
          <div className="kpi-trend">Multi-Language Matrix</div>
        </div>
      </div>

      <div className="card-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3>Modular Document OCR Service Engine</h3>
            <p style={{ color: 'var(--text-secondary)', marginTop: '4px', fontSize: '0.88rem' }}>
              Extracts text, handwriting, layout regions, bounding box coordinates, table matrices, and confidence scores into standardized JSON.
            </p>
          </div>
          <button 
            onClick={handleSimulateOCR}
            disabled={isProcessing}
            style={{ background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-blue))', color: '#000', border: 'none', padding: '10px 18px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <RefreshCw size={16} className={isProcessing ? 'spin' : ''} /> {isProcessing ? 'Processing OCR...' : 'Re-Run Pipeline'}
          </button>
        </div>

        {ocrResult ? (
          <div style={{ marginTop: '24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div style={{ background: 'var(--bg-primary)', padding: '20px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
              <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-cyan)' }}>
                <Scan size={18} /> Layout & Region Analysis
              </h4>
              <div style={{ marginTop: '14px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>Document ID:</span> <strong>{ocrResult.document_id}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>Language Detected:</span> <span className="badge badge-green">{ocrResult.language_detected}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>Overall Confidence:</span> <strong>{(ocrResult.overall_confidence_score * 100).toFixed(1)}%</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span>Processing Latency:</span> <strong>{ocrResult.latency_ms} ms</strong>
                </div>

                <div style={{ marginTop: '12px' }}>
                  <strong style={{ fontSize: '0.85rem' }}>Extracted Text Blocks & Bounding Boxes:</strong>
                  {ocrResult.pages[0].text_blocks.map((b: any, i: number) => (
                    <div key={i} style={{ background: 'var(--bg-secondary)', padding: '10px', borderRadius: '6px', marginTop: '6px', fontSize: '0.82rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span className={`badge ${b.type === 'HANDWRITING' ? 'badge-amber' : 'badge-purple'}`}>{b.type}</span>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Box: [{b.bounding_box.join(', ')}]</span>
                      </div>
                      <div style={{ marginTop: '6px', fontWeight: 500 }}>{b.text}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ background: 'var(--bg-primary)', padding: '20px', borderRadius: '10px', border: '1px solid var(--border-color)' }}>
              <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-purple)' }}>
                <Table size={18} /> Extracted Table Matrix
              </h4>

              <table className="data-table" style={{ marginTop: '14px' }}>
                <thead>
                  <tr>
                    {ocrResult.pages[0].table_grid.headers.map((h: string) => (
                      <th key={h}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ocrResult.pages[0].table_grid.matrix.map((row: string[], idx: number) => (
                    <tr key={idx}>
                      {row.map((cell: string, cidx: number) => (
                        <td key={cidx}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ marginTop: '20px' }}>
                <strong style={{ fontSize: '0.85rem' }}>Standardized JSON Response:</strong>
                <pre style={{ background: '#000', padding: '12px', borderRadius: '6px', marginTop: '6px', fontSize: '0.75rem', color: '#a7f3d0', maxHeight: '180px', overflowY: 'auto' }}>
{JSON.stringify(ocrResult, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        ) : (
          <div style={{ marginTop: '24px', padding: '64px 32px', textAlign: 'center', background: 'rgba(15,23,42,0.4)', borderRadius: '12px', border: '1px dashed rgba(255,255,255,0.08)' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'rgba(0,242,254,0.1)', color: '#00f2fe', margin: '0 auto 16px auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Scan size={28} />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ffffff', margin: '0 0 6px 0' }}>
              No OCR Results
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.88rem', maxWidth: '440px', margin: '0 auto 20px auto', lineHeight: 1.5 }}>
              Upload a document to run OCR extraction and view layout analysis, text blocks, and table matrices.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
