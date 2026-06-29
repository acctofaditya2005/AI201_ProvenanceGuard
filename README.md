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
  "content_id": "20341603-560e-4106-a935-9451fa62a54e",
  "attribution": "likely_ai",
  "confidence": 0.7686,
  "llm_score": 0.87,
  "stylo_score": 0.5803,
  "label": "⚠️ Likely AI-Generated\nOur system's analysis suggests this content was likely produced with AI assistance (confidence: 77%). This label reflects a best estimate — not a certainty. If you are the creator and believe this is incorrect, you can submit an appeal."
}
```

**Attribution values:** `likely_ai` | `uncertain` | `likely_human`

---

### `POST /appeal`

Disputes a classification. Sets the submission status to `under_review` and records the appeal.

**Request:**
```json
{
  "content_id": "ebe34f07-1bfa-47bb-abe3-a9eaa00791e4",
  "creator_reasoning": "I wrote this myself."
}
```

**Response:**
```json
{
  "status": "under_review",
  "content_id": "ebe34f07-1bfa-47bb-abe3-a9eaa00791e4",
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

## Transparency Labels

All three label variants, exactly as returned by the API:

### ⚠️ Likely AI-Generated (confidence > 0.75)
```
⚠️ Likely AI-Generated
Our system's analysis suggests this content was likely produced with AI assistance
(confidence: 77%). This label reflects a best estimate — not a certainty. If you
are the creator and believe this is incorrect, you can submit an appeal.
```

### 🔍 Attribution Uncertain (confidence 0.45–0.75)
```
🔍 Attribution Uncertain
Our system was unable to determine with confidence whether this content is
human-written or AI-generated (confidence: 62%). We're showing this label to be
transparent about that uncertainty. If you are the creator, you can submit an
appeal to provide more context.
```

### ✅ Likely Human-Written (confidence < 0.45)
```
✅ Likely Human-Written
Our system's analysis suggests this content was likely written by a person
(confidence: 68% human). No action is needed.
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

### Example: High-confidence AI text

Input: *"Artificial intelligence represents a transformative paradigm shift in modern society..."*

```json
{
  "attribution": "likely_ai",
  "confidence": 0.7686,
  "llm_score": 0.87,
  "stylo_score": 0.5803
}
```

### Example: High-confidence human text

Input: *"ok so i finally tried that new ramen place downtown and honestly? underwhelming..."*

```json
{
  "attribution": "likely_human",
  "confidence": 0.3198,
  "llm_score": 0.2,
  "stylo_score": 0.5422
}
```

The confidence scores differ by 0.45 across these two inputs, confirming the scoring function produces meaningful separation.

---

## Audit Log

Live output from `GET /log` showing submissions across all three attribution bands and one appeal in `under_review` status:

```json
{
  "appeals": [
    {
      "appeal_id": "e2d1cbac-2eee-447e-830c-c0711fae70ad",
      "appeal_timestamp": "2026-06-28T01:55:38.980451+00:00",
      "content_id": "ebe34f07-1bfa-47bb-abe3-a9eaa00791e4",
      "creator_reasoning": "I wrote this myself.",
      "original_attribution": "likely_ai",
      "original_confidence": 0.7659515366430261
    }
  ],
  "submissions": [
    {
      "attribution": "likely_human",
      "confidence": 0.2983,
      "content_id": "ad4b7383-5660-4024-86fb-498762e19dd3",
      "creator_id": "ratelimit-test",
      "llm_score": 0.1,
      "status": "classified",
      "stylo_score": 0.6667,
      "timestamp": "2026-06-28T02:13:45.881060+00:00"
    },
    {
      "attribution": "likely_human",
      "confidence": 0.3198,
      "content_id": "8e5dd07f-d6c0-4c46-8725-e940dfdfa26c",
      "creator_id": "test-user-2",
      "llm_score": 0.2,
      "status": "classified",
      "stylo_score": 0.5422,
      "timestamp": "2026-06-28T02:12:13.507951+00:00"
    },
    {
      "attribution": "likely_ai",
      "confidence": 0.7686,
      "content_id": "20341603-560e-4106-a935-9451fa62a54e",
      "creator_id": "test-user-1",
      "llm_score": 0.87,
      "status": "classified",
      "stylo_score": 0.5803,
      "timestamp": "2026-06-28T02:12:05.927890+00:00"
    },
    {
      "attribution": "likely_ai",
      "confidence": 0.766,
      "content_id": "ebe34f07-1bfa-47bb-abe3-a9eaa00791e4",
      "creator_id": "user1",
      "llm_score": 0.8,
      "status": "under_review",
      "stylo_score": 0.7027,
      "timestamp": "2026-06-28T01:53:17.512817+00:00"
    }
  ]
}
```

Note: `ebe34f07` shows `status: under_review` — this submission had an appeal filed against it.

---

## Rate Limiting

`POST /submit` is limited to 5 requests per minute per IP. Requests exceeding the limit return HTTP 429:

```
200
200
200
200
200
429
429
```

---

## Security Notes

- All SQLite queries use parameterized `?` placeholders — no string interpolation in SQL
- LLM prompt wraps user text in `<content_to_analyze>` delimiters to prevent prompt injection
- LLM response is validated as a float in `[0.0, 1.0]` before use; raises an exception if invalid

## Known Limitations

**Formal human writing misclassified as AI-generated.**
Academic essays, legal documents, and professional reports share the same statistical profile that the stylometric signal associates with AI output — low sentence length variance, controlled vocabulary, and uniform punctuation. A student submitting a well-structured research paper could receive an "uncertain" or even "likely AI-generated" label despite the work being entirely their own. This happens because the stylometric signal measures uniformity, not intent — it cannot distinguish between "uniform because AI" and "uniform because carefully edited." The LLM signal can partially compensate by reading tone and naturalness, but formal human writing is precisely the category where the LLM is also most likely to find the text "polished and coherent." Both signals can fail in the same direction on this content type.

**Adversarially casual AI output misclassified as human-written.**
If a user prompts an LLM to write in a deliberately messy, informal style — with sentence fragments, irregular punctuation, and colloquial language — the resulting text can have high sentence variance and diverse punctuation patterns that the stylometric signal associates with human writing. The LLM signal may also find the casual tone convincing. This is a known, unsolvable limitation of any current AI detection system. The system's wide uncertain band (0.45–0.75) and appeals workflow exist precisely because no classifier is perfect — creators who are misclassified have a documented path to contest the label.

---

## Spec Reflection

**One way the spec helped:** The planning document's requirement to define exact confidence thresholds before writing any code was the most useful constraint in the project. Having the 0.75 and 0.45 cutoffs decided upfront meant the label generation function had concrete rules to implement against, rather than requiring judgment calls mid-implementation. It also made testing straightforward — I could deliberately construct inputs targeting each band and verify the right label appeared.

**One way implementation diverged from the plan:** The planning document specified that the LLM signal should raise an exception if the response is not a valid float, with the intent of surfacing problems loudly during development. In practice, the Groq API occasionally returned responses where the JSON was valid but the score value was slightly outside the 0.0–1.0 range due to floating point representation (e.g., 1.0000000002). Treating these as hard exceptions caused unnecessary failures on otherwise good responses. The implementation was updated to clamp the value to [0.0, 1.0] after validation rather than rejecting it outright — a small but meaningful divergence from the original spec that made the system more robust without compromising correctness.

---

## AI Usage

**Instance 1: Generating the Flask skeleton and LLM signal function**

I directed Claude to generate the Flask app skeleton (`app.py`), the `classify_with_llm()` function in `signals.py`, the SQLite database setup in `database.py`, and the `GET /log` endpoint. I provided my planning.md's detection signals section and architecture diagram as context, and specified that the LLM prompt must wrap user text in `<content_to_analyze>` XML delimiters for prompt injection protection and that all database writes must use parameterized `?` queries.

What I revised: The generated `classify_with_llm()` function returned the raw JSON object from Groq rather than extracting the float score. I updated it to parse `response.content[0].text`, load it as JSON, and extract the `score` key explicitly. I also added the float range validation step (clamping to [0.0, 1.0]) which the generated code omitted. The database schema the AI generated used `TEXT` for the confidence column — I changed it to `REAL` so SQLite stores it as a proper float for numeric comparisons.

**Instance 2: Generating the transparency label function and appeals endpoint**

I directed Claude to generate the `generate_label()` function in `scoring.py` and the `POST /appeal` endpoint in `app.py`, providing the exact label text for all three variants from my planning.md and the appeals workflow section specifying that status must update to `"under_review"` and a separate appeals table must be written to.

What I revised: The generated `generate_label()` function displayed the raw confidence float directly in the label text (e.g., "confidence: 0.766") rather than converting it to a rounded percentage. I updated it to use `round(confidence * 100)` for the AI and uncertain labels and `round((1 - confidence) * 100)` for the human label, matching the spec. The appeals endpoint the AI generated did not return a 404 when an invalid `content_id` was submitted — it silently inserted an appeal record with a null foreign key. I added the lookup-first check and the 404 response before any write occurs.
