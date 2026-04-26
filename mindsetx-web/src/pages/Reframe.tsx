import { useLocation, useNavigate } from 'react-router-dom';

const Reframe = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const thought = location.state?.thought || "I always fail in everything";

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-in-out' }}>
      <header style={{ display: 'flex', alignItems: 'center', marginBottom: '24px', marginTop: '16px' }}>
        <button onClick={() => navigate('/journal')} style={{ fontSize: '24px', marginRight: '16px', color: 'var(--text-primary)' }}>
          ←
        </button>
        <h1 className="text-xl">Analysis</h1>
      </header>

      <section className="card" style={{ borderLeft: '4px solid var(--alert)' }}>
        <h2 className="text-sm font-semibold text-gray" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          🧠 Pattern Identified
        </h2>
        <p className="text-lg font-semibold" style={{ marginTop: '8px' }}>Overgeneralization</p>
        <p className="text-sm text-gray" style={{ marginTop: '4px' }}>
          Your thought: "{thought}"
        </p>
      </section>

      <section className="card" style={{ borderLeft: '4px solid var(--primary)' }}>
        <h2 className="text-sm font-semibold text-gray" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          🔄 Reframed Thought
        </h2>
        <p className="text-lg font-semibold" style={{ marginTop: '8px', color: 'var(--primary)' }}>
          "I've had setbacks, but I can improve with effort."
        </p>
      </section>

      <section className="card" style={{ borderLeft: '4px solid var(--secondary)' }}>
        <h2 className="text-sm font-semibold text-gray" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          🎯 Small Action
        </h2>
        <p className="text-lg font-medium" style={{ marginTop: '8px' }}>
          Write down 1 thing you're grateful for today.
        </p>
        <button className="btn-primary" style={{ marginTop: '16px', width: '100%', backgroundColor: 'var(--secondary)' }} onClick={() => navigate('/')}>
          Mark Complete
        </button>
      </section>

    </div>
  );
};

export default Reframe;
