const BASE = process.env.REACT_APP_API_URL || '';

function getToken() {
  return localStorage.getItem('token');
}

function authHeaders() {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${getToken()}`
  };
}

export async function login(username, password) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Login failed');
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('role', data.role);
  return data;
}

export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
}

export function getRole() {
  return localStorage.getItem('role');
}

export async function getClients() {
  const res = await fetch(`${BASE}/clients`, { headers: authHeaders() });
  return res.json();
}

export async function getClient(name) {
  const res = await fetch(`${BASE}/clients/${encodeURIComponent(name)}`, { headers: authHeaders() });
  return res.json();
}

export async function addClient(data) {
  const res = await fetch(`${BASE}/clients`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || 'Failed to add client');
  return json;
}

export async function deleteClient(name) {
  const res = await fetch(`${BASE}/clients/${encodeURIComponent(name)}`, {
    method: 'DELETE', headers: authHeaders()
  });
  return res.json();
}

export async function getPrograms() {
  const res = await fetch(`${BASE}/programs`, { headers: authHeaders() });
  return res.json();
}

export async function assignProgram(name, program) {
  const res = await fetch(`${BASE}/clients/${encodeURIComponent(name)}/program`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify({ program })
  });
  return res.json();
}

export async function getWorkouts(name) {
  const res = await fetch(`${BASE}/clients/${encodeURIComponent(name)}/workouts`, { headers: authHeaders() });
  return res.json();
}

export async function addWorkout(name, data) {
  const res = await fetch(`${BASE}/clients/${encodeURIComponent(name)}/workouts`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || 'Failed to add workout');
  return json;
}

export async function getProgress(name) {
  const res = await fetch(`${BASE}/clients/${encodeURIComponent(name)}/progress`, { headers: authHeaders() });
  return res.json();
}

export async function addProgress(name, data) {
  const res = await fetch(`${BASE}/clients/${encodeURIComponent(name)}/progress`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || 'Failed to add progress');
  return json;
}

export async function getMetrics(name) {
  const res = await fetch(`${BASE}/clients/${encodeURIComponent(name)}/metrics`, { headers: authHeaders() });
  return res.json();
}

export async function addMetrics(name, data) {
  const res = await fetch(`${BASE}/clients/${encodeURIComponent(name)}/metrics`, {
    method: 'POST', headers: authHeaders(), body: JSON.stringify(data)
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || 'Failed to add metrics');
  return json;
}

export function getReportUrl(name) {
  return `${BASE}/clients/${encodeURIComponent(name)}/report`;
}
