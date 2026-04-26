import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Journal = () => {
  const [thought, setThought] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const navigate = useNavigate();

  const handleSave = () => {
    if (thought.length < 10) return;
    setIsSaving(true);
    // Simulate API call
    setTimeout(() => {
      setIsSaving(false);
      navigate('/reframe', { state: { thought } });
    }, 1500);
  };

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-in-out', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <header style={{ display: 'flex', alignItems: 'center', marginBottom: '24px', marginTop: '16px' }}>
        <button onClick={() => navigate(-1)} style={{ fontSize: '24px', marginRight: '16px', color: 'var(--text-primary)' }}>
          ←
        </button>
        <h1 className="text-xl">Thought Journal</h1>
      </header>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <label htmlFor="thought" className="text-lg font-medium" style={{ marginBottom: '16px' }}>
          What's on your mind?
        </label>
        <textarea
          id="thought"
          value={thought}
          onChange={(e) => setThought(e.target.value)}
          placeholder="I'm feeling anxious about..."
          style={{
            flex: 1,
            width: '100%',
            backgroundColor: 'var(--surface-color)',
            border: 'none',
            borderRadius: 'var(--radius-xl)',
            padding: '24px',
            fontSize: '16px',
            fontFamily: 'inherit',
            resize: 'none',
            outline: 'none',
            boxShadow: 'var(--shadow-sm)',
            marginBottom: '24px'
          }}
        />

        {thought.length > 0 && thought.length < 10 && (
          <p className="text-xs text-alert" style={{ marginBottom: '16px' }}>
            Please write at least 10 characters.
          </p>
        )}

        <button 
          className="btn-primary" 
          onClick={handleSave}
          disabled={thought.length < 10 || isSaving}
          style={{ 
            width: '100%', 
            opacity: (thought.length < 10 || isSaving) ? 0.5 : 1,
            justifyContent: 'center'
          }}
        >
          {isSaving ? 'Analyzing your thoughts...' : 'Analyze & Reframe'}
        </button>
      </div>

      <footer style={{ textAlign: 'center', marginTop: '24px', color: 'var(--text-primary)', opacity: 0.5 }}>
        <p className="text-xs" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
          🔒 Your data is private & secure
        </p>
      </footer>
    </div>
  );
};

export default Journal;
