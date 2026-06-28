def compute_confidence(llm_score: float, stylo_score: float) -> float:
    return (0.65 * llm_score) + (0.35 * stylo_score)


def get_attribution(confidence: float) -> str:
    if confidence > 0.75:
        return "likely_ai"
    if confidence >= 0.45:
        return "uncertain"
    return "likely_human"


def generate_label(confidence: float) -> str:
    if confidence > 0.75:
        score = round(confidence * 100)
        return (
            f"⚠️ Likely AI-Generated\n"
            f"Our system's analysis suggests this content was likely produced with AI assistance "
            f"(confidence: {score}%). This label reflects a best estimate — not a certainty. "
            f"If you are the creator and believe this is incorrect, you can submit an appeal."
        )
    if confidence >= 0.45:
        score = round(confidence * 100)
        return (
            f"🔍 Attribution Uncertain\n"
            f"Our system was unable to determine with confidence whether this content is "
            f"human-written or AI-generated (confidence: {score}%). We're showing this label "
            f"to be transparent about that uncertainty. If you are the creator, you can submit "
            f"an appeal to provide more context."
        )
    score = round((1 - confidence) * 100)
    return (
        f"✅ Likely Human-Written\n"
        f"Our system's analysis suggests this content was likely written by a person "
        f"(confidence: {score}% human). No action is needed."
    )
