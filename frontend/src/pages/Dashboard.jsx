import React, { useEffect, useState } from 'react'
import StatCard from '../components/StatCard'
import api from '../api/client'

export default function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    api.get('/dashboard/').then(r => setStats(r.data))
  }, [])

  if (!stats) return <p style={{ color: '#aaa', marginTop: 40, textAlign: 'center' }}>Loading…</p>

  const rb = stats.review_breakdown
  const se = stats.scope_emissions

  return (
    <div>
      <h2 style={styles.heading}>Dashboard</h2>

      <div style={styles.grid}>
        <StatCard label="Total Rows" value={stats.total_rows} color="#3b82f6" />
        <StatCard
          label="Total Emissions"
          value={(stats.total_kgco2e / 1000).toFixed(1) + ' tCO₂e'}
          color="#2ecc71"
        />
        <StatCard label="Pending Review" value={rb.PENDING || 0} color="#f59e0b" />
        <StatCard label="Flagged" value={rb.FLAGGED || 0} color="#ef4444" />
        <StatCard label="Approved" value={rb.APPROVED || 0} color="#22c55e" />
        <StatCard label="Rejected" value={rb.REJECTED || 0} color="#a855f7" />
      </div>

      <div style={styles.row}>
        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>Emissions by Scope</h3>
          {Object.entries(se).map(([scope, val]) => (
            <div key={scope} style={styles.scopeRow}>
              <span style={{ color: scopeColor(scope), fontWeight: 600 }}>{scope}</span>
              <span>{(val / 1000).toFixed(2)} tCO₂e</span>
            </div>
          ))}
        </div>

        <div style={styles.panel}>
          <h3 style={styles.panelTitle}>Recent Ingestion Runs</h3>
          {stats.recent_runs.map(run => (
            <div key={run.id} style={styles.runRow}>
              <div>
                <span style={styles.runType}>{run.source_type_display}</span>
                <span style={{ fontSize: 12, color: '#aaa', marginLeft: 8 }}>
                  {new Date(run.uploaded_at).toLocaleString()}
                </span>
              </div>
              <div style={{ fontSize: 12 }}>
                <span style={statusBadge(run.status)}>{run.status}</span>
                <span style={{ color: '#888', marginLeft: 8 }}>{run.row_count} rows</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function scopeColor(s) {
  if (s === 'SCOPE_1') return '#ef4444'
  if (s === 'SCOPE_2') return '#f59e0b'
  return '#3b82f6'
}

function statusBadge(s) {
  const map = { DONE: '#22c55e', FAILED: '#ef4444', PROCESSING: '#f59e0b', PENDING: '#aaa' }
  return { color: map[s] || '#aaa', fontWeight: 600 }
}

const styles = {
  heading:    { fontSize: 22, fontWeight: 700, marginBottom: 24 },
  grid:       { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px,1fr))', gap: 16, marginBottom: 32 },
  row:        { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 },
  panel:      { background: '#fff', borderRadius: 10, padding: 24, boxShadow: '0 2px 8px rgba(0,0,0,0.07)' },
  panelTitle: { fontSize: 15, fontWeight: 600, marginBottom: 16, color: '#333' },
  scopeRow:   { display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid #f0f0f0', fontSize: 14 },
  runRow:     { padding: '10px 0', borderBottom: '1px solid #f0f0f0' },
  runType:    { fontWeight: 600, fontSize: 13 },
}