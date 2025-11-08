# 🎯 AI Lead Scoring & Prioritization Agent - Complete Documentation

**Project Type**: Full-Stack AI Web Application  
**Last Updated**: November 8, 2025

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture & Tech Stack](#2-architecture--tech-stack)
3. [Complete File Documentation](#3-complete-file-documentation)
4. [How to Start the Project](#4-how-to-start-the-project)
5. [Features & Usage](#5-features--usage)
6. [API Reference](#6-api-reference)

---

## 1. Project Overview

### Purpose
AI-powered CRM lead scoring system that automatically evaluates and prioritizes sales leads using Google's Gemini AI and NLP techniques. Scores leads from 0-100 based on urgency, budget, authority, and company size.

### Key Features
- **Real-time Scoring**: < 2 seconds per lead
- **Batch Processing**: 100+ leads with 10 concurrent workers
- **AI Chat Agent**: Ask questions about your leads
- **Visual Analytics**: Interactive dashboards
- **Export**: Download scored data as CSV

---

## 2. Architecture & Tech Stack

### System Flow
```
User (Browser)
    ↓
Streamlit Frontend (Port 8501)
    ↓ HTTP POST/GET
FastAPI Backend (Port 8000)
    ↓
NLP Scorer (Instant) + Gemini AI (Chat)
    ↓
Google Gemini 2.0 Flash
```

### Technologies

**Frontend**:
- Streamlit: Web UI
- Plotly: Charts
- Pandas: Data manipulation
- Requests: API calls

**Backend**:
- FastAPI: REST API
- Uvicorn: ASGI server
- Pydantic: Validation
- Asyncio: Concurrency

**AI/NLP**:
- Google Generative AI (Gemini 2.0 Flash)
- Custom NLP scorer (regex-based)

---

## 3. Complete File Documentation

### 📁 **backend/api.py** (389 lines)

**Purpose**: REST API server handling requests from frontend

**Key Technologies**:
- FastAPI, Uvicorn, Pydantic, Asyncio

**Main Components**:

```python
# App initialization with CORS
app = FastAPI(title="Lead Scoring API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Startup event - initialize Gemini
@app.on_event("startup")
async def startup_event():
    global model
    model = initialize_gemini()
```

**API Endpoints**:

1. **GET /** - API information
2. **GET /health** - Health check
3. **POST /score** - Score single lead
4. **POST /score/batch** - Score multiple leads (10 workers)
5. **POST /chat** - Chat about leads
6. **POST /chat/suggestions** - Get suggested questions

**Batch Processing Logic**:
```python
# 10 concurrent workers using semaphore
semaphore = asyncio.Semaphore(10)
tasks = [process_single_lead_async(lead, semaphore) for lead in batch.leads]
results = await asyncio.gather(*tasks)
```

**Configuration**:
- Host: 0.0.0.0
- Port: 8000
- Reload: True (dev mode)

---

### 📁 **backend/chat_agent.py** (518 lines)

**Purpose**: AI chat agent for lead data analysis

**Key Technologies**:
- Google Generative AI, JSON parsing, Regex

**Main Functions**:

1. **clean_value()**: Remove NaN/None/infinity
2. **convert_to_natural_language()**: JSON → readable text
3. **create_chat_prompt()**: Build context with top 10 leads
4. **chat_with_leads()**: Main chat handler
5. **handle_casual_chat()**: Non-lead conversations
6. **is_lead_related_question()**: Classify questions
7. **get_suggested_questions()**: Generate 8 suggestions

**Gemini Config for Chat**:
```python
text_config = genai.GenerationConfig(
    temperature=0.7,        # Creative
    max_output_tokens=500,  # Longer answers
    top_p=0.95, top_k=40
)
```

**Example Questions**:
- "Who are the top 5 leads?"
- "Show me all high priority leads"
- "What patterns do you see?"

---

### 📁 **backend/core_scoring.py** (220 lines)

**Purpose**: Core scoring coordination (now uses pure NLP)

**Key Technologies**:
- Google Generative AI (chat only), python-dotenv

**Main Functions**:

1. **initialize_gemini()**: Setup Gemini client
   ```python
   generation_config = genai.GenerationConfig(
       response_mime_type="application/json",
       temperature=0.3,
       max_output_tokens=200,
       top_p=0.8, top_k=20
   )
   model = genai.GenerativeModel('gemini-2.0-flash-exp')
   ```

2. **score_single_lead()**: Main scoring (instant, no API calls)
   - Calls NLP scorer
   - Generates justification
   - Returns score + explanation

3. **generate_fallback_justification()**: Create explanation from signals
   - Role type, urgency, budget, scale
   - Max 4 factors, 15 words

4. **get_priority_label()**: Score → emoji label
   - 80-100: 🔥 High Priority
   - 40-79: ⚠️ Medium Priority
   - 1-39: ❄️ Low Priority
   - 0: 🚫 Junk/Error

---

### 📁 **backend/nlp_scorer.py** (340 lines)

**Purpose**: Pure NLP scoring (instant, no API calls)

**Key Technologies**:
- Python re (regex), built-in only

**Scoring Components**:

**1. Keywords & Weights**:
```python
HIGH_PRIORITY = {
    'urgent': +15, 'asap': +15, 'deadline': +12,
    'budget allocated': +15, '$': +10,
    'enterprise': +12, 'migration': +10
}

MEDIUM_PRIORITY = {
    'demo': +8, 'trial': +7, 'pricing': +6,
    'interested': +7, 'evaluate': +8
}

NEGATIVE = {
    'student': -30, 'homework': -30, 'spam': -40,
    'free': -15, 'job': -20
}
```

**2. Role Scores**:
- Executive (CTO, CEO, VP): +25
- Decision Maker (Manager, Director): +15
- Standard: +5

**3. Company Size Multipliers**:
```python
'1-10': 0.5x, '50-200': 1.0x,
'500-1000': 1.4x, '1000+': 1.5x
```

**4. Pattern Detection** (regex):
- **Urgency**: "3 days", "deadline", "urgent" → +25 max
- **Budget**: "$50k", "budget allocated" → +20 max
- **Scale**: "500 users", "100 employees" → +15 max

**Scoring Algorithm**:
```
Base (20) + Keywords + Role + Urgency + Budget + Scale
× Company Size Multiplier
= Final Score (0-100)
```

**Returns**:
```python
{
    'score': 85,
    'breakdown': {...},
    'signals': {
        'role_type': 'Executive',
        'is_urgent': True,
        'has_budget': True,
        'scale_desc': 'Enterprise (500+ users)'
    }
}
```

---

### 📁 **frontend/streamlit_app.py** (875 lines)

**Purpose**: Web UI for lead scoring

**Key Technologies**:
- Streamlit, Plotly, Pandas, Requests, NumPy

**Main Sections**:

**1. Configuration**:
```python
BACKEND_URL = "http://localhost:8000"
st.set_page_config(page_title="Lead Scoring", layout="wide")
```

**2. Session State**:
```python
st.session_state.scored_leads = []  # All scored leads
st.session_state.backend_status = None  # API health
```

**3. API Functions**:
- `check_backend_health()`: Verify backend
- `score_lead_api()`: Score single lead
- `score_batch_api()`: Batch processing

**4. Data Cleaning**:
- `clean_lead_data_for_json()`: Remove NaN/None/infinity

**5. Visualizations**:
- Gauge charts for scores
- Distribution histograms
- Priority pie charts

**6. UI Pages**:
- Score Single Lead (manual entry)
- Batch Processing (CSV upload)
- Analytics Dashboard (charts)
- AI Chat Assistant (Q&A)
- Export Features (CSV download)

---

### 📁 **Configuration Files**

**`.env`** (156 bytes):
```env
GEMINI_API_KEY=your-actual-api-key-here
```
- Get key: https://makersuite.google.com/app/apikey
- Listed in `.gitignore` (never commit)

**`requirements.txt`** (142 bytes):
```
pandas, google-generativeai, fastapi,
uvicorn[standard], streamlit, plotly,
requests, python-dotenv, pydantic
```

**`.gitignore`**: Excludes `.env`, `.venv/`, `__pycache__/`

---

### 📁 **Documentation Files**

**`README.md`** (482 lines):
- Architecture diagrams
- Installation guide
- API documentation
- Troubleshooting

**`MODEL_INFO.md`** (118 lines):
- Gemini 2.0 Flash info
- Model comparison
- Configuration details

---

### 📁 **Startup Scripts**

**`start_all.ps1`** (28 lines):
```powershell
# Start backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", 
    "cd backend; python api.py"

# Wait 5 seconds
Start-Sleep -Seconds 5

# Start frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", 
    "cd frontend; streamlit run streamlit_app.py"
```

---

## 4. How to Start the Project

### Prerequisites

1. **Python 3.8+**: Check with `python --version`
2. **Virtual Environment**: Already in `.venv` folder
3. **Dependencies**: Install with `pip install -r requirements.txt`
4. **API Key**: Add to `.env` file

### Activation Steps

**1. Activate Virtual Environment**:

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Windows CMD:
```cmd
.venv\Scripts\activate.bat
```

**2. Install Dependencies**:
```bash
pip install -r requirements.txt
```

**3. Configure API Key**:
Edit `.env`:
```env
GEMINI_API_KEY=your-actual-key-here
```

### Starting Methods

**Method 1: Automated (Recommended)**:
```powershell
.\start_all.ps1
```
Opens both backend and frontend in separate windows.

**Method 2: Manual (2 terminals)**:

Terminal 1 - Backend:
```bash
cd backend
python api.py
```

Terminal 2 - Frontend:
```bash
cd frontend
streamlit run streamlit_app.py
```

**Method 3: Individual Services**:

Backend only:
```bash
cd backend && python api.py
```

Frontend only (requires backend):
```bash
cd frontend && streamlit run streamlit_app.py
```

### Access URLs

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Verification

1. Check backend health: http://localhost:8000/health
   Should show `"status": "healthy"`

2. Open frontend: http://localhost:8501
   Sidebar should show "✅ Backend API: Connected"

3. Test scoring:
   - Enter Role: "CTO"
   - Company Size: "500-1000"
   - Message: "Urgent migration for 300 users"
   - Click "Score Lead"
   - Should get score ~90-95

---

## 5. Features & Usage

### Feature 1: Score Single Lead

**How to Use**:
1. Click "Score Single Lead" in sidebar
2. Enter lead details:
   - Role (job title)
   - Company size (dropdown)
   - Message (inquiry text)
3. Click "Score Lead"
4. View score, justification, priority

**Scoring Example**:
- **Input**: CTO, 500-1000 employees, "Urgent migration deadline, $50k budget"
- **Output**: Score 95/100 - "C-suite authority, urgent signals, budget mentioned, enterprise scale"

### Feature 2: Batch Processing

**How to Use**:
1. Click "Batch Processing" in sidebar
2. Upload CSV file (columns: role, company_size, message)
3. Click "Process All Leads"
4. Watch progress bar (10 concurrent workers)
5. Download results as CSV

**CSV Format**:
```csv
full_name,email,company_name,role,company_size,message
John Doe,john@company.com,TechCorp,CTO,500-1000,Need urgent migration
```

### Feature 3: Analytics Dashboard

**What You See**:
- Score distribution histogram
- Priority breakdown pie chart
- Statistics (avg score, high/medium/low counts)
- Lead details table

### Feature 4: AI Chat Assistant

**How to Use**:
1. Process some leads first
2. Click "AI Chat Assistant"
3. Type questions:
   - "Who are my top 5 leads?"
   - "Show all high priority leads"
   - "Which companies have budget?"
4. Get natural language answers

**Suggested Questions**:
- Top leads analysis
- Priority breakdowns
- Pattern identification
- Budget/urgency analysis

### Feature 5: Export

**Export Options**:
- CSV download (all scored leads)
- Filtered exports (high priority only)
- Full data with scores and justifications

---

## 6. API Reference

### Endpoints

#### GET /
**Returns**: API information and endpoint list

#### GET /health
**Returns**: Health status
```json
{
  "status": "healthy",
  "timestamp": "2025-11-08T00:00:00Z",
  "gemini_initialized": true
}
```

#### POST /score
**Request**:
```json
{
  "role": "CTO",
  "company_size": "500-1000",
  "message": "Urgent migration needed"
}
```

**Response**:
```json
{
  "score": 95,
  "justification": "C-suite authority, urgent signals",
  "priority_label": "🔥 High Priority",
  "success": true,
  "error": null,
  "timestamp": "2025-11-08T00:00:00Z"
}
```

#### POST /score/batch
**Request**:
```json
{
  "leads": [
    {"role": "CTO", "company_size": "500-1000", "message": "..."},
    {"role": "Manager", "company_size": "50-200", "message": "..."}
  ]
}
```

**Response**:
```json
{
  "results": [...],
  "total": 100,
  "successful": 98,
  "failed": 2
}
```

#### POST /chat
**Request**:
```json
{
  "query": "Who are the top 5 leads?",
  "leads_data": [...]
}
```

**Response**:
```json
{
  "answer": "Based on your data, here are the top 5...",
  "success": true,
  "leads_analyzed": 100
}
```

---

## 🎯 Quick Reference

### Scoring Breakdown
- **Base**: 20 points (everyone)
- **Keywords**: 0-50 points
- **Role**: 5-25 points
- **Urgency**: 0-25 points
- **Budget**: 0-20 points
- **Scale**: 0-15 points
- **Multiplier**: 0.5x - 1.5x (company size)
- **Final**: 0-100 (capped)

### Priority Ranges
- 80-100: 🔥 High Priority (contact immediately)
- 40-79: ⚠️ Medium Priority (follow up)
- 1-39: ❄️ Low Priority (low priority)
- 0: 🚫 Junk/Spam (ignore)

### Port Configuration
- Backend: 8000
- Frontend: 8501
- Change in `api.py` line 382 and `streamlit_app.py` line 66

### File Locations
- **Backend Code**: `backend/`
- **Frontend Code**: `frontend/`
- **API Key**: `.env`
- **Dependencies**: `requirements.txt`
- **Docs**: `README.md`, `MODEL_INFO.md`

---

**Created with ❤️ using Streamlit, FastAPI, and Google Gemini AI**
