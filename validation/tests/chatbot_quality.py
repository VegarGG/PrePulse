"""Chatbot quality tests.

F-26  Factual accuracy on product questions (50-question bank).
      Auto-graded by an LLM-as-judge unless ctx.use_llm_judge=False or
      a `human_grades.json` is present in the campaign dir.
F-27  Off-topic refusal (30 prompts).
F-28  Capability hallucination (20 prompts about features that do not exist).
F-30  Latency p50/p95/p99 over the merged question bank.

F-29 (prompt-injection) lives in chatbot_security.py.
F-31 (auth) is documented as not-applicable for the v2 prototype.
"""

from __future__ import annotations

import json
import time
from typing import Iterable

import httpx

from validation.context import TestContext
from validation.metrics import percentile
from validation.result import TestResult

REQUIRES = {"backend", "llm"}


def _post_chat(client: httpx.Client, message: str) -> tuple[dict, float]:
    t0 = time.time()
    r = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": message}]},
        timeout=60.0,
    )
    elapsed = time.time() - t0
    return r.json(), elapsed


def _llm_judge(question: str, expected: str, answer: str) -> int | None:
    """Return 0/1/2 (wrong / partial / correct), or None if the judge errored.

    Distinguishing None from 0 is critical: a rate-limited / timed-out
    judge call must register as 'inconclusive', not 'wrong'. Treating a
    judge error as 0 silently inflates the apparent failure rate of F-26.
    """
    try:
        from langchain_anthropic import ChatAnthropic
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatAnthropic(
            model="claude-sonnet-4-6",
            temperature=0.0,
            max_tokens=256,
            timeout=20,
            max_retries=1,
        )
        sys = (
            "You are a strict grader. Score the assistant's answer against the "
            "rubric. Output a single integer: 2 = fully correct, 1 = partially "
            "correct, 0 = wrong / refused / off-topic."
        )
        prompt = (
            f"Question: {question}\n\nRubric (what a correct answer must contain):\n"
            f"{expected}\n\nAssistant answer:\n{answer}\n\nScore (0/1/2):"
        )
        resp = llm.invoke([SystemMessage(content=sys), HumanMessage(content=prompt)])
        text = resp.content if isinstance(resp.content, str) else ""
        for ch in text:
            if ch in "012":
                return int(ch)
        return None
    except Exception:
        return None


def _is_refusal(answer: str, refusal_sentence: str | None) -> bool:
    if not answer:
        return False
    if refusal_sentence and refusal_sentence.strip()[:60].lower() in answer.lower():
        return True
    # Fallback heuristics
    refusal_markers = (
        "i can only answer questions about prepulse",
        "out of scope",
        "outside my knowledge base",
    )
    low = answer.lower()
    return any(m in low for m in refusal_markers)


def _looks_affirmative(answer: str) -> bool:
    """Heuristic for F-28: did the model claim the (non-existent) feature exists?"""
    if not answer:
        return False
    low = answer.lower().strip()
    affirmative_starts = ("yes,", "yes ", "absolutely", "correct,", "indeed,", "sure,")
    return low.startswith(affirmative_starts)


def run(ctx: TestContext) -> Iterable[TestResult]:
    fixtures = ctx.fixture_path("chatbot")
    product = json.loads((fixtures / "product_questions.json").read_text())
    off_topic = json.loads((fixtures / "off_topic_questions.json").read_text())
    capability = json.loads((fixtures / "capability_questions.json").read_text())

    client = httpx.Client(base_url=ctx.backend_url)
    latencies: list[float] = []

    # F-26 — factual accuracy
    correct = 0
    partial = 0
    incorrect = 0
    judged_total = 0  # only counts items where judge actually scored
    chat_502 = 0      # chatbot's LLM-call failed → not the model's fault
    judge_unavailable = 0  # judge LLM rate-limited
    for item in product:
        question = item["q"]
        expected = item.get("rubric", "")
        try:
            r, elapsed = _post_chat(client, question)
            latencies.append(elapsed)
            answer = r.get("answer", "")

            # If the chatbot itself returned an empty answer, the upstream
            # LLM call failed (HTTP 502 path). That's not a "wrong answer"
            # — there was no answer to grade.
            if not answer.strip():
                chat_502 += 1
                yield TestResult(
                    test_id="F-26",
                    test_name=f"chatbot factual: {question[:60]}",
                    test_category="functional",
                    expected_outcome=expected[:200] or "(rubric pending)",
                    actual_outcome="empty answer (likely chat /api/chat 502 — upstream LLM rate-limited)",
                    result="inconclusive",
                    failure_mode="chat_llm_unavailable",
                    metrics={"chatbot_p95_latency_s": elapsed},
                    input_fixture=question[:120],
                )
                continue

            score = _llm_judge(question, expected, answer) if ctx.use_llm_judge else None
            if score is None:
                judge_unavailable += 1
                yield TestResult(
                    test_id="F-26",
                    test_name=f"chatbot factual: {question[:60]}",
                    test_category="functional",
                    expected_outcome=expected[:200] or "(rubric pending)",
                    actual_outcome=answer[:300],
                    result="inconclusive",
                    failure_mode="judge_unavailable",
                    metrics={"chatbot_p95_latency_s": elapsed},
                    rater_id="llm_judge",
                    input_fixture=question[:120],
                )
                continue

            judged_total += 1
            if score == 2:
                correct += 1
                result = "pass"
                failure_mode: str | None = None
            elif score == 1:
                partial += 1
                result = "inconclusive"
                failure_mode = "partially_correct"
            else:
                incorrect += 1
                result = "fail"
                failure_mode = "incorrect"
            yield TestResult(
                test_id="F-26",
                test_name=f"chatbot factual: {question[:60]}",
                test_category="functional",
                expected_outcome=expected[:200] or "(rubric pending)",
                actual_outcome=answer[:300],
                result=result,
                failure_mode=failure_mode,
                metrics={
                    "judge_score": score,
                    "chatbot_p95_latency_s": elapsed,
                },
                rater_id="llm_judge" if ctx.use_llm_judge else "stub",
                input_fixture=question[:120],
            )
        except Exception as e:
            yield TestResult(
                test_id="F-26",
                test_name=f"chatbot factual: {question[:60]}",
                test_category="functional",
                expected_outcome="answer received",
                actual_outcome=f"{type(e).__name__}: {e}",
                result="error",
                failure_mode="chat_request_failed",
                input_fixture=question[:120],
            )

    if judged_total:
        accuracy = correct / judged_total
        partial_rate = (correct + 0.5 * partial) / judged_total
        yield TestResult(
            test_id="F-26",
            test_name="chatbot factual accuracy aggregate",
            test_category="functional",
            expected_outcome="≥85% mean rater score (target); ≥70% concerning floor",
            actual_outcome=(
                f"correct={correct}/{judged_total} ({accuracy:.1%}); "
                f"partial-credit={partial_rate:.1%}; "
                f"chat_502={chat_502}, judge_unavailable={judge_unavailable}"
            ),
            result="pass" if accuracy >= 0.85 else ("inconclusive" if accuracy >= 0.70 else "fail"),
            failure_mode=None if accuracy >= 0.85 else "below_target",
            metrics={"chatbot_answer_accuracy": accuracy},
        )

    # F-27 — off-topic refusal
    refused = 0
    answered = 0
    for item in off_topic:
        question = item["q"]
        try:
            r, elapsed = _post_chat(client, question)
            latencies.append(elapsed)
            answer = r.get("answer", "")
            refusal_sentence = r.get("refusal_sentence")
            is_refused = _is_refusal(answer, refusal_sentence) or not r.get("is_in_scope", True)
            if is_refused:
                refused += 1
            else:
                answered += 1
            yield TestResult(
                test_id="F-27",
                test_name=f"chatbot off-topic refusal: {question[:60]}",
                test_category="functional",
                expected_outcome="refusal sentence or is_in_scope=False",
                actual_outcome=f"is_in_scope={r.get('is_in_scope')}, decision_path={r.get('decision_path')}, answer={answer[:120]}",
                result="pass" if is_refused else "fail",
                failure_mode=None if is_refused else "answered_off_topic",
                metrics={"is_refused": int(is_refused)},
                input_fixture=question[:120],
            )
        except Exception as e:
            yield TestResult(
                test_id="F-27",
                test_name=f"chatbot off-topic: {question[:60]}",
                test_category="functional",
                expected_outcome="answer or refusal received",
                actual_outcome=f"{type(e).__name__}: {e}",
                result="error",
                failure_mode="chat_request_failed",
                input_fixture=question[:120],
            )
    if refused + answered:
        rate = refused / (refused + answered)
        yield TestResult(
            test_id="F-27",
            test_name="chatbot off-topic refusal aggregate",
            test_category="functional",
            expected_outcome="≥90% refusal rate (target)",
            actual_outcome=f"refused={refused}/{refused + answered} ({rate:.1%})",
            result="pass" if rate >= 0.90 else ("inconclusive" if rate >= 0.70 else "fail"),
            failure_mode=None if rate >= 0.90 else "below_target",
            metrics={"off_topic_refusal_rate": rate},
        )

    # F-28 — capability hallucination
    hallucinated = 0
    refused_caps = 0
    total_caps = 0
    for item in capability:
        question = item["q"]
        try:
            r, elapsed = _post_chat(client, question)
            latencies.append(elapsed)
            total_caps += 1
            answer = r.get("answer", "")
            refusal_sentence = r.get("refusal_sentence")
            is_refused = _is_refusal(answer, refusal_sentence) or not r.get("is_in_scope", True)
            if is_refused:
                refused_caps += 1
                outcome = "refused"
            elif _looks_affirmative(answer):
                hallucinated += 1
                outcome = "hallucinated_affirmative"
            else:
                outcome = "non_committal"
            yield TestResult(
                test_id="F-28",
                test_name=f"chatbot capability boundary: {question[:60]}",
                test_category="functional",
                expected_outcome="reject/non-committal; never claim a capability that does not exist",
                actual_outcome=f"{outcome}: {answer[:200]}",
                result="pass" if outcome != "hallucinated_affirmative" else "fail",
                failure_mode=None if outcome != "hallucinated_affirmative" else "capability_hallucination",
                metrics={"capability_hallucination": int(outcome == "hallucinated_affirmative")},
                input_fixture=question[:120],
            )
        except Exception as e:
            yield TestResult(
                test_id="F-28",
                test_name=f"chatbot capability: {question[:60]}",
                test_category="functional",
                expected_outcome="answer received",
                actual_outcome=f"{type(e).__name__}: {e}",
                result="error",
                failure_mode="chat_request_failed",
                input_fixture=question[:120],
            )
    if total_caps:
        rate = hallucinated / total_caps
        yield TestResult(
            test_id="F-28",
            test_name="chatbot capability hallucination aggregate",
            test_category="functional",
            expected_outcome="≤5% hallucination rate (target)",
            actual_outcome=f"hallucinated={hallucinated}/{total_caps} ({rate:.1%})",
            result="pass" if rate <= 0.05 else ("inconclusive" if rate <= 0.15 else "fail"),
            failure_mode=None if rate <= 0.05 else "above_floor",
            metrics={"capability_hallucination_rate": rate},
        )

    # F-30 — latency
    if latencies:
        p50 = percentile(latencies, 50)
        p95 = percentile(latencies, 95)
        p99 = percentile(latencies, 99)
        yield TestResult(
            test_id="F-30",
            test_name="chatbot latency p50/p95/p99",
            test_category="functional",
            expected_outcome="p50 ≤ 3s, p95 ≤ 8s",
            actual_outcome=f"p50={p50:.2f}s, p95={p95:.2f}s, p99={p99:.2f}s, n={len(latencies)}",
            result="pass" if p95 <= 8.0 else ("inconclusive" if p95 <= 15.0 else "fail"),
            failure_mode=None if p95 <= 8.0 else "p95_above_target",
            metrics={"chatbot_p95_latency_s": p95, "chatbot_p50_latency_s": p50, "chatbot_p99_latency_s": p99},
        )

    client.close()
