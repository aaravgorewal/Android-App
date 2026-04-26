import { Link } from 'react-router-dom';
import { useState } from 'react';

const Home = () => {
  const [selectedMood, setSelectedMood] = useState<string | null>(null);
  
  const moods = [
    { emoji: '😞', label: 'Down' },
    { emoji: '😐', label: 'Okay' },
    { emoji: '🙂', label: 'Good' },
    { emoji: '😄', label: 'Great' },
  ];

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-in-out' }}>
      <header style={{ marginBottom: '32px', marginTop: '16px' }}>
        <h1 className="text-2xl">How are you feeling today?</h1>
      </header>

      <section className="card" style={{ marginBottom: '24px' }}>
        <h2 className="text-sm font-semibold text-gray" style={{ marginBottom: '16px' }}>Mood Tracker</h2>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          {moods.map((m) => (
            <button
              key={m.label}
              onClick={() => setSelectedMood(m.label)}
              style={{
                fontSize: '32px',
                padding: '12px',
                borderRadius: '16px',
                backgroundColor: selectedMood === m.label ? 'var(--bg-color)' : 'transparent',
                border: selectedMood === m.label ? '2px solid var(--primary)' : '2px solid transparent',
                transition: 'all 0.2s ease',
              }}
            >
              {m.emoji}
            </button>
          ))}
        </div>
      </section>

      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
        <Link to="/journal" className="btn-primary" style={{ flex: 1 }}>
          Write Thoughts
        </Link>
        <Link to="/progress" className="btn-primary" style={{ flex: 1, backgroundColor: 'var(--secondary)' }}>
          View Insights
        </Link>
      </div>

      <section className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 className="text-sm font-semibold text-gray">Current Streak</h2>
          <p className="text-xl font-semibold">3 Days 🔥</p>
        </div>
        <div style={{ width: '48px', height: '48px', borderRadius: '50%', border: '4px solid var(--secondary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span className="font-bold text-gray">3/7</span>
        </div>
      </section>

      <footer style={{ textAlign: 'center', marginTop: '48px', color: 'var(--text-primary)', opacity: 0.5 }}>
        <p className="text-xs" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
          🔒 Your data is private & secure
        </p>
      </footer>
    </div>
  );
};

export default Home;
