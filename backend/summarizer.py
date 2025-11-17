"""
backend/summarizer.py

Robust extractive summarizer:
- summary_text(text, n=5) -> str   # summarize arbitrary text
- summarize_dataset(excel_path='TASK.xlsx', text_col=None, n=5, save_csv=True) -> list[dict]
  # summarize rows in Excel/CSV; writes SummaryFile.csv next to dataset when save_csv=True

Features:
- optional GloVe (place glove.6B.100d.txt in backend/)
- TF-IDF fallback if GloVe missing
- Safe NLTK usage (tries to use nltk.sent_tokenize & stopwords; falls back to simple split)
- Good error handling
"""

from typing import List, Dict, Optional
import os
import re
import logging
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

_LOG = logging.getLogger(__name__)

# Paths to look for glove file (you can place glove.6B.100d.txt inside backend/).
_GLOVE_PATHS = [
    os.path.join(os.path.dirname(__file__), "glove.6B.100d.txt"),
    os.path.join(os.path.dirname(__file__), "..", "glove.6B.100d.txt"),
]

_glove = None
_glove_dim = 100


def _load_glove() -> Optional[dict]:
    """Load GloVe vectors if present; return dict(word -> np.array) or None."""
    global _glove, _glove_dim
    if _glove is not None:
        return _glove
    chosen = None
    for p in _GLOVE_PATHS:
        if os.path.exists(p) and os.path.getsize(p) > 0:
            chosen = p
            break
    if not chosen:
        _LOG.info("GloVe file not found in backend. Using TF-IDF fallback.")
        _glove = None
        return None
    _LOG.info("Loading GloVe from %s ... (this may take a minute)", chosen)
    emb = {}
    with open(chosen, "r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            parts = line.strip().split()
            if len(parts) <= 2:
                continue
            w = parts[0]
            vec = np.asarray(parts[1:], dtype="float32")
            emb[w] = vec
    if not emb:
        _LOG.warning("GloVe file was found but no embeddings loaded.")
        _glove = None
        return None
    _glove_dim = len(next(iter(emb.values())))
    _glove = emb
    _LOG.info("GloVe loaded: vocab=%d dim=%d", len(emb), _glove_dim)
    return _glove


# --- Tokenization & stopwords (use nltk if available, but safe fallback) ---
def _get_sentence_tokenizer_and_stopset():
    fallback_stop = set(
        """a an the and or if in on at for to of is are was were be been it this that
        these those as with by from but not they you i we he she his her their them
        my your so what which who whom""".split()
    )

    try:
        import nltk
        from nltk.tokenize import sent_tokenize

        # ensure punkt & stopwords exist - download only if missing
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            _LOG.info("Downloading NLTK punkt tokenizer (one-time) ...")
            nltk.download("punkt")
        # stopwords
        try:
            nltk.data.find("corpora/stopwords")
            from nltk.corpus import stopwords

            stopset = set(stopwords.words("english"))
        except LookupError:
            _LOG.info("Downloading NLTK stopwords (one-time) ...")
            nltk.download("stopwords")
            from nltk.corpus import stopwords

            stopset = set(stopwords.words("english"))
        except Exception:
            stopset = fallback_stop

        return sent_tokenize, stopset
    except Exception:
        # fallback simple sentence splitter
        def _simple_sent_tokenize(text: str) -> List[str]:
            pieces = re.split(r"(?<=[.!?])\s+", text.strip())
            return [p.strip() for p in pieces if p.strip()]

        return _simple_sent_tokenize, fallback_stop


_sent_tokenize, _stopwords = _get_sentence_tokenizer_and_stopset()


# --- helper utilities ---
def _clean_sentence_for_vectors(s: str) -> str:
    # remove non-word characters but keep spaces and numbers
    s = re.sub(r"[^a-zA-Z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()


def _remove_stopwords_from_tokens(tokens: List[str]) -> str:
    return " ".join([t for t in tokens if t.lower() not in _stopwords])


def _sentence_vectors_with_glove(clean_sentences: List[str], glove_embeddings: dict, dim: int):
    """Return numpy array shape (n_sentences, dim) using averaged glove vectors per sentence."""
    z = np.zeros((dim,), dtype="float32")
    vecs = []
    for s in clean_sentences:
        if s and s.strip():
            words = [w for w in re.findall(r"\w+", s.lower()) if w not in _stopwords]
            if words:
                vs = [glove_embeddings.get(w, np.zeros((dim,), dtype="float32")) for w in words]
                avg = np.sum(vs, axis=0) / (len(vs) + 1e-9)
            else:
                avg = z.copy()
        else:
            avg = z.copy()
        vecs.append(avg)
    return np.vstack(vecs) if vecs else np.zeros((0, dim), dtype="float32")


def _sentence_vectors_with_tfidf(clean_sentences: List[str]):
    """Return dense TF-IDF vectors (numpy array)."""
    if not clean_sentences:
        return np.zeros((0, 1))
    tfidf = TfidfVectorizer(stop_words="english", max_df=0.85)
    mat = tfidf.fit_transform(clean_sentences)
    return mat.toarray()


# --- Core summarization functions ---


def summary_text(test_text: str, n: int = 5) -> str:
    """
    Summarize arbitrary text and return a string containing the top-n sentences (preserving order).
    Returns empty string for empty input.
    """
    if not test_text:
        return ""

    text = str(test_text).strip()
    if not text:
        return ""

    # 1) tokenize into sentences
    sentences = _sent_tokenize(text)
    if not sentences:
        return ""

    # 2) clean sentences for vector creation
    cleaned = [_clean_sentence_for_vectors(s) for s in sentences]
    no_stop = [_remove_stopwords_from_tokens(s.split()) for s in cleaned]

    # 3) try glove
    glove = _load_glove()
    if glove:
        sent_vecs = _sentence_vectors_with_glove(no_stop, glove, _glove_dim)
    else:
        sent_vecs = None

    # 4) if no glove or glove failed, use TF-IDF
    if sent_vecs is None or sent_vecs.shape[0] == 0:
        sent_vecs = _sentence_vectors_with_tfidf(no_stop)

    # 5) build similarity matrix
    m = len(sentences)
    if m == 0:
        return ""
    try:
        sim = cosine_similarity(sent_vecs)
        sim = np.nan_to_num(sim, nan=0.0)
        np.fill_diagonal(sim, 0.0)
        sim_mat = sim
    except Exception:
        sim_mat = np.zeros((m, m), dtype="float32")
        for i in range(m):
            for j in range(m):
                if i == j:
                    continue
                a = sent_vecs[i].reshape(1, -1)
                b = sent_vecs[j].reshape(1, -1)
                denom = (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
                sim_mat[i, j] = float(np.dot(a, b.T) / denom)

    # 6) PageRank / scoring
    try:
        nx_graph = nx.from_numpy_array(sim_mat)
        scores = nx.pagerank(nx_graph)
    except Exception:
        scores = {i: float(sim_mat[i].sum()) for i in range(m)}

    # 7) rank sentences and choose top-n
    ranked = sorted(((scores.get(i, 0.0), i, sentences[i]) for i in range(m)), key=lambda x: x[0], reverse=True)
    topk = ranked[: max(1, int(n))]
    top_indices = sorted([t[1] for t in topk])
    summary_parts = [sentences[i].strip() for i in top_indices]
    return " ".join(summary_parts)


def summarize_dataset(excel_path: str = "TASK.xlsx", text_col: Optional[str] = None, n: int = 5, save_csv: bool = True) -> List[Dict]:
    """
    Read dataset from excel_path (.xlsx/.xls/.csv). Try to find the text column (text_col param).
    Produce a list of dicts: [{'TEST DATASET': idx, 'Introduction': original_text, 'Summary': summary}, ...]
    Optionally writes SummaryFile.csv next to dataset file.
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"{excel_path} not found.")

    # try to read excel or csv (auto detect by extension)
    ext = os.path.splitext(excel_path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(excel_path)
    else:
        df = pd.read_csv(excel_path)

    # choose the text column
    col_found = None
    if text_col and text_col in df.columns:
        col_found = text_col
    else:
        # common names
        candidates = ["Introduction", "Unnamed: 1", "text", "Text", "TEST DATASET", "content", "Content"]
        for c in candidates:
            if c in df.columns:
                col_found = c
                break
        if col_found is None:
            # fallback to second column if present, else first
            if len(df.columns) >= 2:
                col_found = df.columns[1]
            else:
                col_found = df.columns[0]

    results = []
    for i, val in enumerate(df[col_found].tolist(), start=1):
        if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
            text = ""
        else:
            text = str(val)
        try:
            summ = summary_text(text, n)
        except Exception as e:
            _LOG.exception("Failed summarizing row %s: %s", i, e)
            summ = ""
        results.append({"TEST DATASET": i, "Introduction": text, "Summary": summ})

    if save_csv:
        out_df = pd.DataFrame(results)
        out_path = os.path.join(os.path.dirname(excel_path) or ".", "SummaryFile.csv")
        out_df.to_csv(out_path, index=False)
        _LOG.info("Wrote summary CSV to %s", out_path)

    return results
