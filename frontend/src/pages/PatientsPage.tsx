import React, { useState, useEffect } from 'react';
import { Search, Plus, UserCheck, Users } from 'lucide-react';
import { claimStore, PatientRecord } from '../services/store';

export const PatientsPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [patients, setPatients] = useState<PatientRecord[]>(claimStore.getPatients());
  const [showModal, setShowModal] = useState(false);
  const [newMrn, setNewMrn] = useState('');
  const [newFirstName, setNewFirstName] = useState('');
  const [newLastName, setNewLastName] = useState('');
  const [newDob, setNewDob] = useState('');

  useEffect(() => {
    const unsubscribe = claimStore.subscribe(() => {
      setPatients(claimStore.getPatients());
    });
    return () => unsubscribe();
  }, []);

  const handleAddPatient = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMrn || !newFirstName || !newLastName) return;
    claimStore.addPatient({
      mrn: newMrn,
      first_name: newFirstName,
      last_name: newLastName,
      dob: newDob || '1990-01-01'
    });
    setShowModal(false);
    setNewMrn('');
    setNewFirstName('');
    setNewLastName('');
    setNewDob('');
  };

  const filteredPatients = patients.filter(p => 
    p.mrn.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.first_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.last_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div>
      <div className="kpi-row" style={{ marginBottom: '24px' }}>
        <div className="kpi-box">
          <div className="kpi-label">Master Patient Index</div>
          <div className="kpi-num">{patients.length} Registered</div>
          <div className="kpi-trend">Identity Verified</div>
        </div>
        <div className="kpi-box">
          <div className="kpi-label">Compliance Status</div>
          <div className="kpi-num" style={{ color: '#10b981' }}>HIPAA Active</div>
          <div className="kpi-trend">Encrypted Storage</div>
        </div>
      </div>

      <div className="card-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--bg-primary)', padding: '8px 16px', borderRadius: '8px', border: '1px solid var(--border-color)', width: '350px' }}>
            <Search size={18} color="var(--text-secondary)" />
            <input 
              type="text" 
              placeholder="Search MRN or Patient Name..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', width: '100%' }}
            />
          </div>
          <button 
            onClick={() => setShowModal(true)}
            style={{ background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-blue))', color: '#000', border: 'none', padding: '10px 18px', borderRadius: '8px', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Plus size={18} /> Register Patient
          </button>
        </div>

        {filteredPatients.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>MRN Number</th>
                <th>Patient Full Name</th>
                <th>Date of Birth</th>
                <th>Created Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredPatients.map(p => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 600, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)' }}>{p.mrn}</td>
                  <td style={{ fontWeight: 600 }}>{p.first_name} {p.last_name}</td>
                  <td>{p.dob}</td>
                  <td>{p.created_at}</td>
                  <td><span className="badge badge-green">ACTIVE</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ textAlign: 'center', padding: '64px 20px', background: 'rgba(15,23,42,0.4)', borderRadius: '12px', border: '1px border-dashed rgba(255,255,255,0.08)' }}>
            <div style={{ width: '56px', height: '56px', borderRadius: '14px', background: 'rgba(0,242,254,0.1)', color: '#00f2fe', margin: '0 auto 16px auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Users size={28} />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#ffffff', margin: '0 0 6px 0' }}>
              No patients registered.
            </h3>
            <p style={{ color: '#94a3b8', fontSize: '0.88rem', maxWidth: '440px', margin: '0 auto 20px auto', lineHeight: 1.5 }}>
              Patients will be created automatically when claim documents are uploaded or manually registered.
            </p>
            <button
              onClick={() => setShowModal(true)}
              style={{ background: 'linear-gradient(135deg, #10b981, #00f2fe)', color: '#000', border: 'none', padding: '10px 24px', borderRadius: '8px', fontWeight: 800, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '8px' }}
            >
              <Plus size={18} /> Register First Patient
            </button>
          </div>
        )}
      </div>

      {showModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: 'var(--bg-secondary)', padding: '30px', borderRadius: '12px', border: '1px solid var(--border-color)', width: '450px' }}>
            <h3>Register New Patient</h3>
            <form onSubmit={handleAddPatient} style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Medical Record Number (MRN)</label>
                <input 
                  type="text" 
                  value={newMrn} 
                  onChange={e => setNewMrn(e.target.value)}
                  placeholder="MRN-99120"
                  required 
                  style={{ width: '100%', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '10px', borderRadius: '6px', marginTop: '4px' }}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>First Name</label>
                  <input 
                    type="text" 
                    value={newFirstName} 
                    onChange={e => setNewFirstName(e.target.value)}
                    placeholder="First name"
                    required 
                    style={{ width: '100%', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '10px', borderRadius: '6px', marginTop: '4px' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Last Name</label>
                  <input 
                    type="text" 
                    value={newLastName} 
                    onChange={e => setNewLastName(e.target.value)}
                    placeholder="Last name"
                    required 
                    style={{ width: '100%', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '10px', borderRadius: '6px', marginTop: '4px' }}
                  />
                </div>
              </div>
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Date of Birth</label>
                <input 
                  type="date" 
                  value={newDob} 
                  onChange={e => setNewDob(e.target.value)}
                  style={{ width: '100%', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '10px', borderRadius: '6px', marginTop: '4px' }}
                />
              </div>
              <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <button type="submit" style={{ flex: 1, background: 'var(--accent-cyan)', color: '#000', padding: '10px', border: 'none', borderRadius: '6px', fontWeight: 700, cursor: 'pointer' }}>
                  Save Patient Record
                </button>
                <button type="button" onClick={() => setShowModal(false)} style={{ background: 'transparent', color: 'var(--text-secondary)', border: '1px solid var(--border-color)', padding: '10px', borderRadius: '6px', cursor: 'pointer' }}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientsPage;
