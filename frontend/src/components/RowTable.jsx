import React, { useState } from 'react'
import api from '../api/client'

const BADGE = {
  PENDING:  { bg: '#fff8e1', color: '#f59e0b' },
  FLAGGED:  { bg: '#fef2f2', color: '#ef4444' },
  APPROVED: { bg: '#f0fdf4', color: '#22c55e' },
  REJECTED: { bg: '#fdf2f8', color: '#a855f7' },
}

function Badge({ status }) {
  const s = BADGE[status] || { bg: '#eee', color: '#666' }
  return (
    <span style={{
      background: s.bg, color: s.color,
      padding: '2px 10px', borderRadius: 20,
      fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
    }}>
      {status}
    </span>
  )
}

export default function RowTable({ rows, onRefresh }) {
  const [acting, setActing] = useState(null)

  async function act(rowId, action) {
    setActing(rowId + action)
    try {
      await api.post(`/rows/${rowId}/${action}/`)
      onRefresh()
    } finally {
      setActing(null)
    }
  }

  if (!rows.length) return (
    <p style={{ color: '#aaa', textAlign: 'center', padding: 40 }}>No rows found.</p>
  )

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={styles.table}>
        <thead>
          <tr style={styles.thead}>
            {['Scope','Category','Subcategory','Quantity','Unit','kgCO₂e','Date','Status','Source','Actions'].map(h => (
              <th key={h} style={styles.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.id} style={styles.tr}>
              <td style={styles.td}>
                <span style={{ fontWeight: 600, color: scopeColor(r.scope) }}>{r.scope_display}</span>
              </td>
              <td style={styles.td}>{r.category}</td>
              <td style={styles.td}>{r.subcategory}</td>
              <td style={styles.td}>{r.raw_quantity}</td>
              <td style={styles.td}>{r.raw_unit}</td>
              <td style={styles.td}>
                {r.quantity_kgco2e != null
                  ? Number(r.quantity_kgco2e).toLocaleString(undefined, { maximumFractionDigits: 2 })
                  : <span style={{ color: '#ccc' }}>—</span>}
              </td>
              <td style={styles.td}>{r.activity_date || r.period_start || '—'}</td>
              <td style={styles.td}>
                <Badge status={r.review_status} />
                {r.flagged_reason && (
                  <p style={{ fontSize: 10, color: '#ef4444', marginTop: 2 }}>{r.flagged_reason}</p>
                )}
              </td>
              <td style={styles.td}>{r.source_type}</td>
              <td style={styles.td}>
                {!r.audit_locked && r.review_status !== 'APPROVED' && (
                  <button
                    style={styles.approve}
                    disabled={!!acting}
                    onClick={() => act(r.id, 'approve')}
                  >✓ Approve</button>
                )}
                {!r.audit_locked && r.review_status !== 'FLAGGED' && (
                  <button
                    style={styles.flag}
                    disabled={!!acting}
                    onClick={() => act(r.id, 'flag')}
                  >⚑ Flag</button>
                )}
                {!r.audit_locked && r.review_status !== 'REJECTED' && (
                  <button
                    style={styles.reject}
                    disabled={!!acting}
                    onClick={() => act(r.id, 'reject')}
                  >✕ Reject</button>
                )}
                {r.review_status === 'APPROVED' && !r.audit_locked && (
                  <button
                    style={styles.lock}
                    disabled={!!acting}
                    onClick={() => act(r.id, 'lock')}
                  >🔒 Lock</button>
                )}
                {r.audit_locked && (
                  <span style={{ fontSize: 11, color: '#888' }}>🔒 Locked</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function scopeColor(scope) {
  if (scope === 'SCOPE_1') return '#ef4444'
  if (scope === 'SCOPE_2') return '#f59e0b'
  return '#3b82f6'
}

const styles = {
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  thead: { background: '#f8f9fa' },
  th: { padding: '10px 12px', textAlign: 'left', fontWeight: 600, color: '#555', borderBottom: '2px solid #eee', whiteSpace: 'nowrap' },
  tr: { borderBottom: '1px solid #f0f0f0' },
  td: { padding: '10px 12px', verticalAlign: 'top' },
  approve: { background: '#f0fdf4', color: '#22c55e', border: '1px solid #bbf7d0', borderRadius: 5, padding: '3px 8px', fontSize: 11, cursor: 'pointer', marginRight: 4, marginBottom: 4, display: 'inline-block' },
  flag:    { background: '#fef2f2', color: '#ef4444', border: '1px solid #fecaca', borderRadius: 5, padding: '3px 8px', fontSize: 11, cursor: 'pointer', marginRight: 4, marginBottom: 4, display: 'inline-block' },
  reject:  { background: '#fdf2f8', color: '#a855f7', border: '1px solid #e9d5ff', borderRadius: 5, padding: '3px 8px', fontSize: 11, cursor: 'pointer', marginRight: 4, marginBottom: 4, display: 'inline-block' },
  lock:    { background: '#fff8e1', color: '#f59e0b', border: '1px solid #fde68a', borderRadius: 5, padding: '3px 8px', fontSize: 11, cursor: 'pointer', marginRight: 4, marginBottom: 4, display: 'inline-block' },
}