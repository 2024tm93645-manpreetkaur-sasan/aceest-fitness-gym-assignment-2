import React, { useState } from 'react';
import './index.css';
import LoginPage from './components/LoginPage';
import Dashboard from './components/Dashboard';
import { logout } from './api';

export default function App() {
  const [role, setRole] = useState(() => localStorage.getItem('role'));

  function handleLogin(r) { setRole(r); }
  function handleLogout() { logout(); setRole(null); }

  if (!role || !localStorage.getItem('token')) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return <Dashboard role={role} onLogout={handleLogout} />;
}
