# AI-Assisted Learning Platform 🚀

An adaptive, GeeksforGeeks/Stack Overflow-style educational platform featuring a persistent AI assistant, standard documentation layouts, a sandboxed compiler playground, and an interactive aptitude section.

---

## 🛠️ Tech Stack

| Layer | Choice |
| --- | --- |
| **Backend** | FastAPI (Python) |
| **Frontend** | HTML5, CSS3 (Vanilla), JavaScript (no frameworks) |
| **Database** | MongoDB (Motor async driver) |
| **Authentication** | JWT (Access + Refresh Token Pattern in HttpOnly cookies) |
| **AI Integration** | Groq API (`llama-3.3-70b-versatile` serving with streaming) |
| **Code Execution** | Sandboxed Piston API (Multi-language compile/run engine) |

---

## 🌟 Key Features

1. **Structured GFG-style Content**: Topics grouped under domains (Python, Machine Learning, DSA) rendered as dynamic content blocks (texts, code boxes, external link resources).
2. **Persistent AI Sidebar (RAG-lite)**:
   - Evaluates user experience level (fresher, intermediate, experienced).
   - Grounded in the topic's content blocks using system prompting.
   - Streams completions in real-time using Server-Sent Events (SSE).
   - Custom shortcut buttons: *Explain Simply* (beginner analogies), *Deeper Dive* (optimization review), and *Quiz Me* (practice questions).
3. **Practice Playground & Sandboxed Compiler**:
   - Write solutions in **Python, JavaScript, C++, C, or Java**.
   - Compiles and runs submitted code against multiple test cases via the Piston API.
   - Renders case-by-case outputs (stdin, expected, actual, stderr, status).
   - Automatically marks the topic as **Completed** in user progress upon passing all test cases.
4. **JWT Authentication**:
   - Secure passwords using `bcrypt` hashing.
   - Automated JWT token refresh handler (`frontend/js/auth.js`) intercepting 401 statuses.
5. **Interactive Aptitude Bank**:
   - A standalone quiz deck covering logical reasoning, mathematics, and CS concepts with immediate grading and detailed explanations.

---

## 📂 Project Structure

```
├── backend/
│   ├── routes/
│   │   ├── auth.py         # Sign up, Login, Refresh tokens, Profile
│   │   ├── content.py      # Domains and GFG content blocks
│   │   ├── ai.py           # Groq RAG system prompting & streaming chat
│   │   ├── practice.py     # Piston compiler sandbox & test cases
│   │   └── progress.py     # User progress status tracking
│   ├── auth.py             # Password hashing & JWT encoder/decoder
│   ├── config.py           # Configuration variables loader (.env)
│   ├── database.py         # Asynchronous MongoDB motor client
│   ├── models.py           # Pydantic schema request/response types
│   ├── seed.py.DEPRECATED_DO_NOT_RUN  # DEPRECATED - do not run, see Section 4 below
│   └── main.py             # FastAPI entrypoint, lifespan hooks, and static router
│
├── frontend/
│   ├── css/
│   │   └── style.css       # Premium responsive dark CSS stylesheet
│   ├── js/
│   │   ├── auth.js         # JWT fetch wrappers & token refreshes
│   │   ├── dashboard.js    # Domain cards loader & topic drawer logic
│   │   ├── topic.js        # Content blocks compiler & code playground
│   │   ├── ai-sidebar.js   # SSE streaming & prompt chip bindings
│   │   └── aptitude.js     # Standalone quiz & score tracking
│   ├── login.html          # Authentication login
│   ├── signup.html         # User sign up & profile interest tags
│   ├── dashboard.html      # Study workspace dashboard
│   ├── topic.html          # Dynamic learning page with AI sidebar
│   └── aptitude.html       # General aptitude question bank
│
├── .env                    # Secret environment keys
├── .gitignore              # Files excluded from git
├── requirements.txt        # Python libraries list
└── README.md               # Setup and documentation overview
```

---

## ⚙️ Configuration & Installation

### 1. Prerequisites
- **Python 3.10+** (Available at [python.org](https://www.python.org/))
- **MongoDB** running locally (`mongodb://localhost:27017`) or a remote MongoDB Atlas URI.
- **Groq API Key** (Get yours from [console.groq.com](https://console.groq.com/)).

### 2. Install Dependencies
Clone this repository and run the following command in the project root:
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Create a file named `.env` in the root folder with the following variables:
```env
MONGO_URI=mongodb://localhost:27017/education_platform
JWT_SECRET=your_super_secure_jwt_secret_key_string
GROQ_API_KEY=your_groq_api_key_here
PORT=8000
```
> **Note**: If `GROQ_API_KEY` is left blank, the AI sidebar will automatically operate in **Demonstration Mode** and serve educational simulated responses.

### 4. Database Content
This project's MongoDB database is already populated with live, hand-curated content (domains, topics, practice problems). The old seeding script (`backend/seed.py`) has been deprecated and renamed to `seed.py.DEPRECATED_DO_NOT_RUN` because it destructively wipes and overwrites all content collections with thin, outdated placeholder data. **Do not run it.** If you need to bootstrap a brand-new empty database from scratch, contact a maintainer first.

### 5. Launch the Server
Start the development server:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Open your browser and navigate to **[http://localhost:8000](http://localhost:8000)** to register and start learning!
