import React, { useState, useEffect } from 'react';
import { Paperclip, UploadCloud, Search, FileText, CheckCircle, AlertTriangle } from 'lucide-react';
import { claimStore, ClaimRecord } from '../services/store';

interface ClaimsPageProps {
  onNavigateToReview?: () => void;
  onNavigateToUpload?: () => void;
}

export const ClaimsPage: React.FC<ClaimsPageProps> = ({ onNavigateToReview, onNavigateToUpload }) => {
  const [activeFilter, setActiveFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [claims, setClaims] = useState<ClaimRecord[]>(claimStore.getClaims());
  const [selectedClaim, setSelectedClaim] = useState<ClaimRecord | null>(null);

  useEffect(() => {
    const unsubscribe = claimStore.subscribe(() => {
      setClaims(claimStore.getClaims());
    });
    return () => unsubscribe();
  }, []);

  const filteredClaims = claims.filter(c => {
    const matchesFilter = activeFilter === 'ALL' || c.status === activeFilter;
    const matchesSearch = searchQuery === '' || 
      c.claimRef.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.patientName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.patientUhid.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const analytics = claimStore.getAnalytics();

  return (
    <div>
      {/* KPI Row calculated from actual claims */}
      <div className="kpi-row" style={{ marginBottom: '24px' }}>
        <div className="kpi-box">
          <div className="kpi-label">Total Claims Ingested</div>
          <div className="kpi-num">{analytics.totalClaims} Claims</div>
          <div className="kpi-trend">Actual Uploaded Records</div>
        </div>
        <div className="kpi-box">
          <div className="kpi-label">Claims Ready to Submit</div>
          <div className="kpi-num" style={{ color: '#10b981' }}>{analytics.claimsReady}</div>
          <div className="kpi-trend">Zero Compliance Blockers</div>
        </div>
        <div className="kpi-box">
          <div className="kpi-label">Revenue At Risk</div>
          <div className="kpi-num" style={{ color: analytics.revenueAtRisk > 0 ? '#ef4444' : '#ffffff', fontFamily: 'var(--font-mono)' }}>
            ₹{analytics.revenueAtRisk.toLocaleString('en-IN')}.00
          </div>
          <div className="kpi-trend">Open Scrubber Warnings</div>
        </div>
      </div>

      <div className="card-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            {['ALL', 'NEEDS_REVIEW', 'READY_TO_SUBMIT', 'SUBMITTED'].map(st => (
              <button
                key={st}
                onClick={() => setActiveFilter(st)}
                style={{
                  background: activeFilter === st ? 'rgba(0,242,254,0.15)' : 'transparent',
                  color: activeFilter === st ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  border: '1px solid var(--border-color)',
                  padding: '6px 14px',
                  borderRadius: '6px',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--bg-primary)', padding: '6px 14px', borderRadius: '6px', border: '1px solid var(--border-color)', width: '260px' }}>
              <Search size={16} color="var(--text-secondary)" />
              <input
                type="text"
                placeholder="Search claim ref or patient..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', width: '100%', fontSize: '0.84rem' }}
              />
            </div>

            <button
              onClick={onNavigateToUpload}
              style={{
                background: 'linear-gradient(135deg, var(--accent-cyan), #0284c7)',
                color: '#000000',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '0.82rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <UploadCloud size={16} /> Upload Claim
            </button>
          </div>
        </div>

        {/* Claims Table or Clean Empty State */}
        {filteredClaims.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Claim Ref</th>
                <th>Patient Name</th>
                <th>UHID / MRN</th>
                <th>Insurance Company</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredClaims.map(c => (
                <tr key={c.id}>
                  <td style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{c.claimRef}</td>
                  <td style={{ fontWeight: 600 }}>{c.patientName}</td>
                  <td style={{ color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>{c.patientUhid}</td>
                  <td>{c.insuranceCompany}</td>
                  <td style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>₹{c.amount.toLocaleString('en-IN')}.00</td>
                  <td>
                    <span className={`badge ${c.status === 'READY_TO_SUBMIT' || c.status === 'SUBMITTED' ? 'badge-green' : 'badge-amber'}`}>
                      {c.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td>
                    <button 
                      onClick={() => {
                        claimStore.setActiveClaimId(c.id);
                        if (onNavigateToReview) onNavigateToReview();
                      }}
                      style={{ background: 'rgba(0,242,254,0.1)', border: '1px solid rgba(0,242,254,0.3)', color: '#00f2fe', padding: '5px 12px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 700 }}
                    >
                      Review Claim
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          /* Empty State when zero claims match or exist */
          <div style={{ textAlign: 'center', padding: '64px 20px', background: 'rgba(15,23,42,0.4)', borderRadius: '12px', border: '1px border-dashed rgba(255,255,255,0.08)' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'rgba(0,242,254,0.1)', color: '#00f2fe', margin: '0 auto 16px auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <FileText size={28} />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ffffff', margin: '0 0 6px 0' }}>
              {claims.length === 0 ? 'No Claims Yet' : 'No matching claims.'}
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.88rem', maxWidth: '420px', margin: '0 auto 20px auto', lineHeight: 1.5 }}>
              {claims.length === 0 
                ? 'Claims will appear here after documents are uploaded and processed.' 
                : 'Try adjusting your search query or status filter.'}
            </p>
            {claims.length === 0 && (
              <button
                onClick={onNavigateToUpload}
                style={{
                  background: 'linear-gradient(135deg, #10b981, #00f2fe)',
                  color: '#000000',
                  border: 'none',
                  padding: '10px 24px',
                  borderRadius: '8px',
                  fontSize: '0.88rem',
                  fontWeight: 800,
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <UploadCloud size={18} /> Upload First Claim
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ClaimsPage;
