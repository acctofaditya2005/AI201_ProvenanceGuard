# Provenance Guard

An AI content attribution system that analyzes text and classifies it as likely AI-generated, likely human-written, or uncertain. It combines an LLM-based signal (Groq) with pure-Python stylometric heuristics to produce a confidence score, a human-readable transparency label, and a full audit log.

---

## Features

- **Dual-signal detection** — LLM classification (Groq llama-3.3-70b-versatile) + stylometric heuristics (sentence variance, type-token ratio, punctuation density)
- **Transparency labels** — plain-English labels with confidence percentages for each classification
- **Appeals workflow** — creators can dispute a classification; disputed submissions are flagged `under_review`
- **Audit log** — SQLite-backed log of all submissions and appeals
- **Rate limiting** — 5 requests/minute, 50 requests/day per IP

---

## Project Structure

```
.
├── app.py          # Flask app — /submit, /appeal, /log endpoints
├── signals.py      # classify_with_llm(), classify_with_stylometrics()
├── scoring.py      # compute_confidence(), get_attribution(), generate_label()
├── database.py     # SQLite setup, all read/write functions
├── requirements.txt
└── .env            # GROQ_API_KEY (not committed)
```

---

## Setup

**1. Create and activate a virtual environment:**
```
python -m venv .venv
.venv\Scripts\activate
```

**2. Install dependencies:**
```
.venv\Scripts\python.exe -m pip install flask flask-limiter groq python-dotenv
```

**3. Add your Groq API key to `.env`:**
```
GROQ_API_KEY=your_key_here
```

**4. Run the server:**
```
.venv\Scripts\python.exe app.py
```

The server starts at `http://127.0.0.1:5000`.

---

## API Reference

### `POST /submit`

Analyzes a piece of text and returns a classification.

**Rate limit:** 5/minute, 50/day per IP

**Request:**
```json
{
  "text": "The text to analyze.",
  "creator_id": "user123"
}
```

**Response:**
```json
{
  "content_id": "fee354c0-7c04-47b2-a029-4f0bc13b5a39",
  "attribution": "likely_ai",
  "confidence": 0.766,
  "llm_score": 0.8,
  "stylo_score": 0.7027,
  "label": "⚠️ Likely AI-Generated\nOur system's analysis suggests this content was likely produced with AI assistance (confidence: 77%)..."
}
```

**Attribution values:** `likely_ai` | `uncertain` | `likely_human`

---

### `POST /appeal`

Disputes a classification. Sets the submission status to `under_review` and records the appeal.

**Request:**
```json
{
  "content_id": "fee354c0-7c04-47b2-a029-4f0bc13b5a39",
  "creator_reasoning": "I wrote this myself."
}
```

**Response:**
```json
{
  "status": "under_review",
  "content_id": "fee354c0-7c04-47b2-a029-4f0bc13b5a39",
  "message": "Your appeal has been received and will be reviewed."
}
```

Returns `404` if the `content_id` does not exist.

---

### `GET /log`

Returns the 10 most recent submissions and appeals.

**Response:**
```json
{
  "submissions": [...],
  "appeals": [...]
}
```

---

## How Scoring Works

| Signal | Weight | Description |
|---|---|---|
| LLM score | 65% | Groq classifies the text and returns a 0.0–1.0 float |
| Stylometric score | 35% | Average of sentence variance, type-token ratio, punctuation density |

```
confidence = (0.65 × llm_score) + (0.35 × stylometric_score)
```

| Confidence | Attribution | Label |
|---|---|---|
| > 0.75 | `likely_ai` | ⚠️ Likely AI-Generated |
| 0.45 – 0.75 | `uncertain` | 🔍 Attribution Uncertain |
| < 0.45 | `likely_human` | ✅ Likely Human-Written |

---

## Security Notes

- All SQLite queries use parameterized `?` placeholders — no string interpolation in SQL
- LLM prompt wraps user text in `<content_to_analyze>` delimiters to prevent prompt injection
- LLM response is validated as a float in `[0.0, 1.0]` before use; raises an exception if invalid
