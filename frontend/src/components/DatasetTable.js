// frontend/src/components/DatasetTable.js
import React, { useMemo, useState } from "react";

/**
 * Simple responsive dataset table component.
 * Props:
 *   - data: array of { TEST DATASET, Introduction, Summary }
 *   - loading: boolean
 */
export default function DatasetTable({ data = [], loading = false }) {
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 6;

  const filtered = useMemo(() => {
    if (!data || !data.length) return [];
    if (!q) return data;
    const ql = q.toLowerCase();
    return data.filter(r => (r.Introduction || "").toLowerCase().includes(ql) || (r.Summary || "").toLowerCase().includes(ql));
  }, [data, q]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageData = filtered.slice((page-1)*pageSize, page*pageSize);

  return (
    <div className="dataset-table">
      <div className="dataset-controls">
        <input className="search" placeholder="Search dataset..." value={q} onChange={e=>{ setQ(e.target.value); setPage(1); }} />
        <div className="count">{filtered.length} results</div>
      </div>

      <div className="rows">
        {loading && <div className="muted">Loading summaries…</div>}
        {!loading && pageData.length === 0 && <div className="muted">No dataset loaded yet.</div>}

        {pageData.map(row => (
          <div key={row["TEST DATASET"]} className="row">
            <div className="badge">#{row["TEST DATASET"]}</div>
            <div className="row-body">
              <div className="intro">{row.Introduction}</div>
              <div className="row-summary">{row.Summary}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="pagination">
        <button onClick={()=>setPage(p => Math.max(1, p-1))} disabled={page <= 1}>Prev</button>
        <span>Page {page} / {pageCount}</span>
        <button onClick={()=>setPage(p => Math.min(pageCount, p+1))} disabled={page >= pageCount}>Next</button>
      </div>
    </div>
  );
}
