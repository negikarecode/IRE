import React, { useState, useEffect } from 'react';
import { 
  Building2, Users, Lock, ChevronDown, Key, Globe, 
  Webhook, UserPlus, Check, Copy, LogOut, ShieldCheck 
} from 'lucide-react';
import { claimStore } from '../services/store';

interface UserMember {
  id: string;
  name: string;
  email: string;
  role: string;
  permissions: string;
  status: 'Active' | 'Invited';
}

export const SettingsPage: React.FC = () => {
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);
  const [user, setUser] = useState(claimStore.getUser());

  const [hospitalInfo, setHospitalInfo] = useState({
    name: user?.hospital_name || '',
    phone: '',
    address: '',
    facilityId: '',
    npi: ''
  });

  const [users, setUsers] = useState<UserMember[]>([]);

  useEffect(() => {
    const unsubscribe = claimStore.subscribe(() => {
      const currentUser = claimStore.getUser();
      setUser(currentUser);
      if (currentUser?.hospital_name) {
        setHospitalInfo(prev => ({ ...prev, name: currentUser.hospital_name || '' }));
      }
    });
    return () => unsubscribe();
  }, []);

  const [passwords, setPasswords] = useState({
    current: '',
    newPass: '',
    confirm: ''
  });

  const [webhookUrl, setWebhookUrl] = useState('');

  const handleCopyKey = () => {
    const apiKey = localStorage.getItem('auth_token') || '';
    if (apiKey) {
      navigator.clipboard.writeText(apiKey);
      setCopiedKey(true);
      setTimeout(() => setCopiedKey(false), 2000);
    }
  };

  const handleInviteUser = () => {
    const email = prompt('Enter email address of team member to invite:');
    if (email && email.trim()) {
      setUsers([
        ...users,
        {
          id: Date.now().toString(),
          name: email.split('@')[0],
          email,
          role: 'Billing Clerk',
          permissions: 'Claims & Pre-Auth',
          status: 'Invited'
        }
      ]);
      alert(`Invitation sent to ${email}`);
    }
  };

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      <div>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#ffffff', margin: 0 }}>Facility & Account Settings</h2>
        <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginTop: '4px' }}>
          Displaying logged-in hospital facility settings and credentials.
        </p>
      </div>

      {/* 1. HOSPITAL INFORMATION */}
      <div className="gh-card" style={{ padding: '24px 28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(0, 242, 254, 0.1)', color: '#00f2fe', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Building2 size={20} />
          </div>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>Hospital Information</h3>
            <p style={{ fontSize: '0.84rem', color: '#94a3b8', margin: '2px 0 0 0' }}>Logged-in facility profile and legal credentials.</p>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Hospital / Facility Name</label>
              <input
                type="text"
                value={hospitalInfo.name}
                onChange={(e) => setHospitalInfo({ ...hospitalInfo, name: e.target.value })}
                style={{ width: '100%', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '10px 14px', color: '#fff', fontSize: '0.88rem', outline: 'none' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: '6px' }}>ROH / NPI Identifier</label>
              <input
                type="text"
                value={hospitalInfo.facilityId}
                onChange={(e) => setHospitalInfo({ ...hospitalInfo, facilityId: e.target.value })}
                placeholder="Not set"
                style={{ width: '100%', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '10px 14px', color: '#00f2fe', fontFamily: 'var(--font-mono)', fontSize: '0.88rem', outline: 'none' }}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Operational Phone</label>
              <input
                type="text"
                value={hospitalInfo.phone}
                onChange={(e) => setHospitalInfo({ ...hospitalInfo, phone: e.target.value })}
                placeholder="Not set"
                style={{ width: '100%', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '10px 14px', color: '#fff', fontSize: '0.88rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.8rem', fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: '6px' }}>Address</label>
              <input
                type="text"
                value={hospitalInfo.address}
                onChange={(e) => setHospitalInfo({ ...hospitalInfo, address: e.target.value })}
                placeholder="Not set"
                style={{ width: '100%', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '10px 14px', color: '#fff', fontSize: '0.88rem', outline: 'none' }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '8px' }}>
            <button
              onClick={() => alert('Facility settings updated.')}
              style={{ background: 'linear-gradient(135deg, var(--accent-cyan), #0284c7)', color: '#000', border: 'none', padding: '8px 18px', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 700, cursor: 'pointer' }}
            >
              Save Facility Details
            </button>
          </div>
        </div>
      </div>

      {/* 2. USERS & ROLES */}
      <div className="gh-card" style={{ padding: '24px 28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', paddingBottom: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'rgba(0, 242, 254, 0.1)', color: '#00f2fe', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Users size={20} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>Team Members & Roles</h3>
              <p style={{ fontSize: '0.84rem', color: '#94a3b8', margin: '2px 0 0 0' }}>Manage hospital staff access.</p>
            </div>
          </div>
          <button
            onClick={handleInviteUser}
            style={{ background: 'linear-gradient(135deg, var(--accent-cyan), #0284c7)', color: '#000', border: 'none', padding: '8px 16px', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 700, cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <UserPlus size={15} /> Invite User
          </button>
        </div>

        {users.length > 0 ? (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', textAlign: 'left' }}>
                <th style={{ padding: '10px 12px', fontSize: '0.78rem', textTransform: 'uppercase', color: '#64748b' }}>User Name</th>
                <th style={{ padding: '10px 12px', fontSize: '0.78rem', textTransform: 'uppercase', color: '#64748b' }}>Role</th>
                <th style={{ padding: '10px 12px', fontSize: '0.78rem', textTransform: 'uppercase', color: '#64748b' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '12px' }}>
                    <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.88rem' }}>{u.name}</div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b' }}>{u.email}</div>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span className="badge badge-purple">
                      {u.role}
                    </span>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span className={`badge ${u.status === 'Active' ? 'badge-green' : 'badge-amber'}`}>
                      {u.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ textAlign: 'center', padding: '48px 20px', color: '#64748b', fontSize: '0.9rem' }}>
            No team members added yet.
          </div>
        )}
      </div>

    </div>
  );
};
export default SettingsPage;
