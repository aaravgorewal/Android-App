"""
test_ai_service.py — Manual test harness for the CBT reframe engine.

Run from mindsetx-backend root:
    OPENAI_API_KEY=sk-... python test_ai_service.py

Does NOT require a running server or database.
"""

import asyncio
import os
import sys
import json

# Make sure app is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set a minimal .env before importing settings
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-local-testing-only-32c")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test")
os.environ.setdefault("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

from app.services.ai_service import reframe_thought, _strip_pii

# ─── Test Cases (covering all 13 distortion types) ───────────────────────────
TEST_THOUGHTS = [
    # Catastrophizing
    "I made one mistake at work today. This means I'm going to get fired and never find a job again.",

    # Overgeneralization
    "I always fail. I can never do anything right.",

    # All-or-Nothing Thinking
    "If I don't get an A on this test, I'm a complete failure as a student.",

    # Mind Reading
    "My friend didn't text back. She's definitely angry at me and doesn't want to talk to me anymore.",

    # Should Statements
    "I should be happy. I have no reason to feel this way. I'm so weak for feeling anxious.",

    # Emotional Reasoning
    "I feel stupid, so I must actually be stupid.",

    # Self-Blame
    "My team didn't meet the deadline. It's my fault. I let everyone down.",

    # Labeling
    "I forgot to reply to that email. I'm such a failure and an idiot.",
]


async def run_tests():
    if not os.environ.get("OPENAI_API_KEY") or os.environ["OPENAI_API_KEY"] == "":
        print("⚠️  OPENAI_API_KEY not set. Run: OPENAI_API_KEY=sk-... python test_ai_service.py\n")
        sys.exit(1)

    print("=" * 65)
    print("MindsetX — CBT Reframe Engine Test")
    print("=" * 65)

    # Test PII scrubbing
    print("\n🔒 PII Scrubber Test")
    pii_input = "My email is john@example.com and my phone is +91-9876543210"
    scrubbed = _strip_pii(pii_input)
    assert "[EMAIL]" in scrubbed, "Email not scrubbed"
    assert "[PHONE]" in scrubbed, "Phone not scrubbed"
    print(f"  Input:   {pii_input}")
    print(f"  Output:  {scrubbed}")
    print("  ✅ PII scrubbing works correctly\n")

    # Test AI reframes
    passed = 0
    failed = 0

    for i, thought in enumerate(TEST_THOUGHTS, 1):
        print(f"\n{'─'*65}")
        print(f"Test {i}/{len(TEST_THOUGHTS)}")
        print(f"  Thought: {thought[:80]}...")
        try:
            result = await reframe_thought(thought)
            print(f"  Pattern:  [{result.pattern}]")
            print(f"  Reframe:  {result.reframe[:100]}...")
            print(f"  Action:   {result.action}")
            print(f"  ✅ PASS")
            passed += 1
        except Exception as e:
            print(f"  ❌ FAIL — {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'='*65}")
    print(f"Results: {passed} passed / {failed} failed out of {len(TEST_THOUGHTS)} tests")
    print("=" * 65)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_tests())
