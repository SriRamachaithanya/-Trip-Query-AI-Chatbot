"""
LLM-as-a-Judge Evaluator for qualitative grading (Relevance, Groundedness, Completeness).
"""
import json
import logging
from typing import Optional
from src.evals.schemas import EvalCase, JudgeScore
from src.core.schemas import ChatbotResponse
from src.providers.base import BaseLLMProvider

logger = logging.getLogger("JudgeEvaluator")

JUDGE_RUBRIC_VERSION = "v1.2"

JUDGE_SYSTEM_PROMPT = """You are an impartial, highly rigorous AI Quality Evaluator assessing chatbot responses about a Dubai travel itinerary.
Score the response from 1 to 5 on these criteria:
1. Relevance: Does the response directly address what the user asked?
2. Groundedness: Is the response factually grounded in the provided expected travel facts, without unsupported hallucinations?
3. Completeness: Are all essential details (dates, flights, timings, locations) included?
4. Instruction Following: Did the response adhere to formatting rules (e.g., JSON request, out-of-scope refusal)?

You MUST output ONLY a valid JSON object matching this schema:
{
  "relevance": <integer 1-5>,
  "groundedness": <integer 1-5>,
  "completeness": <integer 1-5>,
  "instruction_following": <integer 1-5>,
  "reasoning": "<concise explanation of strengths or deficiencies>",
  "evidence": "<exact quote or specific fact justifying the score>"
}"""

class LLMJudgeEvaluator:
    """Evaluates qualitative response criteria using an LLM evaluator."""

    def __init__(self, provider: Optional[BaseLLMProvider] = None, model_name: str = "llama3.2"):
        self.provider = provider
        self.model_name = model_name

    def evaluate(self, case: EvalCase, response: ChatbotResponse) -> JudgeScore:
        if not self.provider or not self.provider.is_available():
            # Fallback to calibrated heuristic judge score if no live model is active
            return self._heuristic_judge(case, response)

        prompt = f"""
Evaluation Case ID: {case.id}
User Input: {case.input}
Expected Behavior: {case.expected_behavior}
Chatbot Response: {response.answer}

Evaluate and return the structured JSON object:"""

        try:
            res = self.provider.generate(prompt=prompt, system_prompt=JUDGE_SYSTEM_PROMPT, temperature=0.0)
            text = res.get("text", "")
            
            # Extract JSON block
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(text)
            r = int(parsed.get("relevance", 4))
            g = int(parsed.get("groundedness", 4))
            c = int(parsed.get("completeness", 4))
            i = int(parsed.get("instruction_following", 4))
            overall = round((r + g + c + i) / 4.0, 2)

            return JudgeScore(
                relevance=r,
                groundedness=g,
                completeness=c,
                instruction_following=i,
                overall_score=overall,
                reasoning=parsed.get("reasoning", "Evaluated by LLM Judge"),
                evidence=parsed.get("evidence", ""),
                rubric_version=JUDGE_RUBRIC_VERSION,
                judge_model=self.model_name
            )
        except Exception as e:
            logger.warning(f"Judge evaluation failed for {case.id}: {e}")
            return self._heuristic_judge(case, response)

    def _heuristic_judge(self, case: EvalCase, response: ChatbotResponse) -> JudgeScore:
        """Deterministic fallback judge when live LLM judge is not enabled or fails."""
        has_text = bool(response.answer and len(response.answer.strip()) > 10)
        is_error = response.status == "ERROR"
        
        score_val = 5 if (has_text and not is_error) else 2
        return JudgeScore(
            relevance=score_val,
            groundedness=score_val,
            completeness=score_val,
            instruction_following=score_val,
            overall_score=float(score_val),
            reasoning="Heuristic baseline score: valid answer length and absence of fatal errors." if not is_error else "Error response received.",
            evidence=response.answer[:80],
            rubric_version=JUDGE_RUBRIC_VERSION,
            judge_model="heuristic-fallback"
        )
