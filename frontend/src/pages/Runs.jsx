import React, { useEffect, useState } from 'react'
import UploadModal from '../components/UploadModal'
import api from '../api/client'

export default function Runs() {
  const [runs, setRuns] = useState([])
  const [showUpload, setShowUpload] = useState(false)
  const [expanded, setExpanded] = useState(null)

  function load() {
    api.get('/runs/').then(r => setRuns(r.data.results || r.data))
  }

  useEffect(() => { load() }, [])

  return (
    <div>
      <div style={styles.header}>
        <h2 style={styles.heading}>Ingestion Runs</h2>
        <button style={styles.btn} onClick={() => setShowUpload(true)}>+ Upload File</button>
      </div>

      {showUpload && (
        <UploadModal onClose={() => setShowUpload(false)} onDone={load} />
      )}

      <div style={styles.list}>
        {runs.map(run => (
          <div key={run.id} style={styles.card}>
            <div style={styles.cardHeader} onClick={() => setExpanded(expanded === run.id ? null : run.id)}>
              <div>
                <span style={styles.sourceType}>{run.source_type_display}</span>
                <span style={styles.runId}>{run.id.slice(0, 8)}…</span>
              </div>
              <div style={styles.meta}>
                <span style={statusStyle(run.status)}>{run.status}</span>
                <span style={styles.metaItem}>{run.row_count} rows</span>
                {run.error_count > 0 && (
                  <span style={styles.errCount}>{run.error_count} errors</span>
                )}
                <span style={styles.metaItem}>{new Date(run.uploaded_at).toLocaleString()}</span>
                <span style={styles.chevron}>{expanded === run.id ? '▲' : '▼'}</span>
              </div>
            </div>

            {expanded === run.id && run.error_log?.length > 0 && (
              <div style={styles.errorLog}>
                <p style={styles.errTitle}>Parse Errors / Warnings</p>
                {run.error_log.map((e, i) => (
                  <p key={i} style={styles.errLine}>
                    <strong>Row {e.row}</strong> [{e.field}] — {e.message}
                  </p>
                ))}
              </div>
            )}

            {expanded === run.id && (!run.error_log || run.error_log.length === 0) && (
              <p style={{ padding: '12px 20px', color: '#aaa', fontSize: 13 }}>No errors logged.</p>
            )}
          </div>
        ))}

        {runs.length === 0 && (
          <p style={{ color: '#aaa', textAlign: 'center', padding: 60 }}>
            No runs yet. Upload a file to get started.
          </p>
        )}
      </div>
    </div>
  )
}

function statusStyle(s) {
  const map = { DONE: '#22c55e', FAILED: '#ef4444', PROCESSING: '#f59e0b', PENDING: '#888' }
  return { color: map[s] || '#888', fontWeight: 700, fontSize: 12, textTransform: 'uppercase' }
}

const styles = {
  header:     { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  heading:    { fontSize: 22, fontWeight: 700 },
  btn:        { background: '#2ecc71', color: '#fff', border: 'none', borderRadius: 8, padding: '9px 20px', fontWeight: 600, cursor: 'pointer' },
  list:       { display: 'flex', flexDirection: 'column', gap: 12 },
  card:       { background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', overflow: 'hidden' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 20px', cursor: 'pointer' },
  sourceType: { fontWeight: 700, fontSize: 14, marginRight: 10 },
  runId:      { fontSize: 12, color: '#aaa', fontFamily: 'monospace' },
  meta:       { display: 'flex', alignItems: 'center', gap: 16 },
  metaItem:   { fontSize: 13, color: '#888' },
  errCount:   { fontSize: 12, color: '#ef4444', fontWeight: 600 },
  chevron:    { fontSize: 11, color: '#aaa' },
  errorLog:   { borderTop: '1px solid #fee', background: '#fffaf9', padding: '12px 20px' },
  errTitle:   { fontWeight: 600, fontSize: 13, color: '#ef4444', marginBottom: 8 },
  errLine:    { fontSize: 12, color: '#666', marginBottom: 4 },
}