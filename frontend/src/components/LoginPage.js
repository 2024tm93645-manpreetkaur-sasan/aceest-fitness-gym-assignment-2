import React, { useState } from 'react';
import { login } from '../api';

const styles = {
  page: {
    minHeight: '100vh',
    background: '#1a1a1a',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    background: '#242424',
    border: '1px solid #3a3a3a',
    borderTop: '3px solid #d4af37',
    borderRadius: '4px',
    padding: '48px 40px',
    width: '360px',
  },
  logo: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: '36px',
    color: '#d4af37',
    letterSpacing: '2px',
    marginBottom: '4px',
  },
  sub: {
    color: '#888',
    fontSize: '12px',
    marginBottom: '36px',
    letterSpacing: '1px',
    textTransform: 'uppercase',
  },
  label: {
    display: 'block',
    color: '#888',
    fontSize: '11px',
    letterSpacing: '1px',
    textTransform: 'uppercase',
    marginBottom: '6px',
  },
  input: {
    width: '100%',
    background: '#1a1a1a',
    border: '1px solid #3a3a3a',
    borderRadius: '3px',
    color: '#e8e8e8',
    padding: '10px 12px',
    fontSize: '14px',
    marginBottom: '20px',
    outline: 'none',
  },
  btn: {
    width: '100%',
    background: '#d4af37',
    color: '#1a1a1a',
    border: 'none',
    borderRadius: '3px',
    padding: '12px',
    fontSize: '14px',
    fontWeight: '600',
    letterSpacing: '1px',
    marginTop: '8px',
  },
  error: {
    background: '#3a1a1a',
    border: '1px solid #e05555',
    borderRadius: '3px',
    color: '#e05555',
    padding: '10px 12px',
    fontSize: '13px',
    marginBottom: '16px',
  }
};

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await login(username, password);
      onLogin(data.role);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.logo}>ACEest</div>
        <div style={styles.sub}>Fitness &amp; Gym Management</div>

        {error && <div style={styles.error}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <label style={styles.label}>Username</label>
          <input
            style={styles.input}
            value={username}
            onChange={e => setUsername(e.target.value)}
            autoFocus
          />
          <label style={styles.label}>Password</label>
          <input
            style={styles.input}
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
          />
          <button style={styles.btn} disabled={loading}>
            {loading ? 'Logging in...' : 'LOGIN'}
          </button>
        </form>
      </div>
    </div>
  );
}
