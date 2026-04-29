import React, { useState, useEffect, useCallback } from 'react';
import {
  getClients, addClient, deleteClient,
  getPrograms, assignProgram, getReportUrl
} from '../api';
import ClientDetail from './ClientDetail';

const s = {
  layout: { display: 'flex', height: '100vh', overflow: 'hidden' },
  sidebar: {
    width: '260px', minWidth: '260px',
    background: '#1e1e1e',
    borderRight: '1px solid #2e2e2e',
    display: 'flex', flexDirection: 'column',
  },
  sideHeader: {
    background: '#d4af37',
    padding: '16px 20px',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
  },
  sideTitle: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: '22px', color: '#1a1a1a', letterSpacing: '1px',
  },
  roleTag: {
    background: '#1a1a1a', color: '#d4af37',
    fontSize: '10px', padding: '3px 8px', borderRadius: '2px',
    letterSpacing: '1px', textTransform: 'uppercase',
  },
  searchBox: {
    padding: '12px 14px',
    borderBottom: '1px solid #2e2e2e',
  },
  searchInput: {
    width: '100%', background: '#2a2a2a',
    border: '1px solid #3a3a3a', borderRadius: '3px',
    color: '#e8e8e8', padding: '8px 10px', fontSize: '13px', outline: 'none',
  },
  clientList: { flex: 1, overflowY: 'auto' },
  clientItem: {
    padding: '12px 16px', cursor: 'pointer',
    borderBottom: '1px solid #262626',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    transition: 'background 0.1s',
  },
  clientName: { fontSize: '13px', fontWeight: '500' },
  clientStatus: {
    fontSize: '10px', padding: '2px 6px', borderRadius: '10px',
    background: '#1a3a2a', color: '#4caf7d',
  },
  sideFooter: {
    padding: '12px 14px',
    borderTop: '1px solid #2e2e2e',
    display: 'flex', gap: '8px',
  },
  btnGold: {
    flex: 1, background: '#d4af37', color: '#1a1a1a',
    border: 'none', borderRadius: '3px', padding: '9px',
    fontSize: '12px', fontWeight: '600', letterSpacing: '0.5px',
  },
  btnGhost: {
    flex: 1, background: 'transparent', color: '#888',
    border: '1px solid #3a3a3a', borderRadius: '3px', padding: '9px',
    fontSize: '12px',
  },
  main: { flex: 1, overflow: 'auto', background: '#1a1a1a' },
  empty: {
    display: 'flex', flexDirection: 'column',
    alignItems: 'center', justifyContent: 'center',
    height: '100%', color: '#444',
  },
  emptyIcon: { fontSize: '48px', marginBottom: '16px' },
  emptyText: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: '22px', letterSpacing: '2px', color: '#555',
  },
  modal: {
    position: 'fixed', inset: 0,
    background: 'rgba(0,0,0,0.7)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 100,
  },
  modalCard: {
    background: '#242424', border: '1px solid #3a3a3a',
    borderTop: '3px solid #d4af37',
    borderRadius: '4px', padding: '32px', width: '360px',
  },
  modalTitle: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: '22px', color: '#d4af37',
    marginBottom: '20px', letterSpacing: '1px',
  },
  label: {
    display: 'block', color: '#888',
    fontSize: '11px', letterSpacing: '1px',
    textTransform: 'uppercase', marginBottom: '6px',
  },
  input: {
    width: '100%', background: '#1a1a1a',
    border: '1px solid #3a3a3a', borderRadius: '3px',
    color: '#e8e8e8', padding: '9px 12px', fontSize: '13px',
    marginBottom: '16px', outline: 'none',
  },
  modalBtns: { display: 'flex', gap: '10px', marginTop: '8px' },
};

export default function Dashboard({ role, onLogout }) {
  const [clients, setClients]       = useState([]);
  const [filtered, setFiltered]     = useState([]);
  const [search, setSearch]         = useState('');
  const [selected, setSelected]     = useState(null);
  const [programs, setPrograms]     = useState([]);
  const [showAdd, setShowAdd]       = useState(false);
  const [newName, setNewName]       = useState('');
  const [newAge, setNewAge]         = useState('');
  const [newWeight, setNewWeight]   = useState('');
  const [error, setError]           = useState('');

  const loadClients = useCallback(async () => {
    const data = await getClients();
    setClients(data);
    setFiltered(data);
  }, []);

  useEffect(() => { loadClients(); }, [loadClients]);
  useEffect(() => {
    getPrograms().then(p => setPrograms(Array.isArray(p) ? p : Object.keys(p)));
  }, []);

  useEffect(() => {
    if (!search) { setFiltered(clients); return; }
    setFiltered(clients.filter(c =>
      c.name.toLowerCase().includes(search.toLowerCase())
    ));
  }, [search, clients]);

  async function handleAdd() {
    if (!newName.trim()) { setError('Name is required'); return; }
    try {
      await addClient({ name: newName.trim(), age: newAge ? +newAge : undefined, weight: newWeight ? +newWeight : undefined });
      setShowAdd(false); setNewName(''); setNewAge(''); setNewWeight(''); setError('');
      loadClients();
    } catch (e) { setError(e.message); }
  }

  async function handleDelete(name) {
    if (!window.confirm(`Delete client "${name}"?`)) return;
    await deleteClient(name);
    if (selected?.name === name) setSelected(null);
    loadClients();
  }

  async function handleDownloadReport(name) {
    const token = localStorage.getItem('token');
    const res = await fetch(getReportUrl(name), {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) return alert('Failed to generate report');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `${name}_report.pdf`; a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div style={s.layout}>
      {/* Sidebar */}
      <div style={s.sidebar}>
        <div style={s.sideHeader}>
          <span style={s.sideTitle}>ACEest</span>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span style={s.roleTag}>{role}</span>
            <button
              onClick={onLogout}
              style={{ background: 'none', border: 'none', color: '#1a1a1a', cursor: 'pointer', fontSize: '18px' }}
              title="Logout"
            >⏻</button>
          </div>
        </div>

        <div style={s.searchBox}>
          <input
            style={s.searchInput}
            placeholder="Search clients..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        <div style={s.clientList}>
          {filtered.map(c => (
            <div
              key={c.name}
              style={{
                ...s.clientItem,
                background: selected?.name === c.name ? '#2a2a2a' : 'transparent',
                borderLeft: selected?.name === c.name ? '3px solid #d4af37' : '3px solid transparent',
              }}
              onClick={() => setSelected(c)}
            >
              <div>
                <div style={s.clientName}>{c.name}</div>
                <div style={{ fontSize: '11px', color: '#666', marginTop: '2px' }}>
                  {c.program || 'No program'}
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                <span style={s.clientStatus}>{c.membership_status}</span>
              </div>
            </div>
          ))}
          {filtered.length === 0 && (
            <div style={{ padding: '24px', color: '#555', textAlign: 'center', fontSize: '12px' }}>
              No clients found
            </div>
          )}
        </div>

        <div style={s.sideFooter}>
          <button style={s.btnGold} onClick={() => setShowAdd(true)}>+ Add Client</button>
          <button style={s.btnGhost} onClick={onLogout}>Logout</button>
        </div>
      </div>

      {/* Main content */}
      <div style={s.main}>
        {selected ? (
          <ClientDetail
            client={selected}
            programs={programs}
            onAssignProgram={async (prog) => {
              await assignProgram(selected.name, prog);
              loadClients();
            }}
            onDelete={() => handleDelete(selected.name)}
            onDownloadReport={() => handleDownloadReport(selected.name)}
            onRefresh={loadClients}
          />
        ) : (
          <div style={s.empty}>
            <div style={s.emptyIcon}>🏋️</div>
            <div style={s.emptyText}>Select a client to view details</div>
            <div style={{ color: '#444', fontSize: '13px', marginTop: '8px' }}>
              {clients.length} client{clients.length !== 1 ? 's' : ''} registered
            </div>
          </div>
        )}
      </div>

      {/* Add Client Modal */}
      {showAdd && (
        <div style={s.modal} onClick={() => setShowAdd(false)}>
          <div style={s.modalCard} onClick={e => e.stopPropagation()}>
            <div style={s.modalTitle}>Add New Client</div>
            {error && (
              <div style={{ background: '#3a1a1a', border: '1px solid #e05555', borderRadius: '3px', color: '#e05555', padding: '8px 12px', fontSize: '12px', marginBottom: '12px' }}>
                {error}
              </div>
            )}
            <label style={s.label}>Name *</label>
            <input style={s.input} value={newName} onChange={e => setNewName(e.target.value)} autoFocus />
            <label style={s.label}>Age</label>
            <input style={s.input} type="number" value={newAge} onChange={e => setNewAge(e.target.value)} />
            <label style={s.label}>Weight (kg)</label>
            <input style={s.input} type="number" value={newWeight} onChange={e => setNewWeight(e.target.value)} />
            <div style={s.modalBtns}>
              <button style={s.btnGold} onClick={handleAdd}>Save</button>
              <button style={{ ...s.btnGhost, flex: 1 }} onClick={() => { setShowAdd(false); setError(''); }}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
