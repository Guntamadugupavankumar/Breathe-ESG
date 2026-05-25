import React, { useEffect, useState } from 'react'
import RowTable from '../components/RowTable'
import api from '../api/client'

const SCOPES = ['', 'SCOPE_1', 'SCOPE_2', 'SCOPE_3']
const STATUSES = ['', 'PENDING', 'FLAGGED', 'APPROVED', 'REJECTED']
const SOURCES = ['', 'SAP_FLAT_FILE', 'UTILITY_CSV', 'TRAVEL_JSON']

export default function ReviewPage() {
  const [rows, setRows] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  const [scope, setScope]         = useState('')
  const [review, setReview]       = useState('')
  const [source, setSource]       = useState('')

  function load(p = 1) {
    setLoading(true)
    const params = { page: p }
    if (scope)  params.scope = scope
    if (review) params.review_status = review
    if (source) params.source_type = source

    api.get('/rows/', { params }).then(r => {
      const data = r.data
      setRows(data.results || data)
      setTotal(data.count || (data.results || data).length)
      setPage(p)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load(1) }, [scope, review, source])

  const pageSize = 50
  const totalPages = Math.ceil(total / pageSize)

  return (
    <div>
      <h2 style={styles.heading}>Review Emissions Rows</h2>
      <p style={styles.sub}>{total} rows total</p>

      <div style={styles.filters}>
        <select style={styles.select} value={scope} onChange={e => setScope(e.target.value)}>
          <option value="">All Scopes</option>
          {SCOPES.filter(Boolean).map(s => <option key={s} value={s}>{s.replace('_',' ')}</option>)}
        </select>

        <select style={styles.select} value={review} onChange={e => setReview(e.target.value)}>
          <option value="">All Statuses</option>
          {STATUSES.filter(Boolean).map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <select style={styles.select} value={source} onChange={e => setSource(e.target.value)}>
          <option value="">All Sources</option>
          {SOURCES.filter(Boolean).map(s => <option key={s} value={s}>{s.replace(/_/g,' ')}</option>)}
        </select>

        <button style={styles.refresh} onClick={() => load(page)}>↻ Refresh</button>
      </div>

      <div style={styles.tableWrap}>
        {loading
          ? <p style={{ color: '#aaa', textAlign: 'center', padding: 40 }}>Loading…</p>
          : <RowTable rows={rows} onRefresh={() => load(page)} />
        }
      </div>

      {totalPages > 1 && (
        <div style={styles.pagination}>
          <button style={styles.pageBtn} disabled={page === 1} onClick={() => load(page - 1)}>← Prev</button>
          <span style={{ fontSize: 13, color: '#666' }}>Page {page} of {totalPages}</span>
          <button style={styles.pageBtn} disabled={page === totalPages} onClick={() => load(page + 1)}>Next →</button>
        </div>
      )}
    </div>
  )
}

const styles = {
  heading:   { fontSize: 22, fontWeight: 700, marginBottom: 4 },
  sub:       { color: '#aaa', fontSize: 13, marginBottom: 20 },
  filters:   { display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' },
  select:    { padding: '8px 12px', border: '1px solid #ddd', borderRadius: 7, fontSize: 13, background: '#fff' },
  refresh:   { padding: '8px 16px', border: '1px solid #ddd', borderRadius: 7, fontSize: 13, cursor: 'pointer', background: '#fff' },
  tableWrap: { background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', overflow: 'hidden' },
  pagination: { display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 20, marginTop: 20 },
  pageBtn:   { padding: '7px 16px', border: '1px solid #ddd', borderRadius: 7, cursor: 'pointer', background: '#fff', fontSize: 13 },
}