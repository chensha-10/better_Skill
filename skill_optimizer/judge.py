import difflib
import json
import re
from dataclasses import dataclass

from skill_optimizer.files import FileCheckResult


@dataclass(frozen=True)
class JudgeResult:
    score: float
    reason: str


def _extract_json_from_output(output: str) -> str:
    # Prefer markdown code fence with explicit json tag
    m = re.search(r'```json\s*(\{.*?\})\s*```', output, re.DOTALL)
    if m:
        return m.group(1)
    # Fall back: any {...} containing "score"
    m = re.search(r'\{[^{}]*"score"\s*:\s*[0-9.]+[^{}]*\}', output, re.DOTALL)
    if m:
        return m.group(0)
    raise ValueError(f"No JSON object with 'score' found in output: {output[:200]}")


def parse_judge_output(output: str) -> JudgeResult:
    json_text = _extract_json_from_output(output)
    data = json.loads(json_text)
    score = float(data["score"])
    if score < 0 or score > 1:
        raise ValueError(f"Judge score must be between 0 and 1: {score}")
    reason = str(data.get("reason", ""))
    return JudgeResult(score=score, reason=reason)


def judge_text_simple(actual: str, expected: str) -> JudgeResult | None:
    """Use difflib similarity for short expected texts. Returns None if too long."""
    if len(expected) >= 100:
        return None
    ratio = difflib.SequenceMatcher(None, actual.strip(), expected.strip()).ratio()
    return JudgeResult(score=ratio, reason=f"Text similarity: {ratio:.2f}")


def build_judge_prompt(actual: str, expected: str) -> str:
    return (
        "You are an automated evaluator. Compare the actual answer with the expected answer "
        "using these objective criteria:\n"
        "1. Factual correctness: does the answer contain the key facts from expected? (0-0.5)\n"
        "2. No contradiction: does the answer contradict anything in expected? (0-0.3)\n"
        "3. No hallucination: does the answer add false claims beyond expected? (0-0.2)\n"
        "Return ONLY valid JSON with keys score and reason. "
        "score must be between 0 and 1.\n\n"
        "<expected>\n"
        f"{expected}\n"
        "</expected>\n\n"
        "<actual>\n"
        f"{actual}\n"
        "</actual>\n"
    )


def combine_scores(
    text_score: float | None,
    file_result: FileCheckResult | None,
    min_score: float,
) -> tuple[float, bool]:
    # File check: if it exists and fails, immediate failure
    if file_result is not None and not file_result.passed:
        return 0.0, False
    # No text score → pure files case (already passed above)
    if text_score is None:
        return 1.0, True
    # Text score present → must meet threshold
    return text_score, text_score >= min_score
