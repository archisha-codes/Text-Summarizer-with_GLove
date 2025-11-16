// frontend/src/App.js
import React, { useState, useRef } from "react";
import axios from "axios";
import DatasetTable from "./components/DatasetTable";
import "./index.css";

/* --- small inline SVG icons --- */
function IconCopy() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M9 9H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
      <rect x="9" y="3" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function IconDownload() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M7 10l5 5 5-5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 15V3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export default function App() {
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [sentences, setSentences] = useState(3);
  const [lengthPreset, setLengthPreset] = useState("medium"); // short / medium / long
  const [styleMode, setStyleMode] = useState("Key Sentences");
  const [dataset, setDataset] = useState([]);
  const [dsLoading, setDsLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileRef = useRef();

  const presetToN = { short: 1, medium: 3, long: 5 };
  const n = presetToN[lengthPreset] ?? sentences;

  async function doSummarize(e) {
    e?.preventDefault();
    if (!text.trim()) {
      alert("Please enter text to summarize.");
      return;
    }
    setLoading(true);
    setSummary("");
    try {
      const res = await axios.post("/api/summarize", { text, sentences: n }, { timeout: 30000 });
      setSummary(res.data.summary || "— No summary returned —");
    } catch (err) {
      console.error("Summarize error:", err);
      alert(err?.response?.data?.error || err.message || "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleDatasetSummarize(count = 5) {
    setDsLoading(true);
    try {
      const res = await axios.get(`/api/summarize-dataset?n=${count}`, { timeout: 60000 });
      setDataset(res.data.results || []);
      alert(`Dataset summaries generated: ${res.data.count || (res.data.results || []).length}`);
    } catch (err) {
      console.error("Dataset fetch failed:", err);
      alert(err?.response?.data?.error || err.message || "Failed to fetch dataset");
    } finally {
      setDsLoading(false);
    }
  }

  async function handleFileUpload(evt) {
    const f = evt?.target?.files?.[0];
    if (!f) return;
    // accept xlsx/xls/csv by extension/types
    if (!f.name.match(/\.(xlsx|xls|csv)$/i) && !["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","text/csv","application/vnd.ms-excel"].includes(f.type)) {
      alert("Please upload a .xlsx, .xls or .csv file.");
      return;
    }
    setUploading(true); setUploadProgress(0);
    const fd = new FormData();
    fd.append("file", f);
    try {
      const res = await axios.post("/api/upload-dataset", fd, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (p) => { if (p.total) setUploadProgress(Math.round((p.loaded / p.total) * 100)); },
        timeout: 120000
      });
      setDataset(res.data.results || []);
      alert(`Uploaded and summarized ${res.data.count || (res.data.results || []).length} rows`);
      fileRef.current.value = null;
    } catch (err) {
      console.error("Upload error", err);
      alert(err?.response?.data?.error || err.message || "Upload failed");
    } finally {
      setUploading(false); setUploadProgress(0);
    }
  }

  function copySummary() {
    if (!summary) return alert("No summary to copy");
    navigator.clipboard.writeText(summary).then(() => alert("Summary copied to clipboard"));
  }

  function downloadSummary() {
    const blob = new Blob([summary || ""], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "summary.txt"; document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  }

  function clearAll() { setText(""); setSummary(""); }

  return (
    <div className="app-root">
      <header className="app-header">
        <div className="brand">Summarize.<span className="brand-accent">AI</span></div>
        <nav className="nav">
          <button className="btn-ghost">Features</button>
          <button className="btn-ghost">Pricing</button>
          <button className="btn-primary">Sign Up</button>
        </nav>
      </header>

      <main className="container">
        <section className="hero">
          <h1>Instantly Condense Any Text</h1>
          <p className="hero-sub">Paste your text, choose length, and get a concise summary.</p>
        </section>

        <section className="panels">
          <div className="card editor">
            <div className="card-head">
              <h3>Original Text</h3>
              <div className="card-controls">
                <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" onChange={handleFileUpload} style={{display:'none'}} />
                <button onClick={() => fileRef.current?.click()} className="btn-small">Upload dataset</button>
                <button onClick={clearAll} className="btn-small">Clear</button>
                <button onClick={() => navigator.clipboard.readText().then(t => setText(t)).catch(()=>{})} className="btn-small">Paste</button>
              </div>
            </div>

            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste or type your text here..."
              className="editor-area"
            />

            <div className="controls-row">
              <div className="left-controls">
                <div className="preset-buttons" role="toolbar" aria-label="Length presets">
                  <button className={lengthPreset === 'short' ? 'active' : ''} onClick={() => setLengthPreset('short')}>Short</button>
                  <button className={lengthPreset === 'medium' ? 'active' : ''} onClick={() => setLengthPreset('medium')}>Medium</button>
                  <button className={lengthPreset === 'long' ? 'active' : ''} onClick={() => setLengthPreset('long')}>Long</button>
                </div>
                <label className="sent-label">or sentences
                  <input type="number" min="1" value={sentences} onChange={e => setSentences(Number(e.target.value) || 1)} />
                </label>
              </div>

              <div className="right-controls">
                <button onClick={doSummarize} disabled={loading} className="btn-primary">{loading ? 'Working…' : 'Summarize'}</button>
              </div>
            </div>
          </div>

          <div className="card output">
            <div className="card-head">
              <h3>Summarized Text</h3>
              <div className="card-controls">
                <button onClick={copySummary} className="icon-btn" title="Copy"><IconCopy /></button>
                <button onClick={downloadSummary} className="icon-btn" title="Download"><IconDownload /></button>
              </div>
            </div>

            <div className="output-area">
              {summary ? <div className="summary-content">{summary}</div> : <div className="summary-placeholder">Your summary will appear here.</div>}
            </div>

            <div className="controls-row">
              <div className="left-controls">
                <a className="link" href="/api/summarize-dataset?n=5" target="_blank" rel="noreferrer">Download last summary CSV</a>
              </div>
              <div className="right-controls">
                <button onClick={() => handleDatasetSummarize(5)} disabled={dsLoading} className="btn-small">{dsLoading ? 'Working…' : 'Summarize Dataset'}</button>
              </div>
            </div>
          </div>
        </section>

        <section className="dataset-section">
          <h4>Dataset Summaries</h4>
          <div className="upload-status">
            {uploading ? <div>Uploading... {uploadProgress}%</div> : <div className="muted">Upload an .xlsx or .csv to generate summaries for the dataset rows.</div>}
          </div>
          <DatasetTable data={dataset} loading={dsLoading} />
        </section>
      </main>
    </div>
  );
}
