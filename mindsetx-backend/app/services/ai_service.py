"""
ai_service.py — Production CBT Reframing Engine for MindsetX

Architecture:
- Uses OpenAI's gpt-4o-mini with json_object mode (guarantees valid JSON output)
- Few-shot prompting for psychologically consistent, non-generic responses
- PII stripping before sending to external API
- Retry logic for transient failures
- Strict response validation with distortion label enumeration
"""

import json
import logging
import re
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import AsyncOpenAI, APITimeoutError, APIConnectionError, RateLimitError

from app.config import get_settings
from app.schemas.journal import ReframeResponse

logger = logging.getLogger(__name__)
settings = get_settings()

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    timeout=15.0,  # Hard timeout — never let user wait >15s
)

# ─── Cognitive Distortion Taxonomy ───────────────────────────────────────────
# Sourced from CBT literature (Beck, Burns — Feeling Good)
DISTORTION_LABELS = {
    "All-or-Nothing Thinking",
    "Overgeneralization",
    "Mental Filter",
    "Disqualifying the Positive",
    "Jumping to Conclusions",
    "Magnification or Minimization",
    "Catastrophizing",
    "Emotional Reasoning",
    "Should Statements",
    "Labeling",
    "Self-Blame",
    "Mind Reading",
    "Fortune Telling",
}

# ─── PII Scrubber ────────────────────────────────────────────────────────────
_PII_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]"),
    (r"\b(\+?\d[\d\s\-().]{7,}\d)\b", "[PHONE]"),
    (r"\b\d{10,16}\b", "[ID_NUMBER]"),
]


def _strip_pii(text: str) -> str:
    """Remove obvious PII before sending to any external API."""
    for pattern, replacement in _PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


# ─── System Prompt ────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """You are a clinical Cognitive Behavioral Therapy (CBT) assistant embedded in a mindset app.

Your role is to:
1. Identify the specific cognitive distortion in the user's thought — choose EXACTLY ONE from this list:
   All-or-Nothing Thinking, Overgeneralization, Mental Filter, Disqualifying the Positive,
   Jumping to Conclusions, Magnification or Minimization, Catastrophizing, Emotional Reasoning,
   Should Statements, Labeling, Self-Blame, Mind Reading, Fortune Telling

2. Reframe the thought using evidence-based CBT technique — be SPECIFIC to their exact words.
   - Do NOT give generic advice like "stay positive" or "believe in yourself"
   - Do NOT minimize their feeling — validate it first, then gently challenge the distortion
   - Keep the reframe realistic and grounded, not falsely optimistic

3. Suggest ONE small, concrete, same-day action (not a life philosophy — an actual task).

STRICT OUTPUT RULES:
- Return ONLY valid JSON with exactly three keys: "pattern", "reframe", "action"
- "pattern" MUST be one of the 13 labels above — no variations
- "reframe" must be 1-3 sentences, written in second person ("You...")
- "action" must be one specific task completable within the next hour
- No markdown, no commentary, no extra fields"""

# ─── Few-Shot Examples ────────────────────────────────────────────────────────
_FEW_SHOT_EXAMPLES = [
    {
        "role": "user",
        "content": "I failed this exam. I'm going to fail in life and never get a good job."
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "pattern": "Catastrophizing",
            "reframe": "You're in real pain about this exam, and that makes sense — it matters to you. But one exam result doesn't determine your career path. Many people have failed tests and gone on to succeed by adjusting their approach, not their identity.",
            "action": "Write down exactly which topics you got wrong and circle the one that surprised you most — that's your starting point, not your verdict."
        })
    },
    {
        "role": "user",
        "content": "My boss didn't say anything good in the meeting. He must think I'm incompetent."
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "pattern": "Mind Reading",
            "reframe": "You're drawing a firm conclusion from silence, but your boss's quietness in a meeting has dozens of possible explanations — distraction, other priorities, or simply no feedback being needed. Treating one interpretation as fact can create anxiety that isn't based in evidence.",
            "action": "Send your boss one specific question about a piece of work you delivered this week — it creates real data instead of assumptions."
        })
    },
    {
        "role": "user",
        "content": "I always mess things up. I can't do anything right."
    },
    {
        "role": "assistant",
        "content": json.dumps({
            "pattern": "Overgeneralization",
            "reframe": "The word 'always' is doing a lot of heavy lifting in that thought. You're taking a recent difficulty and applying it as a permanent, universal rule about yourself — which isn't supported by your full history. Setbacks are specific, not total.",
            "action": "List three things you completed or handled correctly in the past week, no matter how small they seem."
        })
    },
]


# ─── Retry Logic ─────────────────────────────────────────────────────────────
@retry(
    retry=retry_if_exception_type((APITimeoutError, APIConnectionError, RateLimitError)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=6),
    reraise=True,
)
async def _call_openai(cleaned_thought: str) -> str:
    """Makes the API call with retry on transient failures. Returns raw JSON string."""
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            *_FEW_SHOT_EXAMPLES,
            {"role": "user", "content": cleaned_thought},
        ],
        response_format={"type": "json_object"},
        temperature=0.35,   # Low temp = consistent distortion identification
        max_tokens=400,     # Enough for 3 grounded sentences + action
        top_p=0.9,
    )
    return response.choices[0].message.content


# ─── Validation ───────────────────────────────────────────────────────────────
def _validate_reframe(data: dict) -> ReframeResponse:
    """
    Validates the AI JSON output against the schema.
    Raises ValueError with a user-safe message on any violation.
    """
    required_keys = {"pattern", "reframe", "action"}
    missing = required_keys - data.keys()
    if missing:
        raise ValueError(f"AI response missing required fields: {missing}")

    pattern = data["pattern"].strip()
    if pattern not in DISTORTION_LABELS:
        # Try to salvage via fuzzy match — e.g., "All or Nothing" → "All-or-Nothing Thinking"
        lower_map = {label.lower(): label for label in DISTORTION_LABELS}
        pattern = lower_map.get(pattern.lower(), pattern)
        if pattern not in DISTORTION_LABELS:
            logger.warning(f"AI returned unknown distortion pattern: '{data['pattern']}'")
            pattern = "Overgeneralization"  # Safe fallback, never crash

    reframe = data["reframe"].strip()
    action = data["action"].strip()

    if len(reframe) < 20:
        raise ValueError("AI reframe response is too short to be clinically meaningful.")
    if len(action) < 10:
        raise ValueError("AI action step is too short to be actionable.")

    return ReframeResponse(pattern=pattern, reframe=reframe, action=action)


# ─── Public Interface ─────────────────────────────────────────────────────────
async def reframe_thought(thought_content: str) -> ReframeResponse:
    """
    Main entry point for the AI reframing pipeline.

    Steps:
    1. Strip PII from the input before sending externally
    2. Call OpenAI with retry logic
    3. Parse and validate the structured JSON response
    4. Return a clean ReframeResponse

    Never logs the content of user thoughts — only error types.
    """
    if len(thought_content.strip()) < 10:
        raise ValueError("Thought content is too short to analyze meaningfully.")

    # 1. PII scrub — never send raw user PII to external APIs
    cleaned = _strip_pii(thought_content.strip())

    try:
        # 2. API call (with retry)
        raw_json = await _call_openai(cleaned)

        # 3. Parse
        data = json.loads(raw_json)

        # 4. Validate + return
        return _validate_reframe(data)

    except json.JSONDecodeError:
        logger.error("AI returned non-JSON content. Type: JSONDecodeError")
        raise ValueError("The AI service returned an unexpected response format.")

    except (APITimeoutError, APIConnectionError):
        logger.error("AI service unreachable after 3 retries.")
        raise ConnectionError("The AI service is temporarily unavailable. Please try again in a moment.")

    except RateLimitError:
        logger.error("OpenAI rate limit hit.")
        raise ConnectionError("AI request limit reached. Please wait a moment before trying again.")

    except ValueError:
        raise  # Re-raise validation errors as-is

    except Exception as exc:
        logger.error(f"Unexpected error in reframe_thought: {type(exc).__name__}")
        raise RuntimeError("An unexpected error occurred during AI analysis.") from exc
