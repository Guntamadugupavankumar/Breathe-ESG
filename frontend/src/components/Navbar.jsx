import React from 'react'
import { NavLink } from 'react-router-dom'

export default function Navbar({ onLogout }) {
  const link = active => ({
    ...styles.link,
    ...(active ? styles.active : {}),
  })

  return (
    <nav style={styles.nav}>
      <span style={styles.brand}>🌿 Breathe ESG</span>
      <div style={styles.links}>
        <NavLink to="/" style={({ isActive }) => link(isActive)}>Dashboard</NavLink>
        <NavLink to="/runs" style={({ isActive }) => link(isActive)}>Ingestion Runs</NavLink>
        <NavLink to="/review" style={({ isActive }) => link(isActive)}>Review</NavLink>
      </div>
      <button onClick={onLogout} style={styles.logout}>Logout</button>
    </nav>
  )
}

const styles = {
  nav: {
    display: 'flex', alignItems: 'center', padding: '0 32px',
    height: 56, background: '#1a1a2e',
    boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
  },
  brand: { color: '#2ecc71', fontWeight: 700, fontSize: 18, marginRight: 40 },
  links: { display: 'flex', gap: 8, flex: 1 },
  link: {
    color: '#aaa', textDecoration: 'none', padding: '6px 14px',
    borderRadius: 6, fontSize: 14, fontWeight: 500,
  },
  active: { color: '#fff', background: 'rgba(46,204,113,0.15)' },
  logout: {
    background: 'transparent', border: '1px solid #555',
    color: '#aaa', padding: '5px 14px', borderRadius: 6,
    cursor: 'pointer', fontSize: 13,
  },
}