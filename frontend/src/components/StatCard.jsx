import React from 'react'

export default function StatCard({ label, value, sub, color = '#2ecc71' }) {
  return (
    <div style={{ ...styles.card, borderTop: `3px solid ${color}` }}>
      <p style={styles.label}>{label}</p>
      <p style={{ ...styles.value, color }}>{value ?? '—'}</p>
      {sub && <p style={styles.sub}>{sub}</p>}
    </div>
  )
}

const styles = {
  card: {
    background: '#fff', borderRadius: 10, padding: '20px 24px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.07)', minWidth: 160,
  },
  label: { fontSize: 12, color: '#888', textTransform: 'uppercase', letterSpacing: 1 },
  value: { fontSize: 32, fontWeight: 700, margin: '6px 0 2px' },
  sub:   { fontSize: 12, color: '#aaa' },
}