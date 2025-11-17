"""
backend/app.py

Flask API server for summarizer. Endpoints:

- GET  /api/ping
- POST /api/summarize           # JSON { "text": "...", "sentences": 3 }
- GET  /api/summarize-dataset   # query ?n=3 (summarizes backend/TASK.xlsx or latest upload)
- POST /api/upload-dataset      # multipart form; field 'file' (.xlsx/.xls/.csv/.txt)
- Serves frontend build from backend/frontend/build if present
"""

import os
import logging
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
from flask_cors import CORS

# import summarizer functions
from summarizer import summary_text, summarize_dataset

# Config
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
FRONTEND_BUILD = os.path.join(BASE_DIR, "frontend", "build")
TASK_XLSX = os.path.join(BASE_DIR, "TASK.xlsx")

ALLOWED_EXT = {"xlsx", "xls", "csv", "txt"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

# logging
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
_LOG = logging.getLogger("text_summarizer_app")

app = Flask(__name__, static_folder=FRONTEND_BUILD, static_url_path="/")
CORS(app)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def _get_default_dataset_path() -> str:
    """Prefer TASK.xlsx in backend else most recent file in uploads."""
    if os.path.exists(TASK_XLSX):
        return TASK_XLSX
    files = [
        os.path.join(UPLOAD_DIR, f)
        for f in os.listdir(UPLOAD_DIR)
        if os.path.isfile(os.path.join(UPLOAD_DIR, f)) and os.path.splitext(f)[1].lower() in (".xlsx", ".xls", ".csv")
    ]
    if not files:
        raise FileNotFoundError("No dataset found. Place TASK.xlsx in backend/ or upload a dataset via /api/upload-dataset.")
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files[0]


@app.before_request
def log_request():
    try:
        _LOG.info("Request: %s %s from %s", request.method, request.path, request.remote_addr)
    except Exception:
        pass


@app.route("/api/ping", methods=["GET"])
def ping():
    return jsonify(status="ok", time=datetime.utcnow().isoformat())


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    """
    Accept JSON body with:
    { "text": "some text", "sentences": 3 }
    Returns: { "summary": "..." }
    This handler will return a traceback field on error for debugging (remove after fix).
    """
    print("Received POST /api/summarize")
    data = None
    try:
        data = request.get_json(force=True, silent=True)
    except Exception:
        data = None

    # accept form-data as fallback
    if not data:
        # attempt to read form fields
        text = request.form.get("text") or request.values.get("text") or ""
        n = request.form.get("sentences") or request.values.get("sentences") or request.form.get("n") or request.values.get("n") or 3
    else:
        text = data.get("text") or data.get("input") or ""
        n = data.get("sentences", data.get("n", 3))

    try:
        n = int(n)
    except Exception:
        n = 3

    if not text or not str(text).strip():
        return jsonify(error="No text provided. Provide JSON { 'text': '...', 'sentences': 3 }"), 400

    try:
        _LOG.info("Summarizing text (len=%d) n=%d", len(text), n)
        summ = summary_text(text, n)
        return jsonify(summary=summ)
    except Exception as exc:
        # DEBUG: return traceback in response so frontend shows details (remove in production)
        _LOG.exception("Error summarizing text: %s", exc)
        tb = traceback.format_exc()
        print("Error:", str(exc))
        print("Traceback:", tb)
        return jsonify(error=str(exc), traceback=tb), 500


@app.route("/api/summarize-dataset", methods=["GET"])
def api_summarize_dataset():
    """
    Summarize default dataset (TASK.xlsx or latest uploaded).
    Query param: n=3
    """
    n = request.args.get("n", default=3)
    try:
        n = int(n)
    except Exception:
        n = 3

    try:
        dataset_path = _get_default_dataset_path()
    except FileNotFoundError as e:
        return jsonify(error=str(e)), 404

    try:
        _LOG.info("Summarizing dataset %s n=%d", dataset_path, n)
        results = summarize_dataset(excel_path=dataset_path, n=n, save_csv=True)
        return jsonify(count=len(results), results=results)
    except Exception as exc:
        _LOG.exception("Error summarizing dataset: %s", exc)
        return jsonify(error="Internal server error during dataset summarization"), 500


@app.route("/api/upload-dataset", methods=["POST"])
def api_upload_dataset():
    """
    Accepts multipart form-data with 'file' field. Allowed extensions: xlsx/xls/csv/txt
    If text file (.txt) -> read file content and summarize as a single document (returning {"summary": "..."}).
    If dataset -> summarize rows and write SummaryFile.csv.
    """
    if "file" not in request.files:
        return jsonify(error="No file part in request (field name must be 'file')"), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify(error="No file selected"), 400

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return jsonify(error=f"Disallowed extension. Allowed: {sorted(ALLOWED_EXT)}"), 400

    save_path = os.path.join(UPLOAD_DIR, filename)
    try:
        file.save(save_path)
        _LOG.info("Saved uploaded file to %s", save_path)
    except Exception as e:
        _LOG.exception("Failed saving uploaded file: %s", e)
        return jsonify(error="Failed to save uploaded file"), 500

    # handle text file separately
    ext = os.path.splitext(filename)[1].lower()
    n = request.args.get("n", default=3)
    try:
        n = int(n)
    except Exception:
        n = 3

    try:
        if ext == ".txt":
            with open(save_path, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
            summ = summary_text(text, n)
            return jsonify(summary=summ)
        else:
            # dataset summarization
            results = summarize_dataset(excel_path=save_path, n=n, save_csv=True)
            return jsonify(count=len(results), results=results)
    except Exception as exc:
        _LOG.exception("Error processing uploaded file: %s", exc)
        return jsonify(error="Internal server error processing uploaded file"), 500


# serve frontend if build exists
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        abort(404)
    if os.path.exists(os.path.join(FRONTEND_BUILD, "index.html")):
        if path and os.path.exists(os.path.join(FRONTEND_BUILD, path)):
            return send_from_directory(FRONTEND_BUILD, path)
        return send_from_directory(FRONTEND_BUILD, "index.html")
    # no frontend found
    return (
        "<h3>Text Summarizer Backend</h3>\n"
        "<p>No frontend build found. Use /api/ping, POST /api/summarize, GET /api/summarize-dataset, POST /api/upload-dataset.</p>"
    )


@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Not found"), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify(error="Internal server error"), 500


if __name__ == "__main__":
    _LOG.info("Starting backend on http://0.0.0.0:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=False)
