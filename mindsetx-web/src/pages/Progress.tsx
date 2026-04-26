const Progress = () => {
  const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
  // Mock data for mood
  const moodData = [3, 2, 4, null, 1, 3, 4]; // 1: Down, 2: Okay, 3: Good, 4: Great

  return (
    <div style={{ animation: 'fadeIn 0.5s ease-in-out' }}>
      <header style={{ marginBottom: '32px', marginTop: '16px' }}>
        <h1 className="text-2xl">Your Progress</h1>
      </header>

      <section className="card" style={{ textAlign: 'center', padding: '32px 24px' }}>
        <div style={{ fontSize: '48px', marginBottom: '8px' }}>🔥</div>
        <h2 className="text-4xl font-bold" style={{ color: 'var(--primary)', marginBottom: '4px' }}>7 Days</h2>
        <p className="text-gray font-medium">You're building a strong habit</p>
      </section>

      <section className="card">
        <h2 className="text-lg font-semibold" style={{ marginBottom: '24px' }}>Mood Tracker</h2>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', height: '150px', paddingBottom: '24px', borderBottom: '1px solid #E2E8F0' }}>
          {weekDays.map((day, index) => {
            const val = moodData[index];
            const height = val ? `${val * 25}%` : '0px';
            const color = val === 4 ? 'var(--primary)' : 
                          val === 3 ? 'var(--secondary)' : 
                          val === 2 ? '#F6AD55' : 
                          val === 1 ? 'var(--alert)' : 'transparent';
            
            return (
              <div key={day} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '10%' }}>
                <div style={{ 
                  width: '100%', 
                  height: height, 
                  backgroundColor: color, 
                  borderRadius: '4px',
                  minHeight: val ? '8px' : '0'
                }}></div>
              </div>
            );
          })}
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px' }}>
          {weekDays.map(day => (
            <span key={day} className="text-xs text-gray">{day}</span>
          ))}
        </div>

        <div style={{ marginTop: '24px', padding: '16px', backgroundColor: 'var(--bg-color)', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '24px' }}>💡</span>
          <p className="text-sm font-medium">You felt better on days you journaled.</p>
        </div>
      </section>
    </div>
  );
};

export default Progress;
