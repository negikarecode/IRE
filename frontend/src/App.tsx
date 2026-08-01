import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { ClaimsPage } from './pages/ClaimsPage';
import { AppealsPage } from './pages/AppealsPage';
import { SettingsPage } from './pages/SettingsPage';
import { ClaimReviewPage } from './pages/ClaimReviewPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { PatientsPage } from './pages/PatientsPage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { DocumentUpload } from './components/DocumentUpload';
import { ClaimProcessingPage } from './pages/ClaimProcessingPage';
import { claimStore, ClaimRecord } from './services/store';
import { 
  UploadCloud, FileCheck, ShieldAlert, ArrowRight, CheckCircle, 
  Sparkles, FileText, GitPullRequest, DollarSign, RotateCcw, FileSpreadsheet
} from 'lucide-react';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [authView, setAuthView] = useState<'login' | 'signup' | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStep, setUploadStep] = useState('');
  
  const [analytics, setAnalytics] = useState(claimStore.getAnalytics());
  const [claims, setClaims] = useState<ClaimRecord[]>(claimStore.getClaims());
  const [isAuthenticated, setIsAuthenticated] = useState(claimStore.getIsAuthenticated());

  useEffect(() => {
    const unsubscribe = claimStore.subscribe(() => {
      setAnalytics(claimStore.getAnalytics());
      setClaims(claimStore.getClaims());
      setIsAuthenticated(claimStore.getIsAuthenticated());
    });
    
    // Check authentication status on mount
    if (!claimStore.getIsAuthenticated()) {
      setAuthView('login');
    }
    
    return () => unsubscribe();
  }, []);

  const handleLoginSuccess = () => {
    setAuthView(null);
    setIsAuthenticated(true);
  };

  const handleSignupSuccess = () => {
    setAuthView(null);
    setIsAuthenticated(true);
  };

  const handleSignOut = async () => {
    await claimStore.logout();
    setAuthView('login');
    setIsAuthenticated(false);
    setCurrentTab('dashboard');
  };

  const tabTitles: Record<string, string> = {
    'dashboard': 'Hospital Operational Dashboard',
    'upload-claim': 'Upload Claim Documents',
    'claim-review': 'Claim Review & AI Compliance Scrubber',
    'claims': 'Claims Work Queue',
    'appeals': 'Denied Claims Appeals',
    'documents': 'Document Object Storage',
    'patients': 'Master Patient Index',
    'settings': 'Facility & Account Settings'
  };

  // Show auth pages if not authenticated
  if (!isAuthenticated || authView) {
    if (authView === 'signup') {
      return <SignupPage onSignupSuccess={handleSignupSuccess} onNavigateToLogin={() => setAuthView('login')} />;
    }
    return <LoginPage onLoginSuccess={handleLoginSuccess} onNavigateToSignup={() => setAuthView('signup')} />;
  }

  const handleFileUpload = (file: File) => {
    setIsUploading(true);
    setUploadProgress(20);
    setUploadStep(`Extracting OCR text from ${file.name}...`);

    setTimeout(() => {
      setUploadProgress(50);
      setUploadStep('Parsing CPT-4, ICD-10 & NCCI edits...');
    }, 600);

    setTimeout(() => {
      setUploadProgress(80);
      setUploadStep('Running Star Health TPA scrubber ruleset...');
    }, 1200);

    setTimeout(() => {
      setUploadProgress(100);
      setUploadStep('Claim Created & AI Scrubber Complete! Redirecting to Claim Review...');
      claimStore.ingestDocument(file);
    }, 1700);

    setTimeout(() => {
      setIsUploading(false);
      setCurrentTab('claim-review');
    }, 2200);
  };

  const handleSimulateFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  };

  const handleDemoUploadClick = () => {
    const dummyFile = new File(['Sample Claim Discharge Content'], 'Discharge_Summary_Operative_Report_0728.pdf', { type: 'application/pdf' });
    handleFileUpload(dummyFile);
  };

  const handleResetToCleanSaaS = () => {
    if (confirm('Reset workspace to clean empty state? All uploaded claims and data will be cleared.')) {
      claimStore.clearAllDataForTesting();
      setCurrentTab('dashboard');
    }
  };

  return (
    <Router>
      <div className="app-container">
        <Sidebar currentTab={currentTab} onSelectTab={setCurrentTab} />
      
      <div className="main-viewport" style={{ marginLeft: '240px' }}>
        <Header 
          title={tabTitles[currentTab] || 'Dashboard'} 
          onSignOut={handleSignOut}
        />

        <div className="content-padding">
          <Routes>
            <Route path="/claim-processing" element={<ClaimProcessingPage />} />
            <Route path="/claim-review" element={<ClaimReviewPage onNavigateTab={setCurrentTab} />} />
          </Routes>
          
          {/* DASHBOARD TAB */}
          {currentTab === 'dashboard' && (
            <div style={{ maxWidth: '980px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
              
              {/* Reset to Empty Workspace Quick Button */}
              {claims.length > 0 && (
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button
                    onClick={handleResetToCleanSaaS}
                    style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', color: '#64748b', padding: '4px 10px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    <RotateCcw size={12} /> Clear Session (Reset to Empty SaaS Workspace)
                  </button>
                </div>
              )}

              {/* KPI CARDS - Show actual data or zeros */}
              <div className="kpi-row">
                <div className="kpi-box">
                  <div className="kpi-label">Claims Waiting Review</div>
                  <div className="kpi-num" style={{ color: analytics.claimsWaiting > 0 ? '#f59e0b' : '#ffffff' }}>
                    {analytics.claimsWaiting}
                  </div>
                  <div className="kpi-trend">Requires Scrubber Review</div>
                </div>

                <div className="kpi-box">
                  <div className="kpi-label">Claims Ready to Submit</div>
                  <div className="kpi-num" style={{ color: '#10b981' }}>
                    {analytics.claimsReady}
                  </div>
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

              {/* LARGE UPLOAD AREA */}
              <DocumentUpload 
                onUploadComplete={(documentId) => {
                  // Handle document upload completion
                  // Redirect to claim processing page
                  window.location.href = `/claim-processing?documentId=${documentId}`;
                }}
              />

              {/* RECENT CLAIMS TABLE - Only show when claims exist */}
              {claims.length > 0 && (
                <div className="card-panel">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#fff', margin: 0 }}>Recent Uploaded Claims</h3>
                    <button onClick={() => setCurrentTab('claims')} style={{ background: 'transparent', border: 'none', color: '#00f2fe', fontSize: '0.82rem', fontWeight: 700, cursor: 'pointer' }}>View All Claims →</button>
                  </div>

                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Claim Ref</th>
                        <th>Patient Name</th>
                        <th>Insurance</th>
                        <th>Amount</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {claims.slice(0, 5).map(c => (
                        <tr key={c.id}>
                          <td style={{ fontWeight: 700, color: '#00f2fe', fontFamily: 'var(--font-mono)' }}>{c.claimRef}</td>
                          <td>{c.patientName}</td>
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
                                setCurrentTab('claim-review');
                              }}
                              style={{ background: 'rgba(0,242,254,0.1)', border: '1px solid rgba(0,242,254,0.3)', color: '#00f2fe', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.78rem', fontWeight: 700 }}
                            >
                              Review
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

            </div>
          )}

          {/* UPLOAD CLAIM TAB */}
          {currentTab === 'upload-claim' && (
            <div style={{ maxWidth: '840px', margin: '0 auto', textAlign: 'center', padding: '30px 0' }}>
              {!isUploading ? (
                <div className="gh-card" style={{ padding: '54px 32px' }}>
                  <div style={{ width: '64px', height: '64px', background: 'rgba(0, 242, 254, 0.12)', borderRadius: '18px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#00f2fe', marginBottom: '20px' }}>
                    <UploadCloud size={34} />
                  </div>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff', margin: '0 0 8px 0' }}>Upload Claim PDF & Clinical Documents</h2>
                  <p style={{ color: '#94a3b8', fontSize: '0.92rem', maxWidth: '520px', margin: '0 auto 28px auto', lineHeight: 1.5 }}>
                    Upload CMS-1500, UB-04, Pre-Auth Letters, or Discharge Summaries to automatically store documents, run AI compliance audit, and auto-redirect to Claim Review.
                  </p>

                  <label 
                    style={{
                      background: 'rgba(15, 23, 42, 0.8)',
                      border: '2px dashed rgba(0, 242, 254, 0.4)',
                      borderRadius: '16px',
                      padding: '44px 24px',
                      cursor: 'pointer',
                      display: 'block',
                      marginBottom: '24px'
                    }}
                  >
                    <FileText size={36} color="#00f2fe" style={{ marginBottom: '12px' }} />
                    <div style={{ fontWeight: 700, color: '#ffffff', fontSize: '1.05rem' }}>
                      Select or Drop Hospital Claim PDF File
                    </div>
                    <div style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '6px' }}>
                      Supports PDF, PNG, JPEG, TIFF, DOCX
                    </div>
                    <input type="file" onChange={handleSimulateFileSelect} style={{ display: 'none' }} accept=".pdf,.png,.jpg,.jpeg,.doc,.docx" />
                  </label>

                  <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                    <label style={{
                      background: 'linear-gradient(135deg, #10b981, #00f2fe)',
                      color: '#000000',
                      padding: '12px 28px',
                      borderRadius: '10px',
                      fontWeight: 800,
                      fontSize: '0.92rem',
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}>
                      <Sparkles size={18} /> Upload PDF & Ingest Claim
                      <input type="file" onChange={handleSimulateFileSelect} style={{ display: 'none' }} accept=".pdf,.png,.jpg,.jpeg,.doc,.docx" />
                    </label>

                    <button
                      onClick={handleDemoUploadClick}
                      style={{ background: 'rgba(255,255,255,0.06)', color: '#fff', border: '1px solid rgba(255,255,255,0.12)', padding: '12px 20px', borderRadius: '10px', fontWeight: 600, fontSize: '0.86rem', cursor: 'pointer' }}
                    >
                      Process Sample Operative PDF
                    </button>
                  </div>
                </div>
              ) : (
                <div className="gh-card" style={{ padding: '60px 40px', textAlign: 'center' }}>
                  <div style={{ width: '60px', height: '60px', borderRadius: '50%', border: '4px solid rgba(0,242,254,0.2)', borderTop: '4px solid #00f2fe', animation: 'spin 1s linear infinite', margin: '0 auto 24px auto' }} />
                  <h3 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#fff', margin: '0 0 10px 0' }}>
                    Autonomous AI Claim Processing Pipeline
                  </h3>
                  <p style={{ color: '#00f2fe', fontWeight: 700, fontSize: '0.92rem', fontFamily: 'var(--font-mono)', margin: '0 0 20px 0' }}>
                    {uploadStep}
                  </p>

                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.08)', borderRadius: '4px', overflow: 'hidden', maxWidth: '400px', margin: '0 auto' }}>
                    <div style={{ width: `${uploadProgress}%`, height: '100%', background: 'linear-gradient(90deg, #00f2fe, #10b981)', transition: 'width 0.4s ease' }} />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* OTHER TABS */}
          {currentTab === 'claim-review' && (
            <ClaimReviewPage onNavigateTab={setCurrentTab} />
          )}

          {currentTab === 'claims' && (
            <ClaimsPage 
              onNavigateToReview={() => setCurrentTab('claim-review')} 
              onNavigateToUpload={() => setCurrentTab('upload-claim')} 
            />
          )}

          {currentTab === 'appeals' && <AppealsPage />}

          {currentTab === 'documents' && <DocumentsPage />}

          {currentTab === 'patients' && <PatientsPage />}

          {currentTab === 'settings' && <SettingsPage />}

        </div>
      </div>
    </div>
    </Router>
  );
};

export default App;
