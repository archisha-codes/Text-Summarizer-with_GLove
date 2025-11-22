# Text Summarizer Full Project (with GloVe)

This project is a complete **NLP Text Summarization System** featuring:

-   **Backend (Python + NLP + GloVe)**
-   **Frontend (React.js)**
-   **REST API Integration**
-   **Dataset View & Summary Output**
-   **Machine Learning / NLP Preprocessing Pipeline**

------------------------------------------------------------------------

## 📁 Project Structure

    text_summarizer_full_project_with_glove(FINAL)
    │
    ├── backend/
    │   ├── app.py                 # Flask API backend
    │   ├── model.py               # Summarizer logic
    │   ├── preprocess.py          # NLP cleaning/tokenization utilities
    │   ├── glove/                 # Embeddings
    │   └── requirements.txt       # Backend dependencies
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
    └── README.md (this file)

------------------------------------------------------------------------

## 🚀 Features

### **Backend**

-   Clean text using NLP (tokenization, stopwords, lemmatization)
-   Generate text summaries using NLP algorithms
-   Integrates **GloVe word embeddings**
-   REST API endpoint:
    -   `/summarize` → returns generated summary\
    -   `/upload` → optional dataset upload

### **Frontend (React.js)**

-   Clean and simple UI
-   Input box for text
-   Summary output display
-   Dataset table preview
-   Connected to backend using fetch/axios

------------------------------------------------------------------------

## 🔧 Installation & Setup

### 1️⃣ **Backend Setup**

    cd backend
    pip install -r requirements.txt
    python app.py

Server starts at:

    http://localhost:5000

------------------------------------------------------------------------

### 2️⃣ **Frontend Setup**

    cd frontend
    npm install
    npm run dev

Frontend runs at:

    http://localhost:5173

------------------------------------------------------------------------

## 🔗 API Usage

### **POST /summarize**

**Request Body:**

``` json
{
  "text": "your long paragraph"
}
```

**Response:**

``` json
{
  "summary": "shortened summary"
}
```

------------------------------------------------------------------------

## ⚙️ How the Summarizer Works

1.  Text cleaning → punctuation removal, stopwords, lemmatization\
2.  Vectorization with **GloVe embeddings**\
3.  Sentence ranking using similarity metrics\
4.  Summary extraction

------------------------------------------------------------------------

## 📦 Running the Full Integrated Project

1.  Start backend\
2.  Start frontend\
3.  Enter paragraph → click *Summarize*\
4.  View output instantly

------------------------------------------------------------------------

## 🛠 Tech Stack

### **Backend:**

-   Python
-   Flask
-   NLTK
-   GloVe Embeddings

### **Frontend:**

-   React.js
-   Vite
-   Axios

------------------------------------------------------------------------

## 📝 Author

Created by **Archisha**\


------------------------------------------------------------------------

## 📜 License

MIT License
