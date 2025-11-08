"""
Core Lead Scoring Module
Hybrid: NLP scoring + LLM characterization
"""

import json
import time
import os
from dotenv import load_dotenv
import google.generativeai as genai
from nlp_scorer import calculate_nlp_score, get_priority_label

# Load environment variables
load_dotenv()

# =============================================================================
# GEMINI CONFIGURATION
# =============================================================================

def initialize_gemini():
    """Initialize and configure Gemini API client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found! Please set it in your .env file.\n"
            "Get your API key from: https://makersuite.google.com/app/apikey"
        )
    
    genai.configure(api_key=api_key)
    
    generation_config = genai.GenerationConfig(
        response_mime_type="application/json",
        temperature=0.3,  
        max_output_tokens=200,  
        top_p=0.8,
        top_k=20
    )
    
    model = genai.GenerativeModel(
        'gemini-2.0-flash-exp',  # Gemini 2.5 Flash experimental (latest)
        generation_config=generation_config
    )
    
    return model


# =============================================================================
# INSTRUCTION PROMPT
# =============================================================================

CHARACTERIZATION_PROMPT = """You are an expert B2B SaaS Sales Development Representative (SDR).

A lead has been analyzed and given a score of {score}/100.

Based on the lead information and score, provide a brief, actionable justification (max 15 words) explaining WHY this score was assigned.

Lead Information:
- Role: {role}
- Company Size: {company_size}
- Message: {message}
- Score: {score}/100

Focus on the key factors that influenced the score (urgency, budget, authority, scale, company fit).

You MUST return ONLY a JSON object:
{{"justification": "<string max 15 words>"}}

Be concise and specific. No other text or markdown."""


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def format_lead_data(role, company_size, message):
    """
    Format lead data into a string for the AI prompt.
    
    Args:
        role (str): Job title/role
        company_size (str): Company size range
        message (str): Lead's message/inquiry
        
    Returns:
        str: Formatted lead information string
    """
    return f"Role: {role}, Company Size: {company_size}, Message: '{message}'"


def score_single_lead(model, role, company_size, message, retries=2):
    """
    Score a single lead using PURE NLP approach:
    1. Calculate score using NLP (instant, no API call)
    2. Generate justification using NLP (instant, no API call)
    
    ZERO LLM API CALLS = INSTANT RESULTS!
    
    Args:
        model: Initialized Gemini model (kept for compatibility, not used)
        role (str): Job title/role
        company_size (str): Company size range
        message (str): Lead's message/inquiry
        retries (int): Not used (kept for compatibility)
        
    Returns:
        dict: {"score": int, "justification": str, "success": bool, "error": str or None}
    """
    try:
        # Calculate score and justification using NLP ONLY (instant!)
        nlp_result = calculate_nlp_score(role, company_size, message)
        score = nlp_result['score']
        signals = nlp_result['signals']
        
        # Generate justification using NLP (no LLM call!)
        justification = generate_fallback_justification(score, signals)
        
        return {
            "score": score,
            "justification": justification,
            "success": True,
            "error": None
        }
        
    except Exception as e:
        # Even if NLP fails, return a basic result
        return {
            "score": 0,
            "justification": f"Error: {str(e)}",
            "success": False,
            "error": str(e)
        }


def generate_fallback_justification(score: int, signals: dict) -> str:
    """
    Generate justification without LLM (fallback when API fails).
    
    Args:
        score: Calculated score
        signals: Signals from NLP analysis
        
    Returns:
        str: Justification text
    """
    parts = []
    
    # Add role type
    if signals['role_type'] == 'Executive':
        parts.append("C-suite authority")
    elif signals['role_type'] == 'Decision Maker':
        parts.append("Decision maker role")
    
    # Add urgency
    if signals['is_urgent']:
        parts.append("urgent signals")
    
    # Add budget
    if signals['has_budget']:
        parts.append("budget mentioned")
    
    # Add scale
    if "Enterprise" in signals['scale_desc']:
        parts.append("enterprise scale")
    elif "Mid-market" in signals['scale_desc']:
        parts.append("mid-market scale")
    
    # Add company size
    if signals['size_category'] == 'Enterprise':
        parts.append("large company")
    
    if parts:
        return ", ".join(parts[:4])  # Max 4 factors
    elif score >= 40:
        return "Moderate fit, some positive signals"
    elif score < 40 and score > 0:
        return "Low fit, limited positive signals"
    else:
        return "Poor fit or spam indicators"


def get_priority_label(score):
    """
    Get priority label based on score.
    
    Args:
        score (int): Lead score (0-100)
        
    Returns:
        str: Priority label
    """
    if score >= 80:
        return "🔥 High Priority"
    elif score >= 40:
        return "⚠️ Medium Priority"
    elif score >= 1:
        return "❄️ Low Priority"
    else:
        return "🚫 Junk/Error"


def get_priority_color(score):
    """
    Get color code for priority based on score.
    
    Args:
        score (int): Lead score (0-100)
        
    Returns:
        str: Color name for UI
    """
    if score >= 80:
        return "red"
    elif score >= 40:
        return "orange"
    elif score >= 1:
        return "blue"
    else:
        return "gray"
