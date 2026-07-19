# AI Placement Mentor 

An adaptive, placement-focused learning platform that pairs structured CS curriculum with a **dual-model AI stack** (fast primary model + auto-escalating fallback model) powering a grounded learning assistant, an AI mock interviewer, and an AI resume builder, plus a full analytics dashboard to track study habits.

---

## 🛠️ Tech Stack

| Layer | Choice |
| --- | --- |
| **Backend** | FastAPI (Python) |
| **Frontend** | HTML5, CSS3 (Vanilla), JavaScript (no frameworks) |
| **Database** | MongoDB (Motor async driver) |
| **Authentication** | JWT (Access + Refresh Token Pattern in HttpOnly cookies), forgot/reset password via SMTP email |
| **AI Integration** | Groq API — dual-model routing between `llama-3.3-70b-versatile` (primary, fast) and `openai/gpt-oss-120b` (fallback, deeper) |
| **Code Execution** | Sandboxed Piston API (multi-language compile/run engine) |

---

## 🌟 Key Features

### 1. Structured Learning Content
Topics grouped under domains (Python, Machine Learning, DSA, Web Dev, SDE fundamentals, and more) rendered as dynamic content blocks — explanations, code boxes, complexity notes, and external resource links.

### 2. Persistent AI Sidebar (RAG-lite)
- Grounded in the current topic's content blocks via system prompting, so answers stay on-topic.
- Adapts explanations to the user's experience level (fresher / intermediate / experienced).
- Streams completions in real time over Server-Sent Events (SSE).
- Maintains per-topic chat history in MongoDB so the assistant remembers earlier turns in that topic.
- Shortcut actions: **Explain Simply**, **Deeper Dive**, and **Quiz Me**.

### 3. AI Mock Interview Mode
A full interview simulation, not just a Q&A box:
- Choose a domain and a mode — **Coding**, **HR**, **Technical**, or **Mixed** — and a question count.
- Questions escalate in difficulty (beginner → intermediate → advanced) across the session; HR/coding questions are pulled from a curated pool first, then AI-generated once the pool is exhausted, and technical questions are always freshly AI-generated per domain.
- Each answer is graded out of 10 with strengths, weaknesses, and a model-answer hint, using a rubric tailored to the selected mode.
- An **Explain More** button gives a deeper walkthrough of the ideal answer after grading.
- Sessions can be ended early and still return a scored summary for whatever was answered.

### 4. Dual-Model AI Routing (Primary → Fallback Escalation)
The platform doesn't use one model for everything — it routes between a fast primary model and a stronger fallback model depending on the task:
- **Default**: `llama-3.3-70b-versatile` handles the AI sidebar, quick recommendations, and question generation for speed.
- **Auto-escalates to `openai/gpt-oss-120b`** when:
  - The interview mode is **Technical** (always graded by the larger model).
  - The candidate's submitted answer is **longer than 100 words** (more nuance to evaluate).
  - The primary model's JSON response fails to parse — it automatically retries once on the fallback model.
  - The user requests an **Explain More** deep dive.
  - Resume generation reaches its final drafting stage (see below).

### 5. AI Resume Builder
- Two-stage generation pipeline: the primary model first extracts an honest, ATS-aware "positioning plan" from the candidate's supplied facts (skills, projects, education, achievements, target role/job description); the fallback model then turns that plan into a polished Markdown resume.
- Explicitly instructed not to invent employers, numbers, or skills the user didn't provide.
- Supports concise vs. detailed tone, and outputs clean sectioned Markdown (Summary, Skills, Projects, Education, Achievements).

### 6. Analytics Dashboard
- Study-time overview: total minutes studied, active domains, problems solved, and a 30-day consistency percentage.
- Time-per-domain breakdown chart over a configurable period.
- Cumulative problems-solved trend line.
- Per-domain skill coverage (% of topics completed).
- Backed by an activity log that tracks minutes spent per activity type (topic study, practice, quiz) with daily streak tracking.

### 7. Practice Playground & Sandboxed Compiler
- Write solutions in **Python, JavaScript, C++, C, or Java**.
- Compiles and runs submissions against multiple test cases via the Piston API.
- Renders case-by-case results (stdin, expected, actual, stderr, status).
- Automatically marks a topic as **Completed** in user progress once all test cases pass.

### 8. Roadmap, Cheatsheets & Profile
- **Roadmap** page for structured, sequential domain learning paths.
- **Cheatsheets** page for quick-reference syntax and concept summaries.
- **Profile** page for viewing/updating experience level and interests.

### 9. JWT Authentication + Password Recovery
- Secure password hashing with `bcrypt`.
- Access + refresh token pattern with automated refresh handling in `frontend/js/auth.js` (intercepts 401s).
- Forgot-password / reset-password flow with reset tokens emailed via SMTP.

### 10. Interactive Aptitude Bank
A standalone quiz deck covering logical reasoning, mathematics, and CS fundamentals with immediate grading and explanations.

---

## 📂 Project Structure

```
├── backend/
│   ├── routes/
│   │   ├── auth.py            # Signup, login, refresh tokens, forgot/reset password
│   │   ├── content.py         # Domains and topic content blocks
│   │   ├── ai.py              # AI sidebar: grounded chat, explain, recommend (SSE streaming)
│   │   ├── mock_interview.py  # AI mock interview: sessions, question gen, grading, escalation logic
│   │   ├── resume.py          # Two-stage AI resume generation
│   │   ├── practice.py        # Piston compiler sandbox & test cases
│   │   ├── progress.py        # User progress status tracking
│   │   ├── domain_details.py  # Extended domain metadata for the interview picker
│   │   └── activity.py        # Activity logging & streaks
│   ├── auth.py                 # Password hashing & JWT encode/decode
│   ├── config.py                # Env-driven settings (Mongo, JWT, Groq models, SMTP)
│   ├── database.py              # Async MongoDB (Motor) client
│   ├── models.py                 # Pydantic request/response schemas
│   ├── seed.py.DEPRECATED_DO_NOT_RUN  # Deprecated — destructively wipes content, do not run
│   └── main.py                  # FastAPI entrypoint, lifespan hooks, static + page routing
│
├── frontend/
│   ├── css/style.css            # Shared responsive dark stylesheet
│   ├── js/
│   │   ├── auth.js              # JWT fetch wrappers & token refresh
│   │   ├── dashboard.js         # Domain cards & topic drawer logic
│   │   ├── topic.js             # Content blocks + code playground wiring
│   │   ├── ai-sidebar.js        # SSE streaming & prompt chip bindings
│   │   ├── mock-interview.js / mock-interview-page.js  # Interview flow, grading UI
│   │   ├── resume.js            # Resume builder form & Markdown render
│   │   ├── analytics.js         # Dashboard charts
│   │   ├── roadmap.js           # Roadmap page logic
│   │   ├── activity.js          # Activity/streak tracking calls
│   │   ├── profile.js           # Profile view/edit
│   │   ├── theme.js             # Theme handling
│   │   └── aptitude.js          # Standalone quiz & score tracking
│   ├── login.html / signup.html / forgot-password.html / reset-password.html
│   ├── dashboard.html           # Study workspace dashboard
│   ├── topic.html               # Dynamic learning page with AI sidebar
│   ├── mock-interview.html      # AI mock interview
│   ├── resume.html              # AI resume builder
│   ├── analytics.html           # Analytics dashboard
│   ├── roadmap.html             # Domain roadmaps
│   ├── cheatsheets.html         # Quick-reference cheatsheets
│   ├── profile.html             # User profile
│   ├── playground.html          # Standalone compiler playground
│   └── aptitude.html            # Aptitude question bank
│
├── .env                    # Secret environment keys (not committed)
├── .gitignore
├── requirements.txt
├── runtime.txt              # Python version pin for deployment
└── README.md
```

---

## ⚙️ Configuration & Installation

### 1. Prerequisites
- **Python 3.11+** (project is pinned to 3.11.9 via `runtime.txt`)
- **MongoDB** running locally (`mongodb://localhost:27017`) or a remote MongoDB Atlas URI
- **Groq API Key** — get one from [console.groq.com](https://console.groq.com/)
- (Optional) SMTP credentials, if you want live forgot/reset-password emails

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables
Create a `.env` file in the project root:
```env
MONGO_URI=mongodb://localhost:27017/education_platform
JWT_SECRET=your_super_secure_jwt_secret_key_string
GROQ_API_KEY=your_groq_api_key_here
PORT=8000

# Optional — only needed for live forgot/reset-password emails
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=noreply@eduaiplatform.local
```
> **Note**: If `GROQ_API_KEY` is left blank, all AI features (sidebar, mock interview, resume builder) automatically fall back to **Demonstration Mode** with simulated responses.

### 4. Database Content
The MongoDB database is already populated with hand-curated content (domains, topics, practice problems). The old seeding script has been deprecated and renamed to `backend/seed.py.DEPRECATED_DO_NOT_RUN` because it destructively wipes and overwrites content collections with thin placeholder data. **Do not run it.** To bootstrap a brand-new empty database, contact a maintainer first.

### 5. Launch the Server
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Open **[http://localhost:8000](http://localhost:8000)** to register and start learning.

---

## 🧭 Route Map (Pages)

| Path | Page |
| --- | --- |
| `/` , `/login` | Login |
| `/signup` | Sign up |
| `/forgot-password`, `/reset-password` | Password recovery |
| `/dashboard` | Study workspace |
| `/topic/{slug}` | Topic page with AI sidebar |
| `/playground` | Standalone compiler |
| `/aptitude` | Aptitude question bank |
| `/mock-interview` | AI mock interview |
| `/resume` | AI resume builder |
| `/roadmap` | Domain roadmaps |
| `/cheatsheets` | Cheatsheets |
| `/analytics` | Analytics dashboard |
| `/profile` | User profile |
