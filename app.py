import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from database import init_db, log_submission, get_recent_logs, get_submission, set_status_under_review, log_appeal
from signals import classify_with_llm, classify_with_stylometrics
from scoring import compute_confidence, get_attribution, generate_label

app = Flask(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=[],
)

init_db()


@app.route("/submit", methods=["POST"])
@limiter.limit("5 per minute;50 per day")
def submit():
    body = request.get_json(silent=True) or {}
    text = body.get("text", "")
    creator_id = body.get("creator_id", "")

    if not text:
        return jsonify({"error": "text is required"}), 400

    try:
        llm_score = classify_with_llm(text)
    except Exception as exc:
        return jsonify({"error": f"LLM classification failed: {exc}"}), 502

    stylo_score = classify_with_stylometrics(text)

    confidence = compute_confidence(llm_score, stylo_score)
    attribution = get_attribution(confidence)
    label = generate_label(confidence)
    content_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    log_submission(
        content_id=content_id,
        creator_id=creator_id,
        timestamp=timestamp,
        attribution=attribution,
        confidence=confidence,
        llm_score=llm_score,
        stylo_score=stylo_score,
    )

    return jsonify(
        {
            "content_id": content_id,
            "attribution": attribution,
            "confidence": round(confidence, 4),
            "llm_score": round(llm_score, 4),
            "stylo_score": round(stylo_score, 4),
            "label": label,
        }
    )


@app.route("/appeal", methods=["POST"])
def appeal():
    body = request.get_json(silent=True) or {}
    content_id = body.get("content_id", "")
    creator_reasoning = body.get("creator_reasoning", "")

    if not content_id:
        return jsonify({"error": "content_id is required"}), 400

    submission = get_submission(content_id)
    if submission is None:
        return jsonify({"error": "content_id not found"}), 404

    set_status_under_review(content_id)

    appeal_id = str(uuid.uuid4())
    appeal_timestamp = datetime.now(timezone.utc).isoformat()

    log_appeal(
        appeal_id=appeal_id,
        content_id=content_id,
        creator_reasoning=creator_reasoning,
        appeal_timestamp=appeal_timestamp,
        original_confidence=submission["confidence"],
        original_attribution=submission["attribution"],
    )

    return jsonify(
        {
            "status": "under_review",
            "content_id": content_id,
            "message": "Your appeal has been received and will be reviewed.",
        }
    )


@app.route("/log", methods=["GET"])
def log():
    return jsonify(get_recent_logs())


if __name__ == "__main__":
    app.run(debug=True)
