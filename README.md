# 🎯 AI Lead Scoring & Prioritization Agent

**Frontend-Backend Architecture with Google Gemini AI**

A complete lead scoring system with separated frontend and backend, powered by Google's Gemini AI.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                            │
│                   (Streamlit Frontend)                       │
│                  http://localhost:8501                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     │ HTTP POST Request
                     │ (Lead Data)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND API                                │
│                  (FastAPI Server)                            │
│                  http://localhost:8000                       │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     │ API Call
                     │ (Formatted Prompt)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  GOOGLE GEMINI LLM                           │
│              (gemini-2.0-flash-exp)                          │
│           Latest Gemini Flash 2.0 Model                      │
└─────────────────────────────────────────────────────────────┘
                     │
                     │ JSON Response
                     ▼
              (Flow returns back)
```

---

## ✨ Features

### 🎨 **Separated Architecture**
- **Frontend**: Streamlit web UI (port 8501)
- **Backend**: FastAPI REST API (port 8000)
- **LLM**: Google Gemini AI (cloud)

### 🔄 **Request Flow**
1. User enters lead info in Streamlit
2. Frontend sends HTTP POST to Backend
3. Backend formats prompt and calls Gemini
4. Gemini analyzes and returns JSON
5. Backend processes response
6. Frontend displays results to user

### 📊 **Rich Features**
- Interactive web interface
- Batch CSV upload processing
- Real-time analytics dashboard
- Score distribution charts
- Priority breakdowns
- Export to CSV

---

## 📁 Project Structure

```
CRM_SRS_HACKATHON/
│
├── 📂 frontend/                 # FRONTEND (Streamlit)
│   ├── __init__.py
│   └── streamlit_app.py        # Web UI application
│
├── 📂 backend/                  # BACKEND (FastAPI + LLM)
│   ├── __init__.py
│   ├── api.py                   # REST API server
│   └── core_scoring.py          # Gemini LLM integration
│
├── 📂 .venv/                    # Virtual environment (gitignored)
│
├── 🔐 .env                      # Environment variables
├── 📄 .env.example              # Template for .env
├── 🚫 .gitignore                # Git ignore rules
├── 📋 requirements.txt          # Python dependencies
│
├── 📊 lead_data.csv            # Sample dataset (100 leads)
│
├── 🚀 start_backend.bat        # Start backend server
├── 🚀 start_frontend.bat       # Start frontend UI
├── 🚀 start_all.ps1            # Start both (PowerShell)
│
├── 📖 README.md                # This file
│
└── 📜 (legacy files)           # Old single-file versions
    ├── lead_scorer.py
    ├── gemini_lead_scorer.py
    ├── core_scoring.py
    ├── api.py
    └── streamlit_app.py
```

---

## 🚀 Quick Start

### Option 1: Start Both Services (Recommended)

**Using PowerShell:**
```powershell
.\start_all.ps1
```

This will:
- ✅ Start backend API on http://localhost:8000
- ✅ Start frontend UI on http://localhost:8501
- ✅ Open both in separate windows

### Option 2: Start Manually

**Terminal 1 - Start Backend:**
```bash
cd backend
python api.py
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
streamlit run streamlit_app.py
```

---

## 📦 Installation

### 1. Activate Virtual Environment

**.venv already created!**

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Installed packages:**
- `pandas` - Data manipulation
- `google-generativeai` - Gemini API
- `fastapi` + `uvicorn` - Backend API
- `streamlit` - Frontend UI
- `plotly` - Interactive charts
- `requests` - HTTP communication
- `python-dotenv` - Environment management

### 3. Configure API Key

Edit `.env` file in project root:
```env
GEMINI_API_KEY=your-actual-api-key-here
```

**Get your key:** [Google AI Studio](https://makersuite.google.com/app/apikey)

---

## 🎮 Usage Guide

### 1. Start the Application

**Method A: PowerShell Script (Easiest)**
```powershell
.\start_all.ps1
```

**Method B: Batch Files**
```cmd
# Terminal 1
start_backend.bat

# Terminal 2
start_frontend.bat
```

### 2. Access the Frontend

Open your browser to: **http://localhost:8501**

### 3. Using the Web UI

#### 📝 **Score Single Lead**
1. Select "Score Single Lead" from sidebar
2. Enter role (e.g., "CTO")
3. Select company size
4. Enter message/inquiry
5. Click "Score Lead"
6. View score and justification

#### 📦 **Batch Processing**
1. Select "Batch Processing"
2. Upload CSV file (columns: role, company_size, message)
3. Click "Process All Leads"
4. Download scored results

#### 📊 **Analytics Dashboard**
1. Select "Analytics Dashboard"
2. View score distribution
3. See priority breakdowns
4. Export all data

---

## 🔌 API Endpoints

### Backend API Documentation

Access at: **http://localhost:8000/docs**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information |
| `/health` | GET | Health check (Gemini status) |
| `/score` | POST | Score single lead |
| `/score/batch` | POST | Score multiple leads |

### Example API Request

**Using curl:**
```bash
curl -X POST "http://localhost:8000/score" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "CTO",
    "company_size": "500-1000",
    "message": "Urgent migration deadline. Need enterprise plan for 300+ users."
  }'
```

**Response:**
```json
{
  "score": 95,
  "justification": "Urgent migration, enterprise scale, C-suite authority",
  "priority_label": "🔥 High Priority",
  "success": true,
  "error": null,
  "timestamp": "2025-11-07T21:59:00.000Z"
}
```

**Using Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/score",
    json={
        "role": "CTO",
        "company_size": "500-1000",
        "message": "Urgent migration needed"
    }
)

result = response.json()
print(f"Score: {result['score']}")
```

---

## 📊 Lead Scoring Criteria

The Gemini LLM evaluates leads based on:

### 🔥 High Score (80-100) - Contact Immediately
- ✅ **Urgency**: "deadline", "ASAP", "migration", "urgent"
- ✅ **Budget**: "$50k", "budget allocated", specific amounts
- ✅ **Authority**: CTO, VP, Director, C-suite roles
- ✅ **Scale**: "500+ users", "enterprise", large numbers

### ⚠️ Medium Score (40-79) - Potential Fit
- ⚠️ Vague interest: "more info", "pricing", "demo"
- ⚠️ No clear urgency or timeline
- ⚠️ Mid-level roles

### ❄️ Low Score (1-39) - Poor Fit
- ❌ Students or academic projects
- ❌ Job seekers
- ❌ Very small companies (<10 employees)

### 🚫 Junk (0) - Spam/Irrelevant
- 🚫 Spam messages
- 🚫 Irrelevant inquiries

---

## 🛠️ Troubleshooting

### Issue: Frontend shows "Backend API: Offline"

**Solution:**
1. Make sure backend is running first
2. Start backend: `python backend/api.py`
3. Check terminal for errors
4. Verify port 8000 is available

### Issue: "GEMINI_API_KEY not found"

**Solution:**
1. Check `.env` file exists in project root (not in frontend/backend folders)
2. Verify `GEMINI_API_KEY=your-key` is set
3. No quotes needed around the key
4. Restart backend server

### Issue: Port Already in Use

**Backend (port 8000):**
```python
# Edit backend/api.py, line ~240
uvicorn.run("api:app", port=8001)  # Change port
```

**Frontend (port 8501):**
```bash
streamlit run frontend/streamlit_app.py --server.port 8502
```

### Issue: Import Errors

**Solution:**
```bash
# Make sure you're in project root
cd e:\CRM_SRS_HACKATHON

# Install dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Slow Responses

**Cause:** Gemini API rate limits (free tier: ~60 requests/min)

**Solution:**
- Process smaller batches
- Add delays between requests
- Upgrade API tier if needed

---

## 🔍 Testing the Architecture

### 1. Test Backend Independently

**Start backend:**
```bash
cd backend
python api.py
```

**Test health endpoint:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-07T...",
  "gemini_initialized": true
}
```

### 2. Test Frontend-Backend Communication

1. Start both services
2. Open Streamlit UI
3. Check sidebar for "✅ Backend API: Connected"
4. Score a test lead
5. Check backend terminal for request logs

---

## 📈 Scaling to Production

### Security
- ✅ API key in environment variables
- ✅ `.env` in `.gitignore`
- ⚠️ Add authentication to API endpoints
- ⚠️ Configure CORS for specific origins
- ⚠️ Add rate limiting

### Performance
```python
# Add caching
from functools import lru_cache

# Async processing
from fastapi import BackgroundTasks

# Database
import sqlalchemy
```

### Monitoring
```python
# Logging
import logging
logging.basicConfig(level=logging.INFO)

# Metrics
from prometheus_client import Counter
```

---

## 🎓 Development

### Adding New Features

**To modify scoring logic:**
1. Edit `backend/core_scoring.py`
2. Update `INSTRUCTION_PROMPT` constant
3. Restart backend

**To modify UI:**
1. Edit `frontend/streamlit_app.py`
2. Streamlit auto-reloads on save
3. Refresh browser

**To add API endpoints:**
1. Edit `backend/api.py`
2. Add new route with `@app.post()` or `@app.get()`
3. Update frontend to call new endpoint

---

## 📚 Resources

- [Google Gemini API Docs](https://ai.google.dev/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Requests Library](https://requests.readthedocs.io/)

---

## 🤝 Support

For issues:
1. Check backend terminal for errors
2. Check frontend sidebar for connection status
3. Verify `.env` configuration
4. Test API endpoints directly
5. Check console logs in both terminals

---

## 📄 License

This project is provided as-is for educational and commercial use.

---

**Built with ❤️ using:**
- 🎨 **Frontend**: Streamlit
- 🖥️ **Backend**: FastAPI
- 🤖 **AI**: Google Gemini
- 🔄 **Communication**: HTTP/REST

🎯 Happy Lead Scoring!
