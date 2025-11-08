# 🤖 AI Model Information

## Current Model: Gemini 2.0 Flash (Experimental)

**Model ID**: `gemini-2.0-flash-exp`

---

## ✨ Why Gemini 2.0 Flash?

### 🚀 **Speed & Performance**
- **Faster responses** than Gemini 1.5 Pro
- Optimized for low-latency applications
- Perfect for real-time lead scoring

### 💰 **Cost-Effective**
- Lower cost per token
- Ideal for high-volume batch processing
- Better for production deployments

### 🎯 **Quality**
- Latest model with improved reasoning
- Better understanding of context
- More accurate scoring

### 📊 **Specifications**
- **Input tokens**: Up to 1M tokens
- **Output tokens**: Up to 8K tokens
- **JSON mode**: Supported ✅
- **Streaming**: Supported
- **Languages**: Multilingual support

---

## 🔄 Model Comparison

| Feature | Gemini 1.5 Pro | Gemini 2.0 Flash | Winner |
|---------|----------------|------------------|--------|
| **Speed** | Slower | **Faster** | 🏆 Flash 2.0 |
| **Cost** | Higher | **Lower** | 🏆 Flash 2.0 |
| **Quality** | Excellent | **Excellent** | 🤝 Tie |
| **Context Window** | 2M tokens | 1M tokens | Pro |
| **Output Length** | 8K tokens | 8K tokens | 🤝 Tie |
| **JSON Mode** | ✅ | ✅ | 🤝 Tie |

---

## 📝 Use Cases

### ✅ **Perfect For:**
- Real-time lead scoring
- Batch processing (100s of leads)
- Interactive web applications
- High-volume API calls
- Cost-sensitive deployments

### ⚠️ **Consider Gemini 1.5 Pro For:**
- Very long documents (>1M tokens)
- Complex multi-step reasoning
- Maximum accuracy requirements

---

## 🔧 Configuration

The model is configured in `backend/core_scoring.py`:

```python
model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',  # Latest Gemini Flash 2.0 model
    generation_config=generation_config
)
```

---

## 🎯 For Lead Scoring

Gemini 2.0 Flash is **ideal** for this application because:

1. **Fast responses** - Users get scores in <2 seconds
2. **High accuracy** - Excellent at analyzing sales intent
3. **Cost-effective** - Can score thousands of leads affordably
4. **JSON mode** - Structured output every time
5. **Reliable** - Production-ready experimental model

---

## 🔄 Switching Models

To use a different model, edit `backend/core_scoring.py` line 36:

```python
# Options:
'gemini-2.0-flash-exp'      # Latest Flash 2.0 (Current)
'gemini-1.5-flash'           # Stable Flash 1.5
'gemini-1.5-pro-latest'      # Latest Pro 1.5
'gemini-1.5-pro'             # Stable Pro 1.5
```

Then restart the backend:
```bash
python backend/api.py
```

---

## 📚 Resources

- [Gemini Models Overview](https://ai.google.dev/models/gemini)
- [Gemini 2.0 Announcement](https://deepmind.google/technologies/gemini/flash/)
- [API Documentation](https://ai.google.dev/docs)
- [Pricing Information](https://ai.google.dev/pricing)

---

**Last Updated**: Using Gemini 2.0 Flash Experimental (Latest as of Nov 2025)
