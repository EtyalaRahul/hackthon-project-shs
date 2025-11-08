"""
NLP-Based Lead Scoring Module
Calculate scores using built-in NLP libraries without LLM calls
"""

import re
from typing import Dict, Tuple

# =============================================================================
# SCORING KEYWORDS AND WEIGHTS
# =============================================================================

# High priority keywords (80-100 score range)
HIGH_PRIORITY_KEYWORDS = {
    'urgent': 15,
    'asap': 15,
    'deadline': 12,
    'migration': 10,
    'immediately': 12,
    'critical': 12,
    'need now': 15,
    'emergency': 12,
    'budget allocated': 15,
    'budget approved': 15,
    '$': 10,
    'contract': 10,
    'enterprise': 12,
    'going bankrupt': 15,
    'vendor failing': 12,
    'system failing': 12,
}

# Medium priority keywords (40-79 score range)
MEDIUM_PRIORITY_KEYWORDS = {
    'demo': 8,
    'trial': 7,
    'pricing': 6,
    'information': 5,
    'interested': 7,
    'looking': 6,
    'considering': 7,
    'evaluate': 8,
    'compare': 6,
    'schedule': 7,
    'meeting': 7,
    'call': 6,
}

# Negative keywords (reduce score)
NEGATIVE_KEYWORDS = {
    'student': -30,
    'free': -15,
    'school': -25,
    'university': -25,
    'college': -25,
    'homework': -30,
    'project': -10,
    'thesis': -25,
    'research': -8,
    'job': -20,
    'hiring': -25,
    'resume': -30,
    'spam': -40,
    'click here': -40,
    'make money': -40,
    'earn': -25,
}

# High-value roles
EXECUTIVE_ROLES = [
    'cto', 'ceo', 'cfo', 'coo', 'vp', 'vice president', 
    'director', 'head of', 'chief', 'president'
]

DECISION_MAKER_ROLES = [
    'manager', 'lead', 'senior', 'principal', 'architect'
]

# Company size multipliers
COMPANY_SIZE_SCORES = {
    '1-10': 0.5,
    '10-50': 0.7,
    '50-200': 1.0,
    '200-500': 1.2,
    '500-1000': 1.4,
    '1000+': 1.5,
}

# =============================================================================
# NLP SCORING FUNCTIONS
# =============================================================================

def calculate_keyword_score(message: str) -> Tuple[int, list]:
    """
    Calculate score based on keywords in message.
    
    Returns:
        Tuple of (score, matched_keywords)
    """
    message_lower = message.lower()
    score = 0
    matched = []
    
    # Check high priority keywords
    for keyword, weight in HIGH_PRIORITY_KEYWORDS.items():
        if keyword in message_lower:
            score += weight
            matched.append(f"+{weight} ({keyword})")
    
    # Check medium priority keywords
    for keyword, weight in MEDIUM_PRIORITY_KEYWORDS.items():
        if keyword in message_lower:
            score += weight
            matched.append(f"+{weight} ({keyword})")
    
    # Check negative keywords
    for keyword, weight in NEGATIVE_KEYWORDS.items():
        if keyword in message_lower:
            score += weight  # weight is negative
            matched.append(f"{weight} ({keyword})")
    
    return score, matched


def calculate_role_score(role: str) -> Tuple[int, str]:
    """
    Calculate score based on role/title.
    
    Returns:
        Tuple of (score, role_type)
    """
    role_lower = role.lower()
    
    # Check for executive roles
    for exec_role in EXECUTIVE_ROLES:
        if exec_role in role_lower:
            return 25, "Executive"
    
    # Check for decision maker roles
    for dm_role in DECISION_MAKER_ROLES:
        if dm_role in role_lower:
            return 15, "Decision Maker"
    
    # Default role score
    return 5, "Standard"


def calculate_company_size_score(company_size: str) -> Tuple[float, str]:
    """
    Get multiplier based on company size.
    
    Returns:
        Tuple of (multiplier, size_category)
    """
    multiplier = COMPANY_SIZE_SCORES.get(company_size, 1.0)
    
    if multiplier >= 1.4:
        category = "Enterprise"
    elif multiplier >= 1.0:
        category = "Mid-Market"
    else:
        category = "Small Business"
    
    return multiplier, category


def detect_urgency(message: str) -> Tuple[int, bool]:
    """
    Detect urgency signals in message.
    
    Returns:
        Tuple of (urgency_score, is_urgent)
    """
    message_lower = message.lower()
    
    urgency_patterns = [
        r'\d+\s*(day|week|month)s?',  # "3 days", "2 weeks"
        r'(deadline|due date|expires?)',
        r'(urgent|asap|immediately|critical)',
        r'(need.*now|right away)',
    ]
    
    urgency_score = 0
    is_urgent = False
    
    for pattern in urgency_patterns:
        if re.search(pattern, message_lower):
            urgency_score += 10
            is_urgent = True
    
    return min(urgency_score, 25), is_urgent


def detect_budget_signals(message: str) -> Tuple[int, bool]:
    """
    Detect budget/financial signals.
    
    Returns:
        Tuple of (budget_score, has_budget)
    """
    message_lower = message.lower()
    
    budget_patterns = [
        r'\$[\d,]+k?',  # "$50k", "$10,000"
        r'budget (allocated|approved|available)',
        r'funding (secured|approved)',
        r'\d+k budget',
    ]
    
    budget_score = 0
    has_budget = False
    
    for pattern in budget_patterns:
        if re.search(pattern, message_lower):
            budget_score += 15
            has_budget = True
    
    return min(budget_score, 20), has_budget


def detect_scale(message: str) -> Tuple[int, str]:
    """
    Detect scale indicators (number of users, locations, etc.).
    
    Returns:
        Tuple of (scale_score, scale_description)
    """
    message_lower = message.lower()
    
    # Look for numbers with "users", "employees", "locations", etc.
    scale_patterns = [
        (r'(\d+)\+?\s*(users?|employees?|staff|people)', 'users'),
        (r'(\d+)\+?\s*(locations?|offices?|sites?)', 'locations'),
        (r'(\d+)\+?\s*(teams?|departments?|divisions?)', 'teams'),
    ]
    
    scale_score = 0
    scale_desc = "Unknown scale"
    
    for pattern, unit_type in scale_patterns:
        match = re.search(pattern, message_lower)
        if match:
            number = int(match.group(1))
            if number >= 500:
                scale_score += 15
                scale_desc = f"Enterprise scale ({number}+ {unit_type})"
            elif number >= 100:
                scale_score += 10
                scale_desc = f"Mid-market scale ({number}+ {unit_type})"
            elif number >= 50:
                scale_score += 5
                scale_desc = f"Small-medium scale ({number}+ {unit_type})"
            break
    
    return scale_score, scale_desc


# =============================================================================
# MAIN SCORING FUNCTION
# =============================================================================

def calculate_nlp_score(role: str, company_size: str, message: str) -> Dict:
    """
    Calculate lead score using NLP and rule-based analysis.
    
    Args:
        role: Job title/role
        company_size: Company size range
        message: Lead's message
        
    Returns:
        Dict with score, breakdown, and signals
    """
    # Initialize base score
    base_score = 20  # Everyone starts with 20 points
    
    # Calculate component scores
    keyword_score, keywords_matched = calculate_keyword_score(message)
    role_score, role_type = calculate_role_score(role)
    size_multiplier, size_category = calculate_company_size_score(company_size)
    urgency_score, is_urgent = detect_urgency(message)
    budget_score, has_budget = detect_budget_signals(message)
    scale_score, scale_desc = detect_scale(message)
    
    # Calculate total before multiplier
    total_before_multiplier = (
        base_score + 
        keyword_score + 
        role_score + 
        urgency_score + 
        budget_score + 
        scale_score
    )
    
    # Apply company size multiplier
    final_score = int(total_before_multiplier * size_multiplier)
    
    # Cap at 100
    final_score = max(0, min(100, final_score))
    
    # Build breakdown
    breakdown = {
        'base_score': base_score,
        'keyword_score': keyword_score,
        'role_score': role_score,
        'urgency_score': urgency_score,
        'budget_score': budget_score,
        'scale_score': scale_score,
        'size_multiplier': size_multiplier,
        'final_score': final_score
    }
    
    # Build signals
    signals = {
        'role_type': role_type,
        'size_category': size_category,
        'is_urgent': is_urgent,
        'has_budget': has_budget,
        'scale_desc': scale_desc,
        'keywords_matched': keywords_matched
    }
    
    return {
        'score': final_score,
        'breakdown': breakdown,
        'signals': signals
    }


def get_priority_label(score: int) -> str:
    """Get priority label based on score."""
    if score >= 80:
        return "🔥 High Priority"
    elif score >= 40:
        return "⚠️ Medium Priority"
    elif score >= 1:
        return "❄️ Low Priority"
    else:
        return "🚫 Junk/Error"
