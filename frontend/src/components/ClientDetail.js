import React, { useState, useEffect, useCallback } from 'react';
import { getWorkouts, addWorkout, getProgress, addProgress, getMetrics, addMetrics } from '../api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const WORKOUT_TYPES = ['Strength', 'Hypertrophy', 'Cardio', 'Mobility'];

const s = {
  container: { height: '100vh', display: 'flex', flexDirection: 'column' },
  header: {
    background: '#242424',
    borderBottom: '1px solid #2e2e2e',
    padding: '20px 28px',
    display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between',
  },
  clientName: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: '28px', color: '#d4af37', letterSpacing: '1px',
  },
  meta: { color: '#666', fontSize: '12px', marginTop: '4px' },
  headerActions: { display: 'flex', gap: '8px' },
  btnGold: {
    background: '#d4af37', color: '#1a1a1a',
    border: 'none', borderRadius: '3px', padding: '8px 16px',
    fontSize: '12px', fontWeight: '600', letterSpacing: '0.5px',
  },
  btnDanger: {
    background: 'transparent', color: '#e05555',
    border: '1px solid #e05555', borderRadius: '3px', padding: '8px 16px',
    fontSize: '12px',
  },
  programRow: {
    background: '#1e1e1e', borderBottom: '1px solid #2a2a2a',
    padding: '12px 28px', display: 'flex', alignItems: 'center', gap: '12px',
  },
  programLabel: { color: '#666', fontSize: '11px', letterSpacing: '1px', textTransform: 'uppercase' },
  programSelect: {
    background: '#2a2a2a', border: '1px solid #3a3a3a', borderRadius: '3px',
    color: '#e8e8e8', padding: '6px 10px', fontSize: '13px', outline: 'none',
  },
  tabs: {
    display: 'flex', borderBottom: '1px solid #2e2e2e',
    background: '#1e1e1e', padding: '0 28px',
  },
  tab: {
    padding: '12px 20px', cursor: 'pointer',
    fontSize: '12px', letterSpacing: '1px', textTransform: 'uppercase',
    border: 'none', background: 'none', color: '#666',
    borderBottom: '2px solid transparent',
  },
  tabActive: { color: '#d4af37', borderBottom: '2px solid #d4af37' },
  content: { flex: 1, overflow: 'auto', padding: '24px 28px' },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: {
    textAlign: 'left', padding: '10px 12px',
    fontSize: '11px', color: '#666', letterSpacing: '1px', textTransform: 'uppercase',
    borderBottom: '1px solid #2e2e2e', background: '#1e1e1e',
  },
  td: {
    padding: '12px', fontSize: '13px',
    borderBottom: '1px solid #242424', color: '#ccc',
  },
  addBtn: {
    background: '#d4af37', color: '#1a1a1a', border: 'none',
    borderRadius: '3px', padding: '8px 16px',
    fontSize: '12px', fontWeight: '600', marginBottom: '16px',
  },
  empty: { color: '#444', textAlign: 'center', padding: '40px', fontSize: '13px' },
  modal: {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
  },
  modalCard: {
    background: '#242424', border: '1px solid #3a3a3a',
    borderTop: '3px solid #d4af37', borderRadius: '4px',
    padding: '28px', width: '340px',
  },
  modalTitle: {
    fontFamily: "'Bebas Neue', sans-serif",
    fontSize: '20px', color: '#d4af37', marginBottom: '18px', letterSpacing: '1px',
  },
  label: {
    display: 'block', color: '#888', fontSize: '11px',
    letterSpacing: '1px', textTransform: 'uppercase', marginBottom: '5px',
  },
  input: {
    width: '100%', background: '#1a1a1a', border: '1px solid #3a3a3a',
    borderRadius: '3px', color: '#e8e8e8', padding: '8px 10px',
    fontSize: '13px', marginBottom: '14px', outline: 'none',
  },
  select: {
    width: '100%', background: '#1a1a1a', border: '1px solid #3a3a3a',
    borderRadius: '3px', color: '#e8e8e8', padding: '8px 10px',
    fontSize: '13px', marginBottom: '14px', outline: 'none',
  },
  modalBtns: { display: 'flex', gap: '8px', marginTop: '4px' },
  error: {
    background: '#3a1a1a', border: '1px solid #e05555', borderRadius: '3px',
    color: '#e05555', padding: '8px 10px', fontSize: '12px', marginBottom: '12px',
  },
};

export default function ClientDetail({ client, programs, onAssignProgram, onDelete, onDownloadReport, onRefresh }) {
  const [tab, setTab]             = useState('workouts');
  const [workouts, setWorkouts]   = useState([]);
  const [progress, setProgress]   = useState([]);
  const [metrics, setMetrics]     = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm]           = useState({});
  const [formError, setFormError] = useState('');
  const [selProgram, setSelProgram] = useState(client.program || '');

  const load = useCallback(async () => {
    const [w, p, m] = await Promise.all([
      getWorkouts(client.name),
      getProgress(client.name),
      getMetrics(client.name),
    ]);
    setWorkouts(Array.isArray(w) ? w : []);
    setProgress(Array.isArray(p) ? p : []);
    setMetrics(Array.isArray(m) ? m : []);
  }, [client.name]);

  useEffect(() => { load(); setSelProgram(client.program || ''); }, [client.name, load, client.program]);

  function openModal() { setForm({}); setFormError(''); setShowModal(true); }

  async function handleSave() {
    setFormError('');
    try {
      if (tab === 'workouts') {
        await addWorkout(client.name, { workout_type: form.type, duration_min: +form.duration, notes: form.notes });
      } else if (tab === 'progress') {
        await addProgress(client.name, { week: form.week, adherence: +form.adherence });
      } else if (tab === 'metrics') {
        await addMetrics(client.name, { weight_kg: +form.weight_kg, body_fat_pct: form.body_fat ? +form.body_fat : undefined, date: form.date, notes: form.notes });
      }
      setShowModal(false); load(); onRefresh();
    } catch (e) { setFormError(e.message); }
  }

  async function handleAssign() {
    if (!selProgram) return;
    await onAssignProgram(selProgram);
  }

  const tabs = ['workouts', 'progress', 'metrics'];

  return (
    <div style={s.container}>
      {/* Header */}
      <div style={s.header}>
        <div>
          <div style={s.clientName}>{client.name}</div>
          <div style={s.meta}>
            {client.age ? `Age: ${client.age}` : ''}{client.age && client.weight ? ' · ' : ''}
            {client.weight ? `Weight: ${client.weight} kg` : ''}{(client.age || client.weight) ? ' · ' : ''}
            Membership: <span style={{ color: '#4caf7d' }}>{client.membership_status}</span>
          </div>
        </div>
        <div style={s.headerActions}>
          <button style={s.btnGold} onClick={onDownloadReport}>⬇ PDF Report</button>
          <button style={s.btnDanger} onClick={onDelete}>Delete</button>
        </div>
      </div>

      {/* Program row */}
      <div style={s.programRow}>
        <span style={s.programLabel}>Program</span>
        <select
          style={s.programSelect}
          value={selProgram}
          onChange={e => setSelProgram(e.target.value)}
        >
          <option value="">-- Select --</option>
          {programs.map(p => <option key={p} value={p}>{p}</option>)}
        </select>
        <button style={{ ...s.btnGold, padding: '6px 14px' }} onClick={handleAssign}>Assign</button>
        {client.program && (
          <span style={{ color: '#4caf7d', fontSize: '12px' }}>
            Current: <strong>{client.program}</strong>
          </span>
        )}
      </div>

      {/* Tabs */}
      <div style={s.tabs}>
        {tabs.map(t => (
          <button
            key={t}
            style={{ ...s.tab, ...(tab === t ? s.tabActive : {}) }}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={s.content}>
        <button style={s.addBtn} onClick={openModal}>
          + Add {tab.slice(0, -1)}
        </button>

        {tab === 'workouts' && (
          workouts.length === 0 ? <div style={s.empty}>No workouts logged yet</div> : (
            <table style={s.table}>
              <thead>
                <tr>
                  {['Date', 'Type', 'Duration', 'Notes'].map(h => (
                    <th key={h} style={s.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {workouts.map((w, i) => (
                  <tr key={i}>
                    <td style={s.td}>{w.date}</td>
                    <td style={s.td}><span style={{ background: '#2a2a2a', padding: '2px 8px', borderRadius: '10px', fontSize: '12px' }}>{w.workout_type}</span></td>
                    <td style={s.td}>{w.duration_min} min</td>
                    <td style={{ ...s.td, color: '#666' }}>{w.notes || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}

        {tab === 'progress' && (
          <>
            {progress.length > 0 && (
              <div style={{ marginBottom: '24px', background: '#1e1e1e', borderRadius: '4px', padding: '16px' }}>
                <div style={{ fontFamily: "'Bebas Neue'", fontSize: '16px', color: '#d4af37', marginBottom: '12px', letterSpacing: '1px' }}>
                  Weekly Adherence
                </div>
                <ResponsiveContainer width="100%" height={180}>
                  <LineChart data={progress}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                    <XAxis dataKey="week" tick={{ fill: '#666', fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fill: '#666', fontSize: 11 }} />
                    <Tooltip contentStyle={{ background: '#242424', border: '1px solid #3a3a3a', color: '#e8e8e8' }} />
                    <Line type="monotone" dataKey="adherence" stroke="#d4af37" strokeWidth={2} dot={{ fill: '#d4af37' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            {progress.length === 0 ? <div style={s.empty}>No progress entries yet</div> : (
              <table style={s.table}>
                <thead>
                  <tr>
                    {['Week', 'Adherence'].map(h => <th key={h} style={s.th}>{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {progress.map((p, i) => (
                    <tr key={i}>
                      <td style={s.td}>{p.week || `Week ${i + 1}`}</td>
                      <td style={s.td}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div style={{ flex: 1, background: '#2a2a2a', borderRadius: '10px', height: '6px' }}>
                            <div style={{ width: `${p.adherence}%`, background: p.adherence >= 70 ? '#4caf7d' : '#e05555', height: '6px', borderRadius: '10px' }} />
                          </div>
                          <span style={{ color: p.adherence >= 70 ? '#4caf7d' : '#e05555', fontSize: '13px', minWidth: '36px' }}>{p.adherence}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}

        {tab === 'metrics' && (
          metrics.length === 0 ? <div style={s.empty}>No metrics recorded yet</div> : (
            <table style={s.table}>
              <thead>
                <tr>
                  {['Date', 'Weight (kg)', 'Body Fat %', 'Notes'].map(h => (
                    <th key={h} style={s.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {metrics.map((m, i) => (
                  <tr key={i}>
                    <td style={s.td}>{m.date}</td>
                    <td style={s.td}>{m.weight_kg ?? '-'}</td>
                    <td style={s.td}>{m.body_fat_pct != null ? `${m.body_fat_pct}%` : '-'}</td>
                    <td style={{ ...s.td, color: '#666' }}>{m.notes || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        )}
      </div>

      {/* Add Modal */}
      {showModal && (
        <div style={s.modal} onClick={() => setShowModal(false)}>
          <div style={s.modalCard} onClick={e => e.stopPropagation()}>
            <div style={s.modalTitle}>Add {tab.slice(0, -1)}</div>
            {formError && <div style={s.error}>{formError}</div>}

            {tab === 'workouts' && <>
              <label style={s.label}>Type</label>
              <select style={s.select} value={form.type || ''} onChange={e => setForm({ ...form, type: e.target.value })}>
                <option value="">-- Select --</option>
                {WORKOUT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <label style={s.label}>Duration (min)</label>
              <input style={s.input} type="number" value={form.duration || ''} onChange={e => setForm({ ...form, duration: e.target.value })} />
              <label style={s.label}>Notes</label>
              <input style={s.input} value={form.notes || ''} onChange={e => setForm({ ...form, notes: e.target.value })} />
            </>}

            {tab === 'progress' && <>
              <label style={s.label}>Week</label>
              <input style={s.input} placeholder="e.g. Week 1" value={form.week || ''} onChange={e => setForm({ ...form, week: e.target.value })} />
              <label style={s.label}>Adherence (0-100)</label>
              <input style={s.input} type="number" min="0" max="100" value={form.adherence || ''} onChange={e => setForm({ ...form, adherence: e.target.value })} />
            </>}

            {tab === 'metrics' && <>
              <label style={s.label}>Date</label>
              <input style={s.input} type="date" value={form.date || new Date().toISOString().split('T')[0]} onChange={e => setForm({ ...form, date: e.target.value })} />
              <label style={s.label}>Weight (kg)</label>
              <input style={s.input} type="number" step="0.1" value={form.weight_kg || ''} onChange={e => setForm({ ...form, weight_kg: e.target.value })} />
              <label style={s.label}>Body Fat %</label>
              <input style={s.input} type="number" step="0.1" value={form.body_fat || ''} onChange={e => setForm({ ...form, body_fat: e.target.value })} />
              <label style={s.label}>Notes</label>
              <input style={s.input} value={form.notes || ''} onChange={e => setForm({ ...form, notes: e.target.value })} />
            </>}

            <div style={s.modalBtns}>
              <button style={{ ...s.btnGold, flex: 1 }} onClick={handleSave}>Save</button>
              <button style={{ flex: 1, background: 'transparent', color: '#888', border: '1px solid #3a3a3a', borderRadius: '3px', padding: '8px', fontSize: '12px' }} onClick={() => setShowModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
