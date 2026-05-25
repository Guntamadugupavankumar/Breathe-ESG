import React, { useState, useEffect } from 'react'
import api from '../api/client'

export default function UploadModal({ onClose, onDone }) {
  const [tenants, setTenants] = useState([])
  const [tenantId, setTenantId] = useState('')
  const [sourceType, setSourceType] = useState('SAP_FLAT_FILE')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/tenants/').then(r => {
      setTenants(r.data.results || r.data)
      if ((r.data.results || r.data).length > 0)
        setTenantId((r.data.results || r.data)[0].id)
    })
  }, [])

  async function submit() {
    if (!file) return setError('Please select a file.')
    setLoading(true)
    setError('')
    const fd = new FormData()
    fd.append('file', file)
    fd.append('source_type', sourceType)
    fd.append('tenant_id', tenantId)
    try {
      await api.post('/upload/', fd)
      onDone()
      onClose()
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <h2 style={styles.title}>Upload Data File</h2>

        {error && <p style={styles.err}>{error}</p>}

        <label style={styles.label}>Tenant</label>
        <select style={styles.input} value={tenantId} onChange={e => setTenantId(e.target.value)}>
          {tenants.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>

        <label style={styles.label}>Source Type</label>
        <select style={styles.input} value={sourceType} onChange={e => setSourceType(e.target.value)}>
          <option value="SAP_FLAT_FILE">SAP Flat File</option>
          <option value="UTILITY_CSV">Utility CSV</option>
          <option value="TRAVEL_JSON">Travel JSON</option>
        </select>

        <label style={styles.label}>File</label>
        <input
          type="file"
          style={styles.input}
          onChange={e => setFile(e.target.files[0])}
          accept=".csv,.txt,.json,.tsv"
        />

        <div style={styles.row}>
          <button style={styles.cancel} onClick={onClose}>Cancel</button>
          <button style={styles.btn} onClick={submit} disabled={loading}>
            {loading ? 'Uploading…' : 'Upload'}
          </button>
        </div>
      </div>
    </div>
  )
}

const styles = {
  overlay: {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999,
  },
  modal: {
    background: '#fff', borderRadius: 12, padding: 32,
    width: 420, boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
  },
  title:  { fontSize: 20, fontWeight: 700, marginBottom: 20 },
  label:  { fontSize: 12, color: '#666', display: 'block', marginBottom: 4, marginTop: 14 },
  input:  { width: '100%', padding: '9px 12px', border: '1px solid #ddd', borderRadius: 7, fontSize: 14 },
  err:    { background: '#fee', color: '#c00', borderRadius: 6, padding: '8px 12px', fontSize: 13, marginBottom: 12 },
  row:    { display: 'flex', gap: 10, marginTop: 24 },
  btn:    { flex: 1, padding: 10, background: '#2ecc71', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer' },
  cancel: { flex: 1, padding: 10, background: '#f0f0f0', color: '#333', border: 'none', borderRadius: 8, fontWeight: 600, cursor: 'pointer' },
}