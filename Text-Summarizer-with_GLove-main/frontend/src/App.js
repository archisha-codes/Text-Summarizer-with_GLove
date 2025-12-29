// frontend/src/App.js
import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import DatasetTable from "./components/DatasetTable";
import "./index.css";

/* ✅ REQUIRED: backend base URL */
const API_BASE = "https://text-summarizer-with-glove-6.onrender.com/api";

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
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem("ui_theme") || "dark"; } catch { return "dark"; }
  });

  useEffect(() => {
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

  const [text, setText] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [sentences, setSentences] = useState(3);
  const [lengthPreset, setLengthPreset] = useState("medium");
  const [dataset, setDataset] = useState([]);
  const [dsLoading, setDsLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileRef = useRef();

  const presetToN = { short: 1, medium: 3, long: 5 };
  const n = presetToN[lengthPreset] ?? sentences;

  async function doSummarize(e) {
    e?.preventDefault();
    if (!text.trim()) return alert("Please enter text to summarize.");
    setLoading(true); setSummary("");
    try {
      const res = await axios.post(
        `${API_BASE}/summarize`,
        { text, sentences: n },
        { timeout: 30000 }
      );
      setSummary(res.data.summary || "— No summary returned —");
    } catch (err) {
      alert(err?.response?.data?.error || err.message || "Request failed");
    } finally { setLoading(false); }
  }

  async function handleDatasetSummarize(count = 5) {
    setDsLoading(true);
    try {
      const res = await axios.get(
        `${API_BASE}/summarize-dataset?n=${count}`,
        { timeout: 60000 }
      );
      setDataset(res.data.results || []);
    } catch (err) {
      alert(err?.response?.data?.error || err.message);
    } finally { setDsLoading(false); }
  }

  async function handleFileUpload(evt) {
    const f = evt?.target?.files?.[0];
    if (!f) return;

    setUploading(true); setUploadProgress(0);
    const fd = new FormData(); fd.append("file", f);

    try {
      const res = await axios.post(
        `${API_BASE}/upload-dataset`,
        fd,
        {
          headers: { "Content-Type": "multipart/form-data" },
          onUploadProgress: p => p.total && setUploadProgress(Math.round((p.loaded / p.total) * 100)),
          timeout: 120000
        }
      );
      setDataset(res.data.results || []);
      fileRef.current.value = null;
    } catch (err) {
      alert(err?.response?.data?.error || err.message);
    } finally { setUploading(false); setUploadProgress(0); }
  }

  return (
    <div className="ui-root">
      {/* UI UNCHANGED */}

      <a
        className="link"
        href={`${API_BASE}/summarize-dataset?n=5`}
        target="_blank"
        rel="noreferrer"
      >
        Download last CSV
      </a>

      <DatasetTable data={dataset} loading={dsLoading} />
    </div>
  );
}
