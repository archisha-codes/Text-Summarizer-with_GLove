"""
backend/summarizer.py

GloVe-based extractive summarizer with TF-IDF fallback.
Exposes:
- summary_text(text, n=5) -> str
- summarize_dataset(excel_path='TASK.xlsx', text_col='Introduction', n=5, save_csv=True) -> list of dicts
"""

from typing import List, Dict
import os
import re
import logging
import numpy as np
import pandas as pd

# sklearn, networkx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

_LOG = logging.getLogger(__name__)

# --- GloVe loader (optional) ---
_GLOVE_PATHS = [
    os.path.join(os.path.dirname(__file__), "glove.6B.100d.txt"),
    os.path.join(os.path.dirname(__file__), "..", "glove.6B.100d.txt"),
]

_glove = None
_glove_dim = 100

def _load_glove():
    global _glove, _glove_dim
    if _glove is not None:
        return _glove
    chosen = None
    for p in _GLOVE_PATHS:
        if os.path.exists(p):
            chosen = p
            break
    if not chosen:
        _LOG.info("GloVe not found in backend folder. Falling back to TF-IDF sentence vectors.")
        _glove = None
        return None
    _LOG.info(f"Loading GloVe from {chosen} ...")
    emb = {}
    with open(chosen, "r", encoding="utf-8") as fh:
        for line in fh:
            parts = line.strip().split()
            if len(parts) <= 2:
                continue
            w = parts[0]
            vec = np.asarray(parts[1:], dtype="float32")
            emb[w] = vec
    _glove_dim = len(next(iter(emb.values())))
    _glove = emb
    _LOG.info(f"GloVe loaded: vocab={len(emb)} dim={_glove_dim}")
    return _glove

# --- Tokenization & stopwords: lazy, safe usage of NLTK if available ---
def _get_tokenizer_and_stopset():
    """Return (sent_tokenize_fn, stopset). Use nltk if available; otherwise fallback."""
    fallback_stop = set("""
        a an the and or if in on at for to of is are was were be been it this that
        these those as with by from but not they you i we he she his her their them
        my your so what which who whom
    """.split())

    try:
        import nltk
        from nltk.tokenize import sent_tokenize
        # ensure punkt (download only if missing)
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            _LOG.info("Downloading NLTK punkt tokenizer (one-time).")
            nltk.download('punkt')
        # stopwords
        try:
            from nltk.corpus import stopwords
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                _LOG.info("Downloading NLTK stopwords (one-time).")
                nltk.download('stopwords')
            stopset = set(stopwords.words('english'))
        except Exception:
            stopset = fallback_stop
        return sent_tokenize, stopset
    except Exception:
        # fallback simple sent splitter
        def _sent_tokenize_fallback(text: str) -> List[str]:
            pieces = re.split(r'(?<=[.!?])\s+', text.strip())
            return [p.strip() for p in pieces if p.strip()]
        return _sent_tokenize_fallback, fallback_stop

_sent_tokenize, _stopwords = _get_tokenizer_and_stopset()


# --- helper functions (close to your original code) ---
def remove_stopwords_from_list(word_list: List[str]) -> str:
    """Remove stopwords from a list of tokens and return the cleaned sentence string."""
    filtered = [w for w in word_list if w.lower() not in _stopwords]
    return " ".join(filtered)


def sentence_vector_func(sentences_cleaned: List[str], glove_embeddings: Dict = None, glove_dim: int = 100):
    """
    Create sentence vectors.
    If glove_embeddings provided -> average glove vectors (dim glove_dim).
    Else: return TF-IDF vectors (dense) computed outside this function.
    """
    if glove_embeddings:
        vecs = []
        z = np.zeros((glove_dim,), dtype="float32")
        for s in sentences_cleaned:
            if s and s.strip():
                words = [w for w in re.findall(r"\w+", s.lower()) if w not in _stopwords]
                if words:
                    vs = [glove_embeddings.get(w, np.zeros((glove_dim,))) for w in words]
                    avg = np.sum(vs, axis=0) / (len(vs) + 1e-9)
                else:
                    avg = z.copy()
            else:
                avg = z.copy()
            vecs.append(avg)
        return np.vstack(vecs)
    else:
        # If glove not present, caller will use TF-IDF fallback separately
        return None


# --- core summarization adapted from your code ---
def summary_text(test_text: str, n: int = 5) -> str:
    """
    Extractive summarization using TextRank-like method:
    - tokenize sentences
    - clean sentences (lowercase, remove punctuation)
    - compute sentence vectors (GloVe average if available; otherwise TF-IDF)
    - compute cosine similarities, build graph, run PageRank
    - select top-n sentences (returned in original order)
    """
    if not test_text or not str(test_text).strip():
        return ""

    # 1. tokenize
    sentences = _sent_tokenize(str(test_text))
    # flatten list is not required since sent_tokenize returns flat list

    # 2. cleaning (remove punctuation/numbers -> like your original)
    # Use simpler regex replace for each sentence
    cleaned_sentences = [re.sub(r"[^a-zA-Z0-9\s]", " ", s) for s in sentences]
    cleaned_sentences = [s.lower().strip() for s in cleaned_sentences]

    # 3. remove stopwords (following your remove_stopwords which took a list)
    cleaned_no_stop = [remove_stopwords_from_list(s.split()) for s in cleaned_sentences]

    # 4. get vectors
    glove = _load_glove()
    if glove:
        sent_vecs = sentence_vector_func(cleaned_no_stop, glove, _glove_dim)  # shape (m, dim)
    else:
        # TF-IDF fallback - vectorize cleaned_no_stop (strings)
        tfidf = TfidfVectorizer(stop_words='english', max_df=0.85)
        sent_vecs = tfidf.fit_transform(cleaned_no_stop).toarray()  # dense matrix

    # 5. similarity matrix
    m = len(sentences)
    if m == 0:
        return ""
    sim_mat = np.zeros((m, m), dtype="float32")
    # Use sklearn cosine_similarity for speed
    try:
        sim = cosine_similarity(sent_vecs)
        np.fill_diagonal(sim, 0.0)
        sim_mat = sim
    except Exception:
        # fallback naive
        for i in range(m):
            for j in range(m):
                if i == j:
                    continue
                a = sent_vecs[i].reshape(1, -1)
                b = sent_vecs[j].reshape(1, -1)
                denom = (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
                sim_mat[i, j] = float(np.dot(a, b.T) / denom)

    # 6. PageRank
    try:
        nx_graph = nx.from_numpy_array(sim_mat)
        scores = nx.pagerank(nx_graph)
    except Exception:
        # fallback score = sum of similarities (not ideal but works)
        scores = {i: float(sim_mat[i].sum()) for i in range(m)}

    # 7. rank sentences (your original used sorted ((score, sentence)) but careful about order)
    ranked = sorted(((scores[i], s, i) for i, s in enumerate(sentences)), key=lambda x: x[0], reverse=True)
    top_k = ranked[:n]
    # get indices and sort them to preserve original order
    top_indices = sorted([t[2] for t in top_k])

    # 8. build summary string
    summary_parts = [sentences[i].strip() for i in top_indices]
    return " ".join(summary_parts)


# --- dataset summarization helper (Option A) ---
def summarize_dataset(excel_path: str = "TASK.xlsx", text_col: str = None, n: int = 5, save_csv: bool = True) -> List[Dict]:
    """
    Read excel at excel_path, identify the text column (default tries 'Introduction' or 'Unnamed: 1'),
    produce summaries for each row, and optionally save a CSV 'SummaryFile.csv' in same folder.

    Returns: list of dicts: [{'index': idx, 'text': original_text, 'summary': summary}, ...]
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"{excel_path} not found. Place your TASK.xlsx in the backend folder.")

    df = pd.read_excel(excel_path)  # requires openpyxl for xlsx typically
    # if user didn't provide text_col, try a few common names
    possible = [text_col] if text_col else []
    possible += ['Introduction', 'Unnamed: 1', 'text', 'Text', 'TEST DATASET']
    col_found = None
    for c in possible:
        if c and c in df.columns:
            col_found = c
            break
    if col_found is None:
        # fallback: pick the second column if it exists
        if len(df.columns) >= 2:
            col_found = df.columns[1]
        else:
            col_found = df.columns[0]

    # Build dictionary like your original code (starting at index 1)
    text_dictionary = {}
    # iterate rows; skip NaNs
    for i, val in enumerate(df[col_found].tolist(), start=1):
        if pd.isna(val):
            continue
        text_dictionary[i] = str(val)

    # Summarize every entry
    results = []
    for idx, para in text_dictionary.items():
        try:
            summary = summary_text(para, n)
        except Exception as e:
            _LOG.exception("Failed to summarize row %s: %s", idx, e)
            summary = ""
        results.append({"TEST DATASET": idx, "Introduction": para, "Summary": summary})

    # save CSV
    if save_csv:
        out_df = pd.DataFrame(results)
        out_path = os.path.join(os.path.dirname(excel_path) or ".", "SummaryFile.csv")
        out_df.to_csv(out_path, index=False)
        _LOG.info("Saved summary CSV to %s", out_path)

    return results
