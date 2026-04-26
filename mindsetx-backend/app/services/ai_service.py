import json
import logging
from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas.journal import ReframeResponse

logger = logging.getLogger(__name__)
settings = get_settings()

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# CBT distortion labels the model should pick from
DISTORTION_TYPES = [
    "Overgeneralization",
    "Catastrophizing",
    "Mind Reading",
    "All-or-Nothing Thinking",
    "Emotional Reasoning",
    "Self-Blame",
    "Filtering",
    "Jumping to Conclusions",
    "Should Statements",
    "Labeling",
]

SYSTEM_PROMPT = f"""You are a professional cognitive behavioral therapy (CBT) assistant.
Your job is to analyze a user's thought, identify the cognitive distortion it contains,
and provide a psychologically accurate, practical reframing.

IMPORTANT RULES:
- Be specific and grounded — never give generic motivational quotes.
- Keep the reframe empathetic but realistic.
- The action must be concrete and achievable within the same day.
- Always return ONLY valid JSON with these exact keys: "pattern", "reframe", "action".
- "pattern" must be one of: {', '.join(DISTORTION_TYPES)}.

Example:
Input: "I always fail in everything I try."
Output:
{{
  "pattern": "Overgeneralization",
  "reframe": "You've had setbacks in specific situations, but that doesn't define your overall ability. Failures are data points, not permanent labels.",
  "action": "Write down one small thing you completed successfully today, no matter how minor."
}}"""


async def reframe_thought(thought_content: str) -> ReframeResponse:
    """
    Sends the user's thought to OpenAI and returns structured CBT output.
    Raises ValueError on malformed AI response.
    """
    # SECURITY: We pass the content without logging it
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": thought_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,  # Lower temp = more consistent, less hallucination
            max_tokens=512,
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        # Validate presence of required keys
        if not all(k in data for k in ("pattern", "reframe", "action")):
            raise ValueError("AI returned incomplete JSON structure.")

        return ReframeResponse(
            pattern=data["pattern"],
            reframe=data["reframe"],
            action=data["action"],
        )

    except json.JSONDecodeError as e:
        logger.error("AI returned non-JSON response.")  # Don't log content
        raise ValueError("AI service returned an unexpected format.") from e
    except Exception as e:
        logger.error(f"OpenAI API error: {type(e).__name__}")
        raise
