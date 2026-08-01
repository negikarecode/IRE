import React, { useEffect, useState } from 'react';
import { Search } from 'lucide-react';
import { claimStore } from '../services/store';

interface HeaderProps {
  title: string;
  onSignOut?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ title, onSignOut }) => {
  const [user, setUser] = useState(claimStore.getUser());

  useEffect(() => {
    const unsubscribe = claimStore.subscribe(() => {
      setUser(claimStore.getUser());
    });
    return () => unsubscribe();
  }, []);
  return (
    <header className="header-bar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{title}</h2>
        {user?.hospital_name && (
          <span style={{ fontSize: '0.75rem', background: 'var(--bg-card)', padding: '4px 10px', borderRadius: '12px', border: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
            {user.hospital_name}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        {/* Search Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--bg-primary)', padding: '10px 16px', borderRadius: '12px', border: '1px solid var(--border-color)', width: '360px' }}>
          <Search size={18} color="var(--text-secondary)" />
          <input
            type="text"
            placeholder="Search claims..."
            style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', outline: 'none', width: '100%', fontSize: '0.9rem' }}
          />
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '700', fontSize: '0.9rem' }}>
            {user?.full_name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{user?.full_name || 'User'}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{user?.role || 'Admin'}</div>
          </div>
          {onSignOut && (
            <button
              onClick={onSignOut}
              style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', padding: '6px 12px', borderRadius: '6px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer' }}
            >
              Sign Out
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
