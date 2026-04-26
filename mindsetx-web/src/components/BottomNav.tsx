import { Link, useLocation } from 'react-router-dom';

const BottomNav = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Home', icon: '🏠' },
    { path: '/journal', label: 'Journal', icon: '📝' },
    { path: '/progress', label: 'Progress', icon: '📊' },
  ];

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      width: '100%',
      maxWidth: '480px',
      backgroundColor: 'var(--surface-color)',
      boxShadow: '0 -4px 12px rgba(44, 62, 80, 0.05)',
      display: 'flex',
      justifyContent: 'space-around',
      padding: '16px 0',
      borderTopLeftRadius: '24px',
      borderTopRightRadius: '24px',
      zIndex: 10
    }}>
      {navItems.map((item) => {
        const isActive = location.pathname === item.path || 
                        (item.path === '/journal' && location.pathname === '/reframe');
        return (
          <Link 
            key={item.path} 
            to={item.path}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              color: isActive ? 'var(--primary)' : 'var(--text-primary)',
              opacity: isActive ? 1 : 0.6,
              textDecoration: 'none',
              transition: 'all 0.2s'
            }}
          >
            <span style={{ fontSize: '24px', marginBottom: '4px' }}>{item.icon}</span>
            <span className="text-xs font-medium">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
};

export default BottomNav;
