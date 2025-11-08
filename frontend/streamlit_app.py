"""
Streamlit Frontend for Lead Scoring & Prioritization Agent
Sends requests to FastAPI backend for lead scoring
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
import time
import math
import numpy as np

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clean_lead_data_for_json(leads_data):
    """
    Clean lead data to ensure all values are JSON-serializable.
    Removes NaN, None, and infinity values.
    """
    cleaned_leads = []
    
    for lead in leads_data:
        cleaned_lead = {}
        for key, value in lead.items():
            # Handle None
            if value is None:
                cleaned_lead[key] = 'N/A'
                continue
            
            # Handle NaN and infinity for floats
            if isinstance(value, float):
                if math.isnan(value) or math.isinf(value):
                    cleaned_lead[key] = 'N/A'
                    continue
            
            # Handle numpy types
            try:
                if np.isnan(value):
                    cleaned_lead[key] = 'N/A'
                    continue
            except (TypeError, ValueError):
                pass
            
            # Convert to string and check
            str_value = str(value)
            if str_value.lower() in ['nan', 'none', 'nat', 'inf', '-inf']:
                cleaned_lead[key] = 'N/A'
            else:
                cleaned_lead[key] = value
        
        cleaned_leads.append(cleaned_lead)
    
    return cleaned_leads


# =============================================================================
# CONFIGURATION
# =============================================================================

# Backend API URL
BACKEND_URL = "http://localhost:8000"

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Lead Scoring Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

if 'scored_leads' not in st.session_state:
    st.session_state.scored_leads = []

if 'backend_status' not in st.session_state:
    st.session_state.backend_status = None

# =============================================================================
# API COMMUNICATION FUNCTIONS
# =============================================================================

def check_backend_health():
    """Check if backend API is running and healthy."""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "healthy",
                "gemini_initialized": data.get("gemini_initialized", False)
            }
        return {"status": "unhealthy", "gemini_initialized": False}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "gemini_initialized": False}
    except Exception as e:
        return {"status": "error", "gemini_initialized": False, "error": str(e)}


def score_lead_api(role, company_size, message):
    """
    Send lead to backend API for scoring.
    
    Flow: Frontend (this) → Backend API → Gemini LLM → Backend → Frontend
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/score",
            json={
                "role": role,
                "company_size": company_size,
                "message": message
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "score": 0,
                "justification": "Backend error",
                "priority_label": "🚫 Junk/Error",
                "success": False,
                "error": f"API returned status {response.status_code}"
            }
    except requests.exceptions.Timeout:
        return {
            "score": 0,
            "justification": "Request timeout",
            "priority_label": "🚫 Junk/Error",
            "success": False,
            "error": "Request timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "score": 0,
            "justification": "Connection error",
            "priority_label": "🚫 Junk/Error",
            "success": False,
            "error": str(e)
        }


def score_batch_api(leads):
    """
    Send multiple leads to backend API for batch scoring.
    
    Flow: Frontend (this) → Backend API → Gemini LLM (batch) → Backend → Frontend
    """
    try:
        response = requests.post(
            f"{BACKEND_URL}/score/batch",
            json={"leads": leads},
            timeout=300  # 5 minutes for batch
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        st.error(f"Batch scoring failed: {e}")
        return None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_score_gauge(score):
    """Create a gauge chart for the score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Lead Score"},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 39], 'color': "lightgray"},
                {'range': [40, 79], 'color': "lightyellow"},
                {'range': [80, 100], 'color': "lightcoral"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    fig.update_layout(height=250)
    return fig


def create_distribution_chart(df):
    """Create a distribution chart of lead scores."""
    if df.empty:
        return None
    
    fig = px.histogram(
        df,
        x='score',
        nbins=20,
        title="Lead Score Distribution",
        labels={'score': 'Score', 'count': 'Number of Leads'},
        color_discrete_sequence=['#636EFA']
    )
    fig.update_layout(showlegend=False)
    return fig


def create_priority_pie_chart(df):
    """Create a pie chart showing priority distribution."""
    if df.empty:
        return None
    
    priority_counts = df['priority_label'].value_counts()
    
    fig = px.pie(
        values=priority_counts.values,
        names=priority_counts.index,
        title="Leads by Priority",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    return fig


def get_priority_color(priority_label):
    """Get color for priority label."""
    if "High" in priority_label:
        return "red"
    elif "Medium" in priority_label:
        return "orange"
    elif "Low" in priority_label:
        return "blue"
    else:
        return "gray"


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    # Check backend status
    st.session_state.backend_status = check_backend_health()
    
    # Header
    st.title("🎯 AI Lead Scoring & Prioritization Agent")
    st.markdown("**Frontend → Backend API → Google Gemini LLM**")
    st.divider()
    
    # Sidebar
    with st.sidebar:
        # Navigation
        st.header("📍 Navigation")
        page = st.radio(
            "Select Page",
            ["Batch Processing", "Analytics Dashboard", "💬 Chat Agent", "Score Single Lead"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        st.header("⚙️ System Status")
        
        # Backend Status
        status = st.session_state.backend_status
        if status["status"] == "healthy":
            st.success("✅ Backend API: Connected")
            if status["gemini_initialized"]:
                st.success("✅ Gemini LLM: Initialized")
            else:
                st.error("❌ Gemini LLM: Not Initialized")
        elif status["status"] == "offline":
            st.error("❌ Backend API: Offline")
            st.warning("⚠️ Please start the backend server:\n```python backend/api.py```")
        else:
            st.error(f"❌ Backend API: {status['status']}")
        
        st.divider()
        
        # Architecture Info
        st.header("🏗️ Architecture")
        st.markdown("""
        **Request Flow:**
        1. 📱 Frontend (Streamlit)
        2. 🔄 HTTP Request
        3. 🖥️ Backend API (FastAPI)
        4. 🤖 Gemini LLM
        5. 🔙 Response back to Frontend
        """)
        
        st.divider()
        
        # Info
        st.header("ℹ️ Scoring Criteria")
        st.markdown("""
        **High (80-100):**
        - Urgency signals
        - Budget mentions
        - Authority roles
        - Enterprise scale
        
        **Medium (40-79):**
        - General interest
        - No clear urgency
        
        **Low (1-39):**
        - Poor fit
        - Students/job seekers
        
        **Junk (0):**
        - Spam/irrelevant
        """)
    
    # Main content based on selected page
    if page == "Score Single Lead":
        show_single_lead_page()
    elif page == "Batch Processing":
        show_batch_processing_page()
    elif page == "Analytics Dashboard":
        show_analytics_page()
    elif page == "💬 Chat Agent":
        show_chat_agent_page()


# =============================================================================
# PAGE: SCORE SINGLE LEAD
# =============================================================================

def show_single_lead_page():
    st.header("📝 Score a Single Lead")
    
    # Check if backend is available
    if st.session_state.backend_status["status"] != "healthy":
        st.error("⚠️ Backend API is not available. Please start the backend server.")
        st.code("python backend/api.py", language="bash")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("lead_form"):
            st.subheader("Enter Lead Information")
            
            role = st.text_input(
                "Role/Job Title",
                placeholder="e.g., CTO, IT Director, Marketing Manager",
                help="The lead's job title or role"
            )
            
            company_size = st.selectbox(
                "Company Size",
                ["1-10", "10-50", "50-200", "200-500", "500-1000", "1000+"],
                help="Number of employees"
            )
            
            message = st.text_area(
                "Message",
                placeholder="Enter the lead's message or inquiry...",
                height=150,
                help="The lead's message, inquiry, or context"
            )
            
            submitted = st.form_submit_button("🎯 Score Lead", use_container_width=True)
        
        if submitted:
            if not role or not message:
                st.error("Please fill in all required fields (Role and Message)")
            else:
                with st.spinner("🔄 Sending to backend API... → Gemini LLM..."):
                    result = score_lead_api(role, company_size, message)
                
                if result and result.get('success'):
                    # Store in session state
                    st.session_state.scored_leads.append({
                        'role': role,
                        'company_size': company_size,
                        'message': message,
                        'score': result['score'],
                        'justification': result['justification'],
                        'priority_label': result['priority_label'],
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    st.success("✅ Lead scored successfully!")
                    
                    # Display results in col2
                    with col2:
                        st.subheader("📊 Results")
                        st.metric("Score", f"{result['score']}/100")
                        
                        # Priority badge
                        priority = result['priority_label']
                        color = get_priority_color(priority)
                        st.markdown(f"**Priority:** :{color}[{priority}]")
                        
                        st.info(f"**Justification:** {result['justification']}")
                        
                        # Gauge chart
                        fig = create_score_gauge(result['score'])
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"❌ Failed to score lead: {result.get('error', 'Unknown error')}")
    
    with col2:
        if not submitted:
            st.info("👈 Fill in the form to score a lead")
            st.markdown("---")
            st.markdown("**How it works:**")
            st.markdown("""
            1. You enter lead info
            2. Frontend sends to Backend
            3. Backend calls Gemini LLM
            4. LLM analyzes and scores
            5. Results return to you
            """)


# =============================================================================
# PAGE: BATCH PROCESSING
# =============================================================================

def show_batch_processing_page():
    st.header("📦 Batch Lead Processing")
    
    # Check if backend is available
    if st.session_state.backend_status["status"] != "healthy":
        st.error("⚠️ Backend API is not available. Please start the backend server.")
        st.code("python backend/api.py", language="bash")
        return
    
    st.info("📤 Upload a CSV file with lead data")
    st.markdown("**Required columns**: `role`, `company_size`, `message`")
    st.markdown("**Optional columns**: `full_name`, `email`, `company_name` (for better display)")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Choose CSV File",
        type=['csv'],
        help="Upload your leads CSV file"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ Loaded {len(df)} leads from file")
            
            # Validate columns
            required_cols = ['role', 'company_size', 'message']
            if not all(col in df.columns for col in required_cols):
                st.error(f"CSV must contain columns: {', '.join(required_cols)}")
                return
            
            # Show preview
            with st.expander("📄 Preview Data"):
                st.dataframe(df.head(10))
            
            # Process button
            if st.button("🚀 Process All Leads", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                time_estimate = st.empty()
                
                total_leads = len(df)
                start_time = time.time()
                
                status_text.text(f"🔄 Processing {total_leads} leads...")
                time_estimate.text("⏱️ Estimated time: Calculating...")
                
                # Process leads one by one with progress updates
                results = []
                successful = 0
                failed = 0
                
                for idx, (_, row) in enumerate(df.iterrows()):
                    # Update progress
                    progress = (idx + 1) / total_leads
                    progress_bar.progress(progress)
                    
                    # Calculate time estimates
                    if idx > 0:
                        elapsed = time.time() - start_time
                        avg_time_per_lead = elapsed / idx
                        remaining_leads = total_leads - idx
                        eta_seconds = remaining_leads * avg_time_per_lead
                        eta_minutes = int(eta_seconds / 60)
                        eta_secs = int(eta_seconds % 60)
                        time_estimate.text(f"⏱️ Processing lead {idx+1}/{total_leads} - ETA: {eta_minutes}m {eta_secs}s")
                    else:
                        time_estimate.text(f"⏱️ Processing lead {idx+1}/{total_leads}...")
                    
                    status_text.text(f"🔄 Scoring: {row.get('full_name', f'Lead #{idx+1}')}")
                    
                    # Score this lead
                    try:
                        score_result = score_lead_api(
                            role=row['role'],
                            company_size=row['company_size'],
                            message=row['message']
                        )
                        
                        if score_result and score_result.get('success'):
                            result_dict = row.to_dict()
                            result_dict['score'] = score_result['score']
                            result_dict['justification'] = score_result['justification']
                            result_dict['priority_label'] = score_result['priority_label']
                            results.append(result_dict)
                            successful += 1
                        else:
                            # Failed scoring
                            result_dict = row.to_dict()
                            result_dict['score'] = 0
                            result_dict['justification'] = 'Failed to score'
                            result_dict['priority_label'] = '🚫 Junk/Error'
                            results.append(result_dict)
                            failed += 1
                    except Exception as e:
                        result_dict = row.to_dict()
                        result_dict['score'] = 0
                        result_dict['justification'] = f'Error: {str(e)}'
                        result_dict['priority_label'] = '🚫 Junk/Error'
                        results.append(result_dict)
                        failed += 1
                
                # Complete
                total_time = time.time() - start_time
                minutes = int(total_time / 60)
                seconds = int(total_time % 60)
                
                status_text.text(f"✅ Processing complete in {minutes}m {seconds}s!")
                time_estimate.text(f"📊 Processed {successful} successful, {failed} failed")
                progress_bar.progress(100)
                
                if results:
                    
                    # Create results DataFrame
                    results_df = pd.DataFrame(results)
                    results_df = results_df.sort_values('score', ascending=False).reset_index(drop=True)
                    
                    # Store in session state
                    for result in results:
                        result['timestamp'] = datetime.now().isoformat()
                        st.session_state.scored_leads.append(result)
                    
                    # Display results
                    st.divider()
                    st.subheader("📊 Processing Results")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Leads", total_leads)
                    with col2:
                        st.metric("✅ Successful", successful)
                    with col3:
                        st.metric("❌ Failed", failed)
                    with col4:
                        avg_score = results_df['score'].mean()
                        st.metric("Avg Score", f"{avg_score:.1f}")
                    
                    st.divider()
                    
                    # ========== TOP 10 LEADS SECTION ==========
                    st.subheader("🏆 Top 10 High-Priority Leads")
                    st.markdown("**Contact these leads immediately for best conversion!**")
                    
                    top_10 = results_df.head(10)
                    
                    for idx, lead in top_10.iterrows():
                        # Determine color based on score
                        if lead['score'] >= 80:
                            card_color = "#ffebee"  # Light red
                            icon = "🔥"
                        elif lead['score'] >= 40:
                            card_color = "#fff3e0"  # Light orange
                            icon = "⚠️"
                        else:
                            card_color = "#e3f2fd"  # Light blue
                            icon = "❄️"
                        
                        with st.container():
                            st.markdown(f"""
                            <div style="background-color: {card_color}; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 5px solid {'#d32f2f' if lead['score'] >= 80 else '#f57c00' if lead['score'] >= 40 else '#1976d2'};">
                                <h3 style="margin: 0; color: #333;">{icon} #{idx+1} - Score: {lead['score']}/100</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                # Display name and company if available
                                if 'full_name' in lead and pd.notna(lead['full_name']):
                                    st.markdown(f"**👤 Name:** {lead['full_name']}")
                                
                                if 'email' in lead and pd.notna(lead['email']):
                                    st.markdown(f"**📧 Email:** {lead['email']}")
                                
                                if 'company_name' in lead and pd.notna(lead['company_name']):
                                    st.markdown(f"**🏢 Company:** {lead['company_name']}")
                                
                                st.markdown(f"**💼 Role:** {lead['role']}")
                                st.markdown(f"**📊 Company Size:** {lead['company_size']}")
                                
                            with col2:
                                st.markdown(f"**Priority:** {lead['priority_label']}")
                                st.metric("Score", f"{lead['score']}/100", delta=None)
                            
                            st.markdown(f"**💬 Message:**")
                            st.info(lead['message'])
                            
                            st.markdown(f"**🎯 AI Justification:** {lead['justification']}")
                            
                            st.markdown("---")
                    
                    st.divider()
                    
                    # Full results table
                    with st.expander("📋 View All Results (Expandable Table)"):
                        st.dataframe(
                            results_df,
                            use_container_width=True,
                            height=400
                        )
                    
                    # Download button
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Complete Results (CSV)",
                        data=csv,
                        file_name=f"scored_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        type="primary"
                    )
                else:
                    st.error("❌ No results to display. All leads failed to process.")
                
        except Exception as e:
            st.error(f"Error processing file: {e}")
            import traceback
            st.code(traceback.format_exc())


# =============================================================================
# PAGE: ANALYTICS DASHBOARD
# =============================================================================

def show_analytics_page():
    st.header("📈 Analytics Dashboard")
    
    if not st.session_state.scored_leads:
        st.info("No leads scored yet. Score some leads to see analytics!")
        return
    
    df = pd.DataFrame(st.session_state.scored_leads)
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", len(df))
    with col2:
        high = len(df[df['score'] >= 80])
        st.metric("🔥 High Priority", high)
    with col3:
        medium = len(df[(df['score'] >= 40) & (df['score'] < 80)])
        st.metric("⚠️ Medium Priority", medium)
    with col4:
        avg_score = df['score'].mean()
        st.metric("Average Score", f"{avg_score:.1f}")
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_dist = create_distribution_chart(df)
        if fig_dist:
            st.plotly_chart(fig_dist, use_container_width=True)
    
    with col2:
        fig_pie = create_priority_pie_chart(df)
        if fig_pie:
            st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    # Top leads table
    st.subheader("🏆 Top 10 Leads")
    top_leads = df.nlargest(10, 'score')[['role', 'company_size', 'score', 'justification', 'priority_label']]
    st.dataframe(top_leads, use_container_width=True)
    
    # Export all data
    st.divider()
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download All Scored Leads",
        data=csv,
        file_name=f"all_scored_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
    
    # Clear history button
    if st.button("🗑️ Clear All Data", type="secondary"):
        st.session_state.scored_leads = []
        st.rerun()


# =============================================================================
# PAGE: CHAT AGENT
# =============================================================================

def show_chat_agent_page():
    st.header("💬 Chat with AI About Your Leads")
    st.markdown("Ask questions about your scored leads and get intelligent answers powered by Gemini LLM")
    
    # Check if backend is available
    if st.session_state.backend_status["status"] != "healthy":
        st.error("⚠️ Backend API is not available. Please start the backend server.")
        st.code("python backend/api.py", language="bash")
        return
    
    # Check if there are scored leads
    if not st.session_state.scored_leads:
        st.warning("⚠️ No lead data available yet!")
        st.info("Please go to **Batch Processing** or **Score Single Lead** to process some leads first, then come back here to chat about them.")
        return
    
    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Display lead data summary
    total_leads = len(st.session_state.scored_leads)
    high_priority = len([l for l in st.session_state.scored_leads if l.get('score', 0) >= 80])
    medium_priority = len([l for l in st.session_state.scored_leads if 40 <= l.get('score', 0) < 80])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Leads", total_leads)
    with col2:
        st.metric("🔥 High Priority", high_priority)
    with col3:
        st.metric("⚠️ Medium Priority", medium_priority)
    
    st.divider()
    
    # Suggested questions
    st.subheader("💡 Suggested Questions")
    
    suggestions = [
        "Who are the top 5 leads I should contact?",
        "Show me all high priority leads with contact details",
        "What patterns do you see in high-scoring leads?",
        "Which companies have urgent needs?",
        "Who has budget approval?",
        "Compare the characteristics of high vs medium priority leads",
        "Give me a summary of leads from enterprise companies",
        "Which leads should I prioritize this week?"
    ]
    
    # Display suggestions as buttons
    cols = st.columns(2)
    for idx, suggestion in enumerate(suggestions[:6]):
        with cols[idx % 2]:
            if st.button(suggestion, key=f"suggest_{idx}", use_container_width=True):
                st.session_state.chat_input = suggestion
    
    st.divider()
    
    # Chat interface
    st.subheader("💬 Chat")
    
    # Display chat history
    if st.session_state.chat_history:
        for chat in st.session_state.chat_history:
            with st.container():
                # User question
                st.markdown(f"**You:** {chat['question']}")
                # AI response
                st.info(f"**AI:** {chat['answer']}")
                st.caption(f"🕒 {chat['timestamp']}")
                st.markdown("---")
    
    # Chat input
    user_query = st.text_input(
        "Ask me anything about your leads:",
        value=st.session_state.get('chat_input', ''),
        placeholder="e.g., Who are my top leads? or Which companies need urgent attention?",
        key="chat_input_field"
    )
    
    col1, col2 = st.columns([4, 1])
    with col1:
        send_button = st.button("💬 Send", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear Chat", type="secondary", use_container_width=True)
    
    if clear_button:
        st.session_state.chat_history = []
        st.session_state.chat_input = ''
        st.rerun()
    
    if send_button and user_query:
        with st.spinner("🤔 AI is thinking... (this may take 10-15 seconds)"):
            try:
                # Clean lead data before sending (remove NaN values)
                cleaned_leads = clean_lead_data_for_json(st.session_state.scored_leads)
                
                # Send query to backend
                response = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={
                        "query": user_query,
                        "leads_data": cleaned_leads
                    },
                    timeout=60  # Increased to 60 seconds for LLM response
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get('success'):
                        # Add to chat history
                        st.session_state.chat_history.append({
                            'question': user_query,
                            'answer': result['answer'],
                            'timestamp': datetime.now().strftime("%I:%M %p")
                        })
                        
                        # Clear input
                        st.session_state.chat_input = ''
                        st.rerun()
                    else:
                        st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                elif response.status_code == 503:
                    st.error("❌ Gemini API not initialized. Please check your API key.")
                else:
                    st.error(f"❌ Error {response.status_code}: {response.text}")
            
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out after 60 seconds. The AI might be taking too long. Try a simpler question.")
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to backend. Make sure backend is running.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
                import traceback
                st.code(traceback.format_exc())
    
    elif send_button and not user_query:
        st.warning("⚠️ Please enter a question!")


# =============================================================================
# RUN APP
# =============================================================================

if __name__ == "__main__":
    main()
