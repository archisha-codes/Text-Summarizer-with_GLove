# 📘 **Text Summarizer – NLP + GloVe + React Full-Stack Project**

A complete **end-to-end Text Summarization System** built using **Python (Flask)**, **NLP preprocessing**, **GloVe word embeddings**, and a **React.js frontend**.
The system allows users to input long text and instantly generate a clean, meaningful summary.

This project demonstrates your skills in:

* Machine Learning / NLP
* Full-stack development
* API design
* Frontend–backend integration
* Real-world deployment structure

---

# ⭐ **Project Overview**

The Text Summarizer is designed to automate the process of reducing long text into concise summaries using Natural Language Processing (NLP).

It consists of:

### ✅ **1. Backend — Flask + NLP + GloVe**

Handles:

* Text preprocessing
* Tokenization
* Lemmatization
* Stopword removal
* Vector generation using **GloVe embeddings**
* Sentence ranking
* Summary extraction

### ✅ **2. Frontend — React.js + Vite**

Provides:

* A clean UI
* Input box for long text
* Instant summary display
* Table for dataset preview (optional)
* Smooth API communication

---

# 🏗️ **Project Structure**

```
text-summarizer/
│
├── backend/
│   ├── app.py                 # Flask server and API endpoints
│   ├── model.py               # Summarization logic
│   ├── preprocess.py          # Text cleaning & NLP utilities
│   ├── glove/                 # GloVe embeddings (large files NOT in GitHub)
│   ├── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main UI logic
│   │   ├── components/
│   │   │   └── DatasetTable.js
│   │   ├── index.js
│   │   └── index.css
│   ├── public/index.html
│   └── package.json
│
└── README.md
```

---

# 🚀 **Features**

### 🔹 NLP-Powered Summaries

Uses tokenization, lemmatization, GloVe embeddings & similarity ranking to generate extractive summaries.

### 🔹 Clean React Interface

Interactive UI for typing/pasting long text and receiving summaries in seconds.

### 🔹 Full-Stack Integration

Backend Flask API → consumed by React frontend using Axios.

### 🔹 Dataset Table Component

Shows uploaded data (optional), useful for demos or summarizing multiple entries.

---

# 🧠 **How the Summarizer Works (NLP Logic)**

1. **Text Cleaning**
   Remove punctuation, lowercase, stopwords, unwanted symbols, etc.

2. **Sentence Tokenization**
   Split text into meaningful sentences.

3. **Vector Generation (GloVe)**
   Convert each word into a dense embedding vector.
   Average embeddings → sentence vectors.

4. **Sentence Similarity Graph**
   Use cosine similarity to form a graph of sentence relations.

5. **Sentence Ranking**
   Higher-importance sentences bubble to the top.

6. **Summary Generation**
   Pick top-ranked sentences → combine → final summary.

---

# 🖥️ **Frontend UI Flow**

* User pastes long text
* Click **Summarize**
* Frontend sends POST request to backend
* Backend responds with `"summary": "..."`
* UI displays the summarized output cleanly

---

# 🔧 **Installation & Setup**

## **1️⃣ Backend Setup (Flask)**

```
cd backend
pip install -r requirements.txt
python app.py
```

Server runs at:

```
http://localhost:5000
```

---

## **2️⃣ Frontend Setup (React + Vite)**

```
cd frontend
npm install
npm run dev
```

Runs at:

```
http://localhost:5173
```

---

# 🔗 **API Endpoints**

### **POST /summarize**

Generate summary.

#### Request:

```json
{
  "text": "Your long paragraph"
}
```

#### Response:

```json
{
  "summary": "Short meaningful summary"
}
```

---

# 💡 **Technologies Used**

### **Backend**

* Python
* Flask
* NLTK
* NumPy
* GloVe Word Embeddings

### **Frontend**

* React.js
* Vite
* Axios
* CSS

---

# 👤 **Author**

**Archisha**
ML Engineer • Full-Stack Developer

---

# 📜 **License**

MIT License

