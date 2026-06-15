# 🧠 FlowMind — ADHD Focus Intelligence System

> *Work with your brain, not against it.*

An AI-powered productivity system designed specifically for ADHD brains. FlowMind tracks tasks, focus sessions, and mood — then uses machine learning to detect procrastination patterns and Groq LLaMA 3.3 to deliver personalized, neurodivergent-affirming micro-coaching.

---

## 🎯 Why This Exists

ADHD isn't laziness — it's a dopamine and executive function challenge. Generic productivity apps ignore this. FlowMind is built from lived experience: it detects *how* you procrastinate, not just *that* you do, and responds with compassion and strategy.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Task Manager** | Add tasks with priority, category, estimated time, and due date |
| **Focus Sessions** | Pomodoro-style sessions with live timer, mood & energy tracking |
| **Procrastination Scorer** | ML-powered score (0–100) per task using delay count, abandonment rate, mood drag |
| **Pattern Clustering** | KMeans identifies your ADHD archetype: Avoider, Sprinter, Perfectionist, or Drifter |
| **Focus Hour Prediction** | LinearRegression learns your personal peak productivity windows |
| **AI Nudge Engine** | Groq LLaMA 3.3 generates personalized ADHD-aware micro-coaching messages |
| **7 Chart Dashboard** | Plotly visualizations: daily focus, mood vs productivity, streak calendar, hourly heatmap, radar chart, and more |
| **Nudge Rating** | Rate nudges helpful/not helpful — builds feedback loop |
| **Offline Fallbacks** | App works without API key; hardcoded fallback nudges ensure nothing breaks |

---

## 🏗️ Architecture

```
flowmind/
├── app.py              # Streamlit UI — 5 pages
├── database.py         # SQLite layer — 3 tables, all CRUD + analytics queries
├── ml_engine.py        # sklearn — procrastination scoring, clustering, prediction
├── ai_nudge.py         # Groq LLaMA 3.3 — prompt engineering + 7 nudge types
├── charts.py           # Plotly — 7 chart functions with dark theme
├── requirements.txt
└── README.md
```

### Data Model

```sql
tasks    → id, title, category, priority, estimated_minutes, status, delay_count
sessions → id, task_id, mood(1-5), energy(1-5), start_time, end_time, actual_minutes, completed
nudges   → id, session_id, trigger_reason, nudge_text, was_helpful
```

---

## 🤖 ML Pipeline

### Procrastination Score (0–100)
```
score = delay_count/5 × 30
      + abandonment_rate × 40
      + (1 - time_efficiency) × 15
      + mood_drag × 15
```

### Pattern Clustering (KMeans)
Four ADHD archetypes identified from session behavior:
- **The Avoider** — delays starting
- **The Sprinter** — starts strong, abandons early
- **The Perfectionist** — over-plans, under-executes
- **The Drifter** — rapid task-switching

### Focus Hour Prediction (LinearRegression)
Trained on historical session data by hour → predicts your best and worst focus windows.

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/flowmind-adhd.git
cd flowmind-adhd
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a free Groq API key
Visit [console.groq.com](https://console.groq.com) → Create account → API Keys → Create key

### 4. Run the app
```bash
streamlit run app.py
```

### 5. Enter your Groq API key in the sidebar and start tracking!

---

## 📸 App Pages

| Page | What you'll see |
|---|---|
| 🏠 Dashboard | Metrics, daily focus chart, mood vs productivity, pattern insight, weekly AI summary |
| ✅ Tasks | Add/edit/delete tasks, status updates, one-click focus start |
| ⏱️ Focus Session | Live timer, mood/energy check-in, complete or abandon with AI nudge |
| 🤖 AI Nudges | Nudge history, helpfulness ratings, manual nudge triggers |
| 📊 Analytics | Hourly heatmap, procrastination table, radar chart, category breakdown |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Database | SQLite + Pandas |
| ML | scikit-learn (KMeans, LinearRegression, MinMaxScaler) |
| AI | Groq API + LLaMA 3.3 70B |
| Charts | Plotly |
| Language | Python 3.10+ |

---

## 💡 ADHD-Specific Design Decisions

- **No streak punishment** — missing a day doesn't reset your history, just the streak counter
- **Mood-aware nudges** — low mood triggers rest suggestions, not productivity pressure
- **Task shrinking** — nudges suggest micro-steps, never the full task
- **Offline-first** — fallback nudges mean the app never breaks without an API key
- **Delay counter** — tracks how many times you've pushed a task back (visible, not shameful)

---

## 🔮 Future Roadmap

- [ ] Google Calendar sync for deadline awareness
- [ ] Body doubling mode (virtual co-working timer)
- [ ] Voice-to-task logging
- [ ] Spotify integration for focus playlists
- [ ] Export session data to CSV
- [ ] Mobile-optimized layout

---

## 👩‍💻 About

Built by **Neeta Singh** — a data analyst who has ADHD and built the tool she actually needed.

Part of a portfolio of AI-powered data projects:
- **Project 1:** [FashionFind AI](https://github.com/YOUR_USERNAME/fashionfind-ai) — RAG pipeline on Myntra data using FAISS + LLaMA 3.3
- **Project 2:** FlowMind — ADHD Focus Intelligence System ← *you are here*

---

## 📄 License

MIT License — free to use, fork, and build upon.
