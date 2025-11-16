// frontend/src/components/DatasetTable.js
import React, { useMemo, useState } from 'react';

export default function DatasetTable({ data = [], loading = false }) {
  const [q, setQ] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 8;

  const filtered = useMemo(() => {
    if (!data || !data.length) return [];
    if (!q) return data;
    const ql = q.toLowerCase();
    return data.filter(r => (r.Introduction || '').toLowerCase().includes(ql) || (r.Summary || '').toLowerCase().includes(ql));
  }, [data, q]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageData = filtered.slice((page-1)*pageSize, page*pageSize);

  return (
    <div className="dataset-table">
      <div className="dataset-controls">
        <input placeholder="Search dataset..." value={q} onChange={e=>{setQ(e.target.value); setPage(1)}} className="search-input" />
        <div className="result-count">{filtered.length} results</div>
      </div>

      <div className="rows">
        {loading && <div className="loading">Loading summaries…</div>}
        {!loading && !pageData.length && <div className="muted">No dataset loaded.</div>}
        {!loading && pageData.map(r => (
          <div key={r['TEST DATASET']} className="row">
            <div className="row-left">#{r['TEST DATASET']}</div>
            <div className="row-right">
              <div className="row-text">{r.Introduction?.slice(0,250)}{r.Introduction && r.Introduction.length>250 ? '...' : ''}</div>
              <div className="row-summary">{r.Summary}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="pagination">
        <button onClick={()=>setPage(p=>Math.max(1,p-1))} disabled={page<=1}>Prev</button>
        <div>Page {page} / {pageCount}</div>
        <button onClick={()=>setPage(p=>Math.min(pageCount,p+1))} disabled={page>=pageCount}>Next</button>
      </div>
    </div>
  );
}
