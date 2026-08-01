import React, { useEffect, useState } from 'react';
import { LayoutDashboard, UploadCloud, GitPullRequest, FileText, AlertTriangle, Settings } from 'lucide-react';
import { claimStore } from '../services/store';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab }) => {
  const [user, setUser] = useState(claimStore.getUser());

  useEffect(() => {
    const unsubscribe = claimStore.subscribe(() => {
      setUser(claimStore.getUser());
    });
    return () => unsubscribe();
  }, []);
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload-claim', label: 'Upload Claim', icon: UploadCloud },
    { id: 'claim-review', label: 'Claim Review', icon: GitPullRequest },
    { id: 'claims', label: 'Claims Queue', icon: FileText },
    { id: 'appeals', label: 'Appeals', icon: AlertTriangle },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <aside style={{
      width: '240px',
      background: '#0b0f19',
      borderRight: '1px solid rgba(255, 255, 255, 0.06)',
      display: 'flex',
      flexDirection: 'column',
      position: 'fixed',
      height: '100vh',
      top: 0,
      left: 0,
      zIndex: 100
    }}>
      {/* Sidebar Header */}
      <div style={{
        height: '64px',
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        gap: '12px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)'
      }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          color: '#000000',
          fontSize: '0.9rem'
        }}>
          {user?.hospital_name?.charAt(0).toUpperCase() || 'H'}
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: '0.92rem', color: '#ffffff', letterSpacing: '-0.01em' }}>{user?.hospital_name || 'Hospital'}</div>
          <div style={{ fontSize: '0.72rem', color: '#64748b' }}>{user?.email || ''}</div>
        </div>
      </div>

      {/* Sidebar Navigation - 5 Items Only */}
      <nav style={{ padding: '24px 14px', display: 'flex', flexDirection: 'column', gap: '6px', flex: 1 }}>
        {menuItems.map(item => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <div
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '10px 14px',
                color: isActive ? '#ffffff' : '#94a3b8',
                background: isActive ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.88rem',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                userSelect: 'none'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.04)';
                  e.currentTarget.style.color = '#f1f5f9';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = '#94a3b8';
                }
              }}
            >
              <Icon size={17} style={{ opacity: isActive ? 1 : 0.7 }} />
              <span>{item.label}</span>
            </div>
          );
        })}
      </nav>
    </aside>
  );
};
export default Sidebar;
