# backend/app.py
import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
from flask_cors import CORS

# Import summarization functions from summarizer.py (must exist)
# ensure summarizer.py provides: summary_text(text, n) and summarize_dataset(excel_path, text_col=None, n=5, save_csv=True)
from summarizer import summary_text, summarize_dataset  # your summarizer module

# ------------------------------
# Configuration
# ------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
FRONTEND_BUILD = os.path.join(BASE_DIR, "frontend", "build")
TASK_XLSX = os.path.join(BASE_DIR, "TASK.xlsx")  # default dataset (if present)
ALLOWED_EXT = {"xlsx", "xls", "csv"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------------------
# Logging & Flask app
# ------------------------------
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)
_LOG = logging.getLogger("text_summarizer_app")

app = Flask(__name__, static_folder=FRONTEND_BUILD, static_url_path="/")
CORS(app)  # allow all origins in development; configure for production as needed

# ------------------------------
# Helpers
# ------------------------------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def _get_default_dataset_path() -> str:
    """
    Prefer TASK.xlsx in backend folder if present; otherwise use the most recent file in uploads.
    Returns path or raises FileNotFoundError.
    """
    if os.path.exists(TASK_XLSX):
        return TASK_XLSX
    # find newest file in uploads
    files = [os.path.join(UPLOAD_DIR, f) for f in os.listdir(UPLOAD_DIR) if os.path.isfile(os.path.join(UPLOAD_DIR, f))]
    if not files:
        raise FileNotFoundError("No dataset found (no TASK.xlsx and uploads is empty). Upload a dataset first.")
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files[0]

# ------------------------------
# Request logging for debugging
# ------------------------------
@app.before_request
def log_request():
    try:
        _LOG.info("Incoming request: %s %s - from %s", request.method, request.path, request.remote_addr)
    except Exception:
        pass

# ------------------------------
# Routes
# ------------------------------
@app.route("/api/ping", methods=["GET"])
def ping():
    return jsonify(status="ok", message="Text Summarizer API is running", time=str(datetime.utcnow()))

@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    """
    POST JSON { "text": "...", "sentences": 3 }   OR   { "text": "...", "n": 3 }
    Returns: { "summary": "..." }
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify(error="Invalid JSON body"), 400

    text = data.get("text") or data.get("input") or ""
    sentences = data.get("sentences", None)
    if sentences is None:
        sentences = data.get("n", None)
    try:
        sentences = int(sentences) if sentences is not None else 3
    except Exception:
        sentences = 3

    text = (text or "").strip()
    if not text:
        return jsonify(error="No text provided"), 400

    try:
        _LOG.info("Summarizing input (len=%d) sentences=%d", len(text), sentences)
        summ = summary_text(text, sentences)
        return jsonify(summary=summ)
    except Exception as e:
        _LOG.exception("Error in summary_text:")
        return jsonify(error="Internal server error summarizing text"), 500

@app.route("/api/summarize-dataset", methods=["GET"])
def api_summarize_dataset():
    """
    Summarize default dataset (TASK.xlsx in backend or latest uploaded).
    Query param: n=3 (sentences per summary)
    Returns JSON: { count: N, results: [ { TEST DATASET, Introduction, Summary }, ... ] }
    Also writes SummaryFile.csv next to dataset file (summarize_dataset handles that).
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
        _LOG.info("Summarizing dataset at %s (n=%d)", dataset_path, n)
        results = summarize_dataset(excel_path=dataset_path, n=n, save_csv=True)
        return jsonify(count=len(results), results=results)
    except Exception as e:
        _LOG.exception("Error summarizing dataset:")
        return jsonify(error="Internal server error summarizing dataset"), 500

@app.route("/api/upload-dataset", methods=["POST"])
def api_upload_dataset():
    """
    Accepts multipart/form-data with form field 'file'.
    Saves uploaded file into backend/uploads/, runs summarize_dataset on it and returns results.
    """
    if "file" not in request.files:
        return jsonify(error="No file part in request"), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify(error="No file selected"), 400

    filename = secure_filename(file.filename)
    if not allowed_file(filename):
        return jsonify(error=f"Disallowed file extension. Allowed: {sorted(ALLOWED_EXT)}"), 400

    save_path = os.path.join(UPLOAD_DIR, filename)
    try:
        file.save(save_path)
        _LOG.info("Saved uploaded dataset to %s", save_path)
    except Exception:
        _LOG.exception("Failed to save uploaded file")
        return jsonify(error="Failed to save uploaded file"), 500

    # run summarization
    try:
        n = request.args.get("n", default=3)
        try:
            n = int(n)
        except Exception:
            n = 3
        _LOG.info("Running summarize_dataset on uploaded file %s (n=%d)", save_path, n)
        results = summarize_dataset(excel_path=save_path, n=n, save_csv=True)
        return jsonify(count=len(results), results=results)
    except Exception:
        _LOG.exception("Error summarizing uploaded dataset")
        return jsonify(error="Internal server error summarizing uploaded dataset"), 500

# ------------------------------
# Serve frontend (if build exists)
# ------------------------------
# If a frontend build is present (frontend/build/index.html), serve it and static assets.
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    # Serve API routes normally
    if path.startswith("api/"):
        abort(404)
    # If build exists, serve static
    if os.path.exists(os.path.join(FRONTEND_BUILD, "index.html")):
        if path != "" and os.path.exists(os.path.join(FRONTEND_BUILD, path)):
            return send_from_directory(FRONTEND_BUILD, path)
        else:
            return send_from_directory(FRONTEND_BUILD, "index.html")
    # If no build, show a simple message
    return (
        "<h3>Text Summarizer Backend</h3>"
        "<p>No frontend build found. Start the React dev server (frontend) or build it into backend/frontend/build.</p>"
        "<ul>"
        "<li>Health: <a href='/api/ping'>/api/ping</a></li>"
        "<li>Summarize (POST): /api/summarize</li>"
        "<li>Summarize dataset (GET): /api/summarize-dataset?n=3</li>"
        "</ul>"
    )

# ------------------------------
# Error handlers
# ------------------------------
@app.errorhandler(404)
def not_found(e):
    return jsonify(error="Not found"), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify(error="Internal server error"), 500

# ------------------------------
# Start app
# ------------------------------
if __name__ == "__main__":
    # Use 0.0.0.0 to be reachable from other hosts if needed; debug True for auto-reload during development
    _LOG.info("Starting Text Summarizer backend...")
    app.run(host="0.0.0.0", port=5000, debug=True)
