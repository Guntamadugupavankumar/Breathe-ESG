import React, { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Runs from './pages/Runs'
import ReviewPage from './pages/ReviewPage'
import api from './api/client'

export default function App() {
  const [authed, setAuthed] = useState(!!localStorage.getItem('access'))
  const [creds, setCreds] = useState({ username: '', password: '' })
  const [err, setErr] = useState('')

  async function login(e) {
    e.preventDefault()
    setErr('')
    try {
      const { data } = await api.post('/token/', creds)
      localStorage.setItem('access', data.access)
      localStorage.setItem('refresh', data.refresh)
      setAuthed(true)
    } catch {
      setErr('Invalid username or password.')
    }
  }

  function logout() {
    localStorage.clear()
    setAuthed(false)
  }

  if (!authed) return (
    <div style={styles.loginWrap}>
      <div style={styles.loginBox}>
        <h1 style={styles.loginTitle}>🌿 Breathe ESG</h1>
        <p style={styles.loginSub}>Emissions Review Platform</p>
        {err && <p style={styles.err}>{err}</p>}
        <form onSubmit={login}>
          <input
            style={styles.input}
            placeholder="Username"
            value={creds.username}
            onChange={e => setCreds(p => ({ ...p, username: e.target.value }))}
          />
          <input
            style={styles.input}
            type="password"
            placeholder="Password"
            value={creds.password}
            onChange={e => setCreds(p => ({ ...p, password: e.target.value }))}
          />
          <button style={styles.btn} type="submit">Sign in</button>
        </form>
      </div>
    </div>
  )

  return (
    <BrowserRouter>
      <Navbar onLogout={logout} />
      <div style={{ padding: '24px 32px' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

const styles = {
  loginWrap: {
    minHeight: '100vh', display: 'flex',
    alignItems: 'center', justifyContent: 'center',
    background: 'linear-gradient(135deg,#1a1a2e,#16213e)',
  },
  loginBox: {
    background: '#fff', borderRadius: 12, padding: 40,
    width: 360, boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
  },
  loginTitle: { fontSize: 28, fontWeight: 700, color: '#1a1a2e', marginBottom: 4 },
  loginSub:   { color: '#666', marginBottom: 24, fontSize: 14 },
  err:        { background: '#fee', color: '#c00', borderRadius: 6, padding: '8px 12px', marginBottom: 16, fontSize: 13 },
  input: {
    width: '100%', padding: '10px 14px', marginBottom: 12,
    border: '1px solid #ddd', borderRadius: 8, fontSize: 14,
    display: 'block',
  },
  btn: {
    width: '100%', padding: '11px', background: '#2ecc71',
    color: '#fff', border: 'none', borderRadius: 8,
    fontWeight: 600, fontSize: 15, cursor: 'pointer',
  },
}