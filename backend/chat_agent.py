"""
Chat Agent for Lead Data Analysis
Uses LLM to answer questions about scored leads
"""

import json
import google.generativeai as genai

def clean_value(value):
    """Clean a value to ensure it's JSON-compatible."""
    import math
    import numpy as np
    
    # Handle None
    if value is None:
        return 'N/A'
    
    # Handle NaN and infinity
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 'N/A'
    
    # Handle numpy NaN
    try:
        if np.isnan(value):
            return 'N/A'
    except (TypeError, ValueError):
        pass
    
    # Convert to string and check
    str_value = str(value)
    if str_value.lower() in ['nan', 'none', 'nat', 'inf', '-inf']:
        return 'N/A'
    
    return value


def convert_to_natural_language(response_text: str, query: str) -> str:
    """
    Convert JSON or structured response to natural, readable language.
    
    Args:
        response_text: Raw response from LLM
        query: Original user query
        
    Returns:
        str: Human-readable text
    """
    # Clean up the response text
    response_text = response_text.strip()
    
    # Check if response looks like JSON (starts with { or [)
    if response_text.startswith('{') or response_text.startswith('['):
        try:
            # Try to parse as JSON
            data = json.loads(response_text)
            
            # Convert based on query type
            query_lower = query.lower()
            
            if "least" in query_lower or "lowest" in query_lower:
                return format_least_score_response(data, query)
            elif "top" in query_lower or "best" in query_lower or "high" in query_lower:
                return format_top_leads_response(data)
            elif "who" in query_lower or "which" in query_lower:
                return format_who_response(data)
            elif "all" in query_lower and "lead" in query_lower:
                return format_all_leads_response(data)
            else:
                return format_general_response(data)
                
        except (json.JSONDecodeError, TypeError) as e:
            # JSON parsing failed, but it looks like JSON
            # Return a friendly error message
            return f"I found some information, but I'm having trouble formatting it nicely. Here's what I found:\n\n{response_text[:500]}..."
    
    # Not JSON, return as is
    return response_text


def format_top_leads_response(data) -> str:
    """Format JSON data about top leads into readable text."""
    if isinstance(data, dict):
        # Single lead analysis
        if "analysis" in data or "summary" in data:
            return data.get("analysis", data.get("summary", str(data)))
        
        # Top leads breakdown
        if "top_leads" in data:
            leads = data["top_leads"]
        else:
            leads = [data]
    elif isinstance(data, list):
        leads = data
    else:
        return str(data)
    
    # Build natural response
    response = "Based on your lead data, here are the top leads you should prioritize:\n\n"
    
    for idx, lead in enumerate(leads[:5], 1):
        if isinstance(lead, dict):
            name = lead.get("name", "Unknown")
            company = lead.get("company", "N/A")
            score = lead.get("score", 0)
            role = lead.get("role", "N/A")
            priority = lead.get("priority", "")
            
            response += f"**{idx}. {name}** - {role}\n"
            response += f"   • Company: {company}\n"
            response += f"   • Score: {score}/100 {priority}\n"
            
            if "justification" in lead:
                response += f"   • Why: {lead['justification']}\n"
            
            response += "\n"
    
    return response


def format_who_response(data) -> str:
    """Format 'who is' type questions."""
    if isinstance(data, dict):
        name = data.get("name", "Unknown")
        company = data.get("company", "N/A")
        score = data.get("score", 0)
        role = data.get("role", "N/A")
        email = data.get("email", "N/A")
        
        response = f"The top lead is **{name}**\n\n"
        response += f"📋 **Details:**\n"
        response += f"• Role: {role}\n"
        response += f"• Company: {company}\n"
        response += f"• Score: {score}/100\n"
        response += f"• Email: {email}\n\n"
        
        if "justification" in data:
            response += f"🎯 **Why this lead matters:**\n{data['justification']}\n"
        
        return response
    
    return str(data)


def format_least_score_response(data, query) -> str:
    """Format response for 'least score' or 'lowest score' questions."""
    if isinstance(data, dict):
        # Extract lead info from various possible structures
        if "zeroScoreLeads" in data:
            count = data.get("zeroScoreLeads", 0)
            return f"You have **{count} leads with a score of 0**. These are typically spam, students, or completely irrelevant inquiries that you should ignore."
        
        if "lowPriorityLeads" in data:
            leads = data.get("lowPriorityLeads", [])
            if leads:
                response = f"Here are your lowest-scoring leads:\n\n"
                for idx, lead in enumerate(leads[:5], 1):
                    if isinstance(lead, dict):
                        name = lead.get("name", "Unknown")
                        score = lead.get("score", 0)
                        reason = lead.get("reason", "Poor fit")
                        response += f"{idx}. **{name}** - Score: {score}/100\n   Reason: {reason}\n\n"
                return response
    
    # Fallback to general formatting
    return format_general_response(data)


def format_all_leads_response(data) -> str:
    """Format response for 'show all leads' questions."""
    if isinstance(data, list):
        response = "Here's a summary of all your leads:\n\n"
        
        # Group by priority
        high_priority = [l for l in data if isinstance(l, dict) and l.get('score', 0) >= 80]
        medium_priority = [l for l in data if isinstance(l, dict) and 40 <= l.get('score', 0) < 80]
        low_priority = [l for l in data if isinstance(l, dict) and 0 < l.get('score', 0) < 40]
        
        if high_priority:
            response += f"🔥 **High Priority ({len(high_priority)} leads):**\n"
            for lead in high_priority[:5]:
                name = lead.get("name", "Unknown")
                company = lead.get("company", "N/A")
                score = lead.get("score", 0)
                response += f"• {name} from {company} - {score}/100\n"
            if len(high_priority) > 5:
                response += f"  ...and {len(high_priority) - 5} more\n"
            response += "\n"
        
        if medium_priority:
            response += f"⚠️ **Medium Priority ({len(medium_priority)} leads):**\n"
            response += f"Focus on these after contacting high-priority leads\n\n"
        
        if low_priority:
            response += f"❄️ **Low Priority ({len(low_priority)} leads):**\n"
            response += f"Consider these if you have extra capacity\n"
        
        return response
    
    return format_general_response(data)


def format_general_response(data) -> str:
    """Format general JSON responses into readable text."""
    if isinstance(data, dict):
        response = ""
        
        # Check for common summary keys first
        if "summary" in data:
            return str(data["summary"])
        if "analysis" in data:
            return str(data["analysis"])
        if "answer" in data:
            return str(data["answer"])
        if "response" in data:
            return str(data["response"])
        
        # Check for lead-related keys
        if "highPriorityLeads" in data:
            high_count = data.get("highPriorityLeads", 0)
            medium_count = data.get("mediumPriorityLeads", 0)
            low_count = data.get("lowPriorityLeads", 0)
            
            response = f"**Lead Summary:**\n\n"
            response += f"🔥 High Priority: {high_count} leads\n"
            response += f"⚠️ Medium Priority: {medium_count} leads\n"
            response += f"❄️ Low Priority: {low_count} leads\n\n"
            
            if "topLeads" in data:
                leads = data["topLeads"]
                response += "\n**Top Leads to Contact:**\n"
                for idx, lead in enumerate(leads[:5], 1):
                    if isinstance(lead, dict):
                        name = lead.get("name", "Unknown")
                        company = lead.get("company", "N/A")
                        score = lead.get("score", 0)
                        response += f"{idx}. {name} from {company} ({score}/100)\n"
            
            return response
        
        # Generic dict formatting
        for key, value in data.items():
            response += f"**{key.replace('_', ' ').title()}:**\n"
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        # Format dict items nicely
                        name = item.get("name", item.get("title", "Item"))
                        response += f"• {name}\n"
                    else:
                        response += f"• {item}\n"
            elif isinstance(value, dict):
                for k, v in value.items():
                    response += f"  {k}: {v}\n"
            else:
                response += f"{value}\n"
            response += "\n"
        
        return response if response else str(data)
        
    elif isinstance(data, list):
        response = ""
        for idx, item in enumerate(data, 1):
            if isinstance(item, dict):
                name = item.get("name", item.get("title", f"Item {idx}"))
                score = item.get("score", "")
                score_str = f" - {score}/100" if score else ""
                response += f"{idx}. {name}{score_str}\n"
            else:
                response += f"{idx}. {item}\n"
        return response
    
    return str(data)


def create_chat_prompt(query: str, leads_data: list) -> str:
    """
    Create a prompt for the chat agent with lead data context.
    
    Args:
        query: User's question
        leads_data: List of scored leads
        
    Returns:
        str: Formatted prompt for LLM
    """
    # Prepare data summary
    total_leads = len(leads_data)
    high_priority = len([l for l in leads_data if l.get('score', 0) >= 80])
    medium_priority = len([l for l in leads_data if 40 <= l.get('score', 0) < 80])
    low_priority = len([l for l in leads_data if 0 < l.get('score', 0) < 40])
    
    # Get top 10 AND bottom 5 leads for context
    sorted_leads = sorted(leads_data, key=lambda x: x.get('score', 0), reverse=True)
    top_leads = sorted_leads[:10]
    bottom_leads = sorted_leads[-5:] if len(sorted_leads) > 10 else []
    
    # Format top leads
    top_leads_text = ""
    for idx, lead in enumerate(top_leads, 1):
        name = clean_value(lead.get('full_name', 'Unknown'))
        company = clean_value(lead.get('company_name', 'N/A'))
        role = clean_value(lead.get('role', 'N/A'))
        score = int(lead.get('score', 0)) if lead.get('score') else 0
        email = clean_value(lead.get('email', 'N/A'))
        justification = clean_value(lead.get('justification', 'N/A'))
        
        top_leads_text += f"\n{idx}. {name} from {company} - {role} - Score: {score}/100 - Email: {email}"
        if justification and justification != 'N/A':
            top_leads_text += f"\n   Why: {justification}"
    
    # Format bottom leads
    bottom_leads_text = ""
    if bottom_leads:
        for idx, lead in enumerate(bottom_leads, 1):
            name = clean_value(lead.get('full_name', 'Unknown'))
            company = clean_value(lead.get('company_name', 'N/A'))
            role = clean_value(lead.get('role', 'N/A'))
            score = int(lead.get('score', 0)) if lead.get('score') else 0
            email = clean_value(lead.get('email', 'N/A'))
            
            bottom_leads_text += f"\n{idx}. {name} from {company} - {role} - Score: {score}/100 - Email: {email}"
    
    prompt = f"""You are a helpful AI Sales Assistant. A sales team member is asking you about their leads.

CONTEXT - You have analyzed {total_leads} leads:
• {high_priority} High Priority leads (scores 80-100)
• {medium_priority} Medium Priority leads (scores 40-79)  
• {low_priority} Low Priority leads (scores 1-39)

TOP 10 HIGHEST-SCORING LEADS:{top_leads_text}

LOWEST-SCORING 5 LEADS:{bottom_leads_text}

QUESTION: {query}

CRITICAL INSTRUCTIONS - YOU MUST FOLLOW EXACTLY:
1. Write your answer as a CONVERSATIONAL PARAGRAPH, like you're talking to a friend
2. DO NOT use lists, bullet points, numbered items, or structured formats
3. DO NOT use quotation marks around field values
4. DO NOT separate data with commas like "name", "company", "role"
5. Write full sentences that flow naturally
6. Include names, titles, companies, and emails IN the sentences naturally

GOOD EXAMPLE (what TO do):
"Based on your leads, I'd recommend reaching out to Jacob Turner first. He's a COO at Prime Consulting with a perfect score of 100/100, and you can contact him at jacob.turner@corp.com. He has urgent needs for vendor replacement. Your second priority should be Patricia Brown who is the Operations Director at Strategic Ventures, also scoring 100/100. Her email is patricia.brown@business.com and she's dealing with a critical platform issue."

BAD EXAMPLE (what NOT to do):
"Jacob Turner", "Prime Consulting", "COO", "100/100", "jacob.turner@corp.com"

Now write your answer as a natural, flowing paragraph:"""

    return prompt


def handle_casual_chat(model, query: str, leads_data: list) -> dict:
    """
    Handle casual, non-lead-related conversation.
    
    Args:
        model: Initialized Gemini model
        query: User's casual question
        leads_data: List of scored leads (for context)
        
    Returns:
        dict: Friendly response
    """
    try:
        # Create a simple conversational prompt
        casual_prompt = f"""You are a friendly AI assistant helping a sales team. 
The user just asked you a casual question that's not about their leads.

USER QUESTION: {query}

Respond naturally and friendly, then gently remind them you're here to help with their lead data if needed.

Keep your response brief (1-2 sentences) and friendly."""

        # Create text-only config for casual chat
        text_config = genai.GenerationConfig(
            temperature=0.9,  # More creative for casual chat
            max_output_tokens=150,
            top_p=0.95
        )
        
        response = model.generate_content(casual_prompt, generation_config=text_config)
        answer = response.text.strip()
        
        return {
            "answer": answer,
            "success": True,
            "error": None,
            "leads_analyzed": 0  # Not a lead query
        }
        
    except Exception as e:
        # Fallback for casual chat
        return {
            "answer": "I'm doing well, thank you! 😊 Is there anything about your leads I can help you with?",
            "success": True,
            "error": None,
            "leads_analyzed": 0
        }


def is_lead_related_question(query: str) -> bool:
    """
    Determine if the question is about lead data or just casual conversation.
    
    Args:
        query: User's question
        
    Returns:
        bool: True if about leads, False if casual chat
    """
    query_lower = query.lower()
    
    # Lead-related keywords
    lead_keywords = [
        'lead', 'leads', 'score', 'priority', 'contact', 'call', 'email',
        'company', 'companies', 'customer', 'prospect', 'sales',
        'top', 'best', 'highest', 'lowest', 'budget', 'urgent',
        'who', 'which', 'what', 'show', 'list', 'tell me about',
        'recommend', 'prioritize', 'focus', 'crm', 'deal'
    ]
    
    # Check if any lead keyword is in the question
    return any(keyword in query_lower for keyword in lead_keywords)


def chat_with_leads(model, query: str, leads_data: list) -> dict:
    """
    Process a chat query with SMART API USAGE to minimize rate limits.
    
    STEP 1: Query leads data and get response (1 API call)
    STEP 2: Check if conversion needed - ONLY make 2nd API call if format is bad
    STEP 3: Python post-processing to strip any remaining JSON wrappers
    
    This approach minimizes API calls (usually just 1) while ensuring natural text output.
    
    Args:
        model: Initialized Gemini model
        query: User's question
        leads_data: List of scored leads
        
    Returns:
        dict: Response with answer (guaranteed plain text) and metadata
    """
    try:
        # Check if question is about leads or just casual chat
        if not is_lead_related_question(query):
            # Handle casual conversation
            return handle_casual_chat(model, query, leads_data)
        
        # Handle lead-related questions
        if not leads_data:
            return {
                "answer": "No lead data available yet. Please process some leads first!",
                "success": True,
                "error": None
            }
        
        # Create prompt with data context
        prompt = create_chat_prompt(query, leads_data)
        
        # Create a text-only generation config (override JSON mode)
        text_config = genai.GenerationConfig(
            temperature=0.7,  # More creative for chat
            max_output_tokens=500,  # Allow longer responses
            top_p=0.95,
            top_k=40
            # NO response_mime_type - defaults to plain text!
        )
        
        # ============================================================
        # STEP 1: Get raw response from LLM (might be JSON/structured)
        # ============================================================
        response = model.generate_content(
            prompt,
            generation_config=text_config
        )
        raw_answer = response.text.strip()
        
        # ============================================================
        # STEP 2: Check if conversion is needed (avoid extra API call)
        # Only do second LLM call if response has problematic formatting
        # ============================================================
        import re
        
        # Check if raw answer has problematic formatting
        needs_conversion = False
        
        # Pattern 1: Starts with JSON object
        if raw_answer.startswith('{') and raw_answer.endswith('}'):
            needs_conversion = True
        # Pattern 2: Multiple comma-separated quoted strings
        elif re.search(r'"[^"]+"\s*,\s*"[^"]+"\s*,\s*"[^"]+"', raw_answer):
            needs_conversion = True
        # Pattern 3: Contains JSON field names
        elif any(term in raw_answer.lower() for term in ['"summary":', '"response":', '"answer":', '"message":']):
            needs_conversion = True
        
        if needs_conversion:
            # Make second API call to convert to natural language
            conversion_prompt = f"""Rewrite this as natural, conversational text without any JSON or structured formatting:

{raw_answer}

Write it as if you're talking to a colleague. No quotes, brackets, or comma-separated values. Just natural sentences."""

            conversion_config = genai.GenerationConfig(
                temperature=0.7,
                max_output_tokens=500
            )
            
            conversion_response = model.generate_content(
                conversion_prompt,
                generation_config=conversion_config
            )
            answer = conversion_response.text.strip()
        else:
            # Already natural language, skip second API call
            answer = raw_answer
        
        # ============================================================
        # STEP 3: Python post-processing to remove any remaining JSON
        # ============================================================
        import re
        
        # Try to parse as JSON and extract text content
        try:
            # Check if it's still JSON
            if answer.startswith('{') and answer.endswith('}'):
                data = json.loads(answer)
                # Extract from common JSON fields
                if 'summary' in data:
                    answer = data['summary']
                elif 'response' in data:
                    answer = data['response']
                elif 'answer' in data:
                    answer = data['answer']
                elif 'message' in data:
                    answer = data['message']
        except (json.JSONDecodeError, KeyError):
            # Not JSON or failed to parse, keep as is
            pass
        
        # Check if answer is comma-separated quoted strings (e.g., "name", "company", "role")
        # Pattern: multiple quoted strings separated by commas
        if re.search(r'"[^"]+"\s*,\s*"[^"]+"', answer):
            # This is structured data, convert to readable text
            # Extract all quoted values
            values = re.findall(r'"([^"]+)"', answer)
            if len(values) >= 3:
                # Try to reconstruct as natural text
                # Assume pattern might be: name, company, role, score, email
                answer = f"Lead information: {' | '.join(values)}"
        
        # Remove any remaining quotes around the entire string
        answer = answer.strip('"').strip("'")
        
        return {
            "answer": answer,
            "success": True,
            "error": None,
            "leads_analyzed": len(leads_data)
        }
        
    except Exception as e:
        error_msg = str(e)
        
        # Handle rate limit errors specifically
        if "429" in error_msg or "Resource exhausted" in error_msg:
            return {
                "answer": "I've hit the API rate limit. The free tier of Gemini API has limited requests per minute. Please wait a moment and try again, or consider upgrading your API plan.",
                "success": False,
                "error": "Rate limit exceeded (429)",
                "leads_analyzed": len(leads_data) if leads_data else 0
            }
        
        return {
            "answer": f"Sorry, I encountered an error: {error_msg}",
            "success": False,
            "error": error_msg,
            "leads_analyzed": len(leads_data) if leads_data else 0
        }


def get_suggested_questions(leads_data: list) -> list:
    """
    Generate suggested questions based on available data.
    
    Args:
        leads_data: List of scored leads
        
    Returns:
        list: Suggested questions
    """
    if not leads_data:
        return [
            "How do I get started?",
            "What can you help me with?"
        ]
    
    high_priority = len([l for l in leads_data if l.get('score', 0) >= 80])
    
    suggestions = [
        "Who are the top 5 leads I should contact?",
        "Show me all high priority leads",
        "What patterns do you see in high-scoring leads?",
        "Which companies have urgent needs?",
        "Who has budget approval?",
        "What industries are represented in top leads?",
        "Compare high vs medium priority leads",
        "Give me contact details for top 3 leads"
    ]
    
    if high_priority > 0:
        suggestions.insert(0, f"Tell me about the {high_priority} high priority leads")
    
    return suggestions[:8]
