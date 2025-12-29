// frontend/src/App.js
import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import DatasetTable from "./components/DatasetTable";
import "./index.css";

/* Inline icons */
function IconCopy() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M9 9H5a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2v-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
      <rect x="9" y="3" width="11" height="11" rx="2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function IconDownload() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M7 10l5 5 5-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M12 15V3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}
function IconSun() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  );
}
function IconMoon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

export default function App() {
  // theme: 'dark' | 'light'
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem("ui_theme") || "dark"; } catch { return "dark"; }
  });

  useEffect(() => {
    // apply theme by toggling class on <html>
    const root = document.documentElement;
    if (theme === "light") {
      root.classList.add("theme-light");
      root.classList.remove("theme-dark");
    } else {
      root.classList.add("theme-dark");
      root.classList.remove("theme-light");
    }
    try { localStorage.setItem("ui_theme", theme); } catch {}
  }, [theme]);

  // rest of UI state
  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [sentences, setSentences] = useState(3);
  const [lengthPreset, setLengthPreset] = useState("medium"); // short / medium / long
  const [dataset, setDataset] = useState([]);
  const [dsLoading, setDsLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileRef = useRef();

  const presetToN = { short: 1, medium: 3, long: 5 };
  const n = presetToN[lengthPreset] ?? sentences;

  async function doSummarize(e) {
    e?.preventDefault();
    if (!text.trim()) { alert("Please enter text to summarize."); return; }
    setLoading(true); setSummary("");
    try {
      const res = await axios.post(
  "https://text-summarizer-with-glove-6.onrender.com/api/summarize",
  { text, sentences: n },
  { timeout: 30000 }
);

      setSummary(res.data.summary || "— No summary returned —");
    } catch (err) {
      console.error("Summarize error:", err);
      alert(err?.response?.data?.error || err.message || "Request failed");
    } finally { setLoading(false); }
  }

  async function handleDatasetSummarize(count = 5) {
    setDsLoading(true);
    try {
      const res = await axios.get(
  `https://text-summarizer-with-glove-6.onrender.com/api/summarize-dataset?n=${count}`,
  { timeout: 60000 }
);

      setDataset(res.data.results || []);
      alert(`Dataset summaries generated: ${res.data.count || (res.data.results || []).length}`);
    } catch (err) {
      console.error("Dataset fetch failed:", err);
      alert(err?.response?.data?.error || err.message || "Failed to fetch dataset");
    } finally { setDsLoading(false); }
  }

  async function handleFileUpload(evt) {
    const f = evt?.target?.files?.[0];
    if (!f) return;
    if (!f.name.match(/\.(xlsx|xls|csv)$/i) && !["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","text/csv","application/vnd.ms-excel"].includes(f.type)) {
      alert("Please upload a .xlsx, .xls or .csv file."); return;
    }
    setUploading(true); setUploadProgress(0);
    const fd = new FormData(); fd.append("file", f);
    try {
      const res = await axios.post(
  "https://text-summarizer-with-glove-6.onrender.com/api/upload-dataset",
  fd,
  {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (p) => {
      if (p.total) setUploadProgress(Math.round((p.loaded / p.total) * 100));
    },
    timeout: 120000
  }
);

      setDataset(res.data.results || []);
      alert(`Uploaded and summarized ${res.data.count || (res.data.results || []).length} rows`);
      fileRef.current.value = null;
    } catch (err) {
      console.error("Upload error", err);
      alert(err?.response?.data?.error || err.message || "Upload failed");
    } finally { setUploading(false); setUploadProgress(0); }
  }

  function copySummary() {
    if (!summary) return alert("No summary to copy");
    navigator.clipboard.writeText(summary).then(()=> alert("Summary copied to clipboard"));
  }

  function downloadSummary() {
    const blob = new Blob([summary || ""], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "summary.txt"; a.click(); URL.revokeObjectURL(url);
  }

  function clearAll() { setText(""); setSummary(""); }

  return (
    <div className="ui-root">
      <header className="ui-header">
        <div className="logo">
          <div className="logo-mark">S</div>
          <div className="logo-text">Summarize <span className="accent">AI</span></div>
        </div>

        <nav className="nav">
          <button className="nav-btn" aria-label="Docs">Docs</button>
          <button className="nav-btn" aria-label="Examples">Examples</button>

          {/* THEME TOGGLE */}
          <button
            className="theme-toggle"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
            aria-pressed={theme === "dark" ? "false" : "true"}
            style={{marginLeft:12}}
          >
            {theme === "dark" ? <IconSun/> : <IconMoon/>}
          </button>

          <button className="cta">Try Pro</button>
        </nav>
      </header>

      <main className="ui-main">
        <section className="hero-card">
          <h1>Turn long text into crisp, readable summaries — instantly.</h1>
          <p className="hero-sub">Paste text or upload an Excel/CSV dataset. Toggle light/dark above — your preference will be remembered.</p>
        </section>

        <section className="grid-area">
          <div className="panel left-panel">
            <div className="panel-head">
              <h3>Original Text</h3>
              <div className="panel-actions">
                <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" style={{display:'none'}} onChange={handleFileUpload}/>
                <button className="btn-outline" onClick={()=>fileRef.current?.click()}>{uploading ? `Uploading ${uploadProgress}%` : "Upload Dataset"}</button>
                <button className="btn-ghost" onClick={clearAll}>Clear</button>
                <button className="btn-ghost" onClick={()=>navigator.clipboard.readText().then(t=>setText(t)).catch(()=>{})}>Paste</button>
              </div>
            </div>

            <textarea className="editor" placeholder="Paste article, document, or any long text here..." value={text} onChange={e=>setText(e.target.value)} />

            <div className="controls">
              <div className="presets">
                <button className={lengthPreset==='short'?'preset active':'preset'} onClick={()=>setLengthPreset('short')}>Short</button>
                <button className={lengthPreset==='medium'?'preset active':'preset'} onClick={()=>setLengthPreset('medium')}>Medium</button>
                <button className={lengthPreset==='long'?'preset active':'preset'} onClick={()=>setLengthPreset('long')}>Long</button>
                <div className="or">or</div>
                <input type="number" min="1" value={sentences} onChange={e=>setSentences(Number(e.target.value)||1)} className="count-input"/>
              </div>
              <div>
                <button className="btn-primary" onClick={doSummarize} disabled={loading}>{loading ? 'Summarizing…' : 'Summarize'}</button>
              </div>
            </div>
          </div>

          <div className="panel right-panel">
            <div className="panel-head">
              <h3>Summary</h3>
              <div className="panel-actions">
                <button className="icon-btn" onClick={copySummary} title="Copy"><IconCopy/></button>
                <button className="icon-btn" onClick={downloadSummary} title="Download"><IconDownload/></button>
              </div>
            </div>

            <div className="summary-area">
              { summary ? <div className="summary-text">{summary}</div> : <div className="summary-empty">No summary yet — press <b>Summarize</b>.</div> }
            </div>

            <div className="controls lower-controls">
              <a
  className="link"
  href="https://text-summarizer-with-glove-6.onrender.com/api/summarize-dataset?n=5"
  target="_blank"rel="noreferrer">Download last CSV</a>
              <div>
                <button className="btn-ghost" onClick={()=>handleDatasetSummarize(5)} disabled={dsLoading}>{dsLoading ? 'Working…' : 'Summarize Dataset'}</button>
              </div>
            </div>
          </div>
        </section>

        <section className="dataset-section">
          <h4>Dataset Summaries</h4>
          <DatasetTable data={dataset} loading={dsLoading} />
        </section>
      </main>

      <footer className="ui-footer">
        <div>Made with ❤️ — place <code>glove.6B.100d.txt</code> in backend/ for semantic summaries</div>
      </footer>
    </div>
  );
}
