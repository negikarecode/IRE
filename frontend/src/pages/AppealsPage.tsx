import React, { useState, useEffect } from 'react';
import { CheckCircle, FileText, Send, ShieldCheck, ShieldAlert } from 'lucide-react';
import { claimStore, AppealRecord } from '../services/store';

export const AppealsPage: React.FC = () => {
  const [appeals, setAppeals] = useState<AppealRecord[]>(claimStore.getAppeals());

  useEffect(() => {
    const unsubscribe = claimStore.subscribe(() => {
      setAppeals(claimStore.getAppeals());
    });
    return () => unsubscribe();
  }, []);

  const handleReviewAppeal = (appeal: AppealRecord) => {
    alert(`Reviewing AI Appeal Draft for #${appeal.claimRef} (${appeal.patientName}).`);
  };

  const handleSubmitAppeal = (appeal: AppealRecord) => {
    alert(`Submitted reconsideration appeal package for #${appeal.claimRef} to ${appeal.insuranceCompany}.`);
  };

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#ffffff', margin: 0 }}>Denied Claims Appeals</h2>
          <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginTop: '4px' }}>
            Reconsideration manager for denied claims requiring appeal packages.
          </p>
        </div>
        <span className={`badge ${appeals.length > 0 ? 'badge-red' : 'badge-green'}`} style={{ fontFamily: 'var(--font-mono)' }}>
          {appeals.length} Denied Claims
        </span>
      </div>

      {appeals.length > 0 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {appeals.map((appeal) => (
            <div
              key={appeal.id}
              className="gh-card"
              style={{
                padding: '24px 28px'
              }}
            >
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '18px' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '2px' }}>
                    Claim Ref
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#ffffff' }}>
                    #{appeal.claimRef} — {appeal.patientName}
                  </div>
                  <div style={{ marginTop: '6px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginRight: '6px' }}>
                      Insurance Company:
                    </span>
                    <span style={{ fontSize: '0.88rem', color: '#cbd5e1', fontWeight: 500 }}>
                      {appeal.insuranceCompany}
                    </span>
                  </div>
                </div>
                {appeal.aiDraftReady && (
                  <span className="badge badge-green" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                    <CheckCircle size={14} /> AI Appeal Draft Ready
                  </span>
                )}
              </div>

              {/* Body */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '20px', paddingBottom: '18px', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <div>
                  <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                    Denial Reason
                  </div>
                  <div style={{ fontSize: '0.92rem', color: '#ef4444', fontWeight: 600 }}>
                    {appeal.denialReason}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '40px', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                      Amount at Risk
                    </div>
                    <div style={{ fontSize: '0.92rem', color: '#ffffff', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      {appeal.amountAtRisk}
                    </div>
                  </div>

                  <div>
                    <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                      Appeal Deadline
                    </div>
                    <div style={{ fontSize: '0.92rem', color: '#f59e0b', fontWeight: 600 }}>
                      {appeal.appealDeadline}
                    </div>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  onClick={() => handleReviewAppeal(appeal)}
                  style={{
                    background: 'rgba(255, 255, 255, 0.06)',
                    color: '#e2e8f0',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    padding: '8px 16px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <FileText size={15} /> Review Appeal
                </button>
                <button
                  onClick={() => handleSubmitAppeal(appeal)}
                  style={{
                    background: 'linear-gradient(135deg, var(--accent-cyan), #0284c7)',
                    color: '#000000',
                    border: 'none',
                    padding: '8px 18px',
                    borderRadius: '8px',
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <Send size={15} /> Submit Appeal
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        /* Empty State - No Appeals Required */
        <div className="gh-card" style={{ padding: '64px 32px', textAlign: 'center' }}>
          <div style={{ width: '60px', height: '60px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', margin: '0 auto 16px auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShieldCheck size={32} />
          </div>
          <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#ffffff', margin: '0 0 6px 0' }}>
            No Appeals Required
          </h3>
          <p style={{ color: '#94a3b8', fontSize: '0.92rem', margin: 0 }}>
            Good news.
          </p>
          <p style={{ color: '#94a3b8', fontSize: '0.92rem', margin: '4px 0 0 0' }}>
            There are currently no denied claims requiring appeal.
          </p>
        </div>
      )}
    </div>
  );
};

export default AppealsPage;
