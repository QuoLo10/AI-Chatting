"""
Comprehensive Empirical Stress Test Harness for determine_response_length().
Executed by Challenger 1 (Milestone M2).
"""

import sys
import os
import time
import traceback
from typing import List, Dict, Any, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from langchain_core.messages import HumanMessage, AIMessage

from src.core.length_controller import (
    LengthTier,
    LengthDecision,
    determine_response_length,
    RE_EMOTIONAL_CONFESSION,
    TIER_TOKEN_LIMITS,
    TIER_WORD_BOUNDS,
)


class TestResult:
    def __init__(self, name: str, passed: bool, details: str, severity: str = "INFO"):
        self.name = name
        self.passed = passed
        self.details = details
        self.severity = severity  # INFO, LOW, MEDIUM, HIGH, CRITICAL


results: List[TestResult] = []


def record(name: str, passed: bool, details: str, severity: str = "INFO"):
    res = TestResult(name, passed, details, severity)
    results.append(res)
    status = "PASS" if passed else f"FAIL [{severity}]"
    print(f"[{status}] {name}: {details}")


# ==============================================================================
# 1. EXTREME LENGTHS STRESS TESTS
# ==============================================================================
print("\n--- Running Suite 1: Extreme Lengths Stress Tests ---")

# 1.1 Zero words & whitespace
try:
    d_empty = determine_response_length("")
    record("1.1 Empty string returns SHORT", d_empty.tier == LengthTier.SHORT and d_empty.max_tokens == 35, f"tier={d_empty.tier}, max_tokens={d_empty.max_tokens}")
except Exception as e:
    record("1.1 Empty string returns SHORT", False, f"Exception: {e}", "CRITICAL")

try:
    whitespace_inputs = ["   ", "\t\t\n\r\n", "   " * 1000]
    all_short = all(determine_response_length(w).tier == LengthTier.SHORT for w in whitespace_inputs)
    record("1.2 Whitespace inputs return SHORT", all_short, f"Tested {len(whitespace_inputs)} whitespace variations")
except Exception as e:
    record("1.2 Whitespace inputs return SHORT", False, f"Exception: {e}", "CRITICAL")

# 1.3 Exact word count boundaries
try:
    w4 = "một hai ba bốn"
    w5 = "một hai ba bốn năm"
    w15 = " ".join([f"từ_{i}" for i in range(15)])
    w25 = " ".join([f"từ_{i}" for i in range(25)])
    w26 = " ".join([f"từ_{i}" for i in range(26)])

    d4 = determine_response_length(w4)
    d5 = determine_response_length(w5)
    d15 = determine_response_length(w15)
    d25 = determine_response_length(w25)
    d26 = determine_response_length(w26)

    record("1.3.1 Boundary 4 words -> SHORT", d4.tier == LengthTier.SHORT, f"tier={d4.tier}")
    # Note: 5 words boundary check against specification
    # Specification says: SHORT: 1-5 words, MEDIUM: 6-15 words
    # Implementation checks: if word_count <= 4: SHORT, else MEDIUM
    record(
        "1.3.2 Boundary 5 words aligns with SHORT (Spec says 1-5 words)",
        d5.tier == LengthTier.SHORT,
        f"tier={d5.tier} (Implementation classified 5 words as MEDIUM; spec defines SHORT as 1-5 words)",
        "MEDIUM"
    )
    record("1.3.3 Boundary 15 words -> MEDIUM", d15.tier == LengthTier.MEDIUM, f"tier={d15.tier}")
    record("1.3.4 Boundary 25 words -> MEDIUM", d25.tier == LengthTier.MEDIUM, f"tier={d25.tier}")
    record("1.3.5 Boundary 26 words -> LONG", d26.tier == LengthTier.LONG, f"tier={d26.tier}")
except Exception as e:
    record("1.3 Exact word count boundaries", False, f"Exception: {e}", "HIGH")

# 1.4 Massive text & Single token massive string
try:
    text_1k = "chúng ta đi học bài nhé bạn ơi " * 125  # 1000 words
    t0 = time.perf_counter()
    d_1k = determine_response_length(text_1k)
    t_1k = time.perf_counter() - t0
    record("1.4.1 1,000 words handled quickly", d_1k.tier == LengthTier.LONG and t_1k < 0.05, f"tier={d_1k.tier}, elapsed={t_1k*1000:.2f}ms")

    text_10k = "học bài đi nha " * 2500  # 10,000 words
    t0 = time.perf_counter()
    d_10k = determine_response_length(text_10k)
    t_10k = time.perf_counter() - t0
    record("1.4.2 10,000 words handled quickly", d_10k.tier == LengthTier.LONG and t_10k < 0.1, f"tier={d_10k.tier}, elapsed={t_10k*1000:.2f}ms")

    text_50k = "tập trung ôn thi đi " * 10000  # 50,000 words
    t0 = time.perf_counter()
    d_50k = determine_response_length(text_50k)
    t_50k = time.perf_counter() - t0
    record("1.4.3 50,000 words stress test", d_50k.tier == LengthTier.LONG and t_50k < 0.5, f"tier={d_50k.tier}, elapsed={t_50k*1000:.2f}ms")

    # Single giant token without whitespace (e.g. 50,000 chars)
    giant_token = "a" * 50000
    t0 = time.perf_counter()
    d_giant = determine_response_length(giant_token)
    t_giant = time.perf_counter() - t0
    record(
        "1.4.4 Single 50k-char token (no space) survives regex scan",
        d_giant.tier == LengthTier.SHORT and t_giant < 0.2,
        f"tier={d_giant.tier}, elapsed={t_giant*1000:.2f}ms"
    )

    # Catastrophic regex test
    cat_input = ("muốn " * 500) + "bên an"
    t0 = time.perf_counter()
    d_cat = determine_response_length(cat_input)
    t_cat = time.perf_counter() - t0
    record("1.4.5 Catastrophic pattern test", d_cat.tier == LengthTier.LONG and t_cat < 0.1, f"elapsed={t_cat*1000:.2f}ms")
except Exception as e:
    record("1.4 Massive text stress", False, f"Exception: {e}", "HIGH")


# ==============================================================================
# 2. REGEX SUBSTRING FALSE POSITIVES (OVERMATCHING CHALLENGE)
# ==============================================================================
print("\n--- Running Suite 2: Regex Substring False Positives ---")

# 2.1 The "ex" unanchored substring bug
ex_false_positives = [
    ("gửi text cho t", "4 words study request"),
    ("mở file excel nha", "4 words study request"),
    ("next bài đi bạn", "4 words casual banter"),
    ("export file pdf", "3 words study request"),
    ("bị exception rồi", "3 words code help"),
    ("hơi complex xíu", "3 words comment"),
    ("context bài này", "3 words study context"),
    ("flex nhẹ cái nha", "4 words casual banter"),
    ("relax xíu đi An", "4 words casual chat"),
    ("xem lại index", "3 words study request"),
]

ex_failures = []
for phrase, desc in ex_false_positives:
    decision = determine_response_length(phrase)
    # These phrases are <= 4 words, should be SHORT tier (max_tokens=35), NOT LONG emotional confession!
    if decision.tier == LengthTier.LONG:
        ex_failures.append((phrase, decision.tier, desc))

record(
    "2.1 Regex 'ex' unanchored substring does not hijack short tech/casual messages to LONG tier",
    len(ex_failures) == 0,
    f"{len(ex_failures)}/{len(ex_false_positives)} phrases misclassified as LONG: {ex_failures[:3]}",
    "CRITICAL"
)

# 2.2 The "thích m" unanchored prefix bug
thich_m_false_positives = [
    ("t thích mua cái này", "5 words casual chat"),
    ("mình thích màu hồng", "4 words casual chat"),
    ("thích môn này kh b", "5 words study question"),
    ("thích mang giày thể thao", "5 words casual preference"),
    ("mình thích mở nhạc", "4 words casual preference"),
]

thich_m_failures = []
for phrase, desc in thich_m_false_positives:
    decision = determine_response_length(phrase)
    if decision.tier == LengthTier.LONG:
        thich_m_failures.append((phrase, decision.tier, desc))

record(
    "2.2 Regex 'thích m' without word boundary does not hijack ordinary preferences to LONG tier",
    len(thich_m_failures) == 0,
    f"{len(thich_m_failures)}/{len(thich_m_false_positives)} preferences misclassified as LONG: {thich_m_failures[:3]}",
    "HIGH"
)

# 2.3 Other common non-confession phrases matching emotional keywords
phrase_false_positives = [
    ("khoảng cách bao xa b?", "4 words distance question"),
    ("bài thi không giới hạn thời gian", "6 words study info"),
    ("để mình nghĩ lại đã nha", "6 words casual decision"),
    ("thầy bảo mình với an làm chung", "7 words group study"),
    ("hôm nay đi bộ mệt mỏi ghê", "6 words physical fatigue"),
]

phrase_failures = []
for phrase, desc in phrase_false_positives:
    decision = determine_response_length(phrase)
    if decision.tier == LengthTier.LONG:
        phrase_failures.append((phrase, decision.tier, desc))

record(
    "2.3 Technical / physical terms (khoảng cách, giới hạn, nghĩ lại, mệt mỏi) not hijacked to LONG tier",
    len(phrase_failures) == 0,
    f"{len(phrase_failures)}/{len(phrase_false_positives)} phrases misclassified as LONG: {phrase_failures[:3]}",
    "HIGH"
)


# ==============================================================================
# 3. EMOJIS, NON-ALPHANUMERIC & AMBIGUOUS QUERIES
# ==============================================================================
print("\n--- Running Suite 3: Emojis, Non-Alphanumeric & Code Snippets ---")

# 3.1 Single and short emojis -> should be SHORT
try:
    emojis_short = ["😴", "🤡", "🤡🤡🤡", "❤️", "👍🏽", "👩‍👩‍👧‍👦", "🇻🇳"]
    all_emoji_short = all(determine_response_length(e).tier == LengthTier.SHORT for e in emojis_short)
    record("3.1 Single and dense emojis classify as SHORT", all_emoji_short, f"Tested {len(emojis_short)} emoji forms")
except Exception as e:
    record("3.1 Single and dense emojis classify as SHORT", False, f"Exception: {e}", "HIGH")

# 3.2 Repetitive space-separated emojis vs dense emojis (Asymmetry check)
try:
    dense_clowns = "🤡" * 30  # 30 clowns without spaces
    spaced_clowns = "🤡 " * 30  # 30 clowns with spaces

    d_dense = determine_response_length(dense_clowns)
    d_spaced = determine_response_length(spaced_clowns)

    # An An sending 20-50 words emotional boundary for 30 spaced clown emojis is irrational
    record(
        "3.2 Spaced emojis ('🤡 ' * 30) should classify as SHORT, not LONG emotional tier",
        d_spaced.tier == LengthTier.SHORT,
        f"dense tier={d_dense.tier}, spaced tier={d_spaced.tier} (max_tokens={d_spaced.max_tokens})",
        "HIGH"
    )
except Exception as e:
    record("3.2 Spaced emojis test", False, f"Exception: {e}", "MEDIUM")

# 3.3 Repetitive space-separated punctuation vs dense punctuation
try:
    dense_punct = "?" * 30
    spaced_punct = "? " * 30

    dp_dense = determine_response_length(dense_punct)
    dp_spaced = determine_response_length(spaced_punct)

    record(
        "3.3 Spaced punctuation ('? ' * 30) should classify as SHORT, not LONG emotional tier",
        dp_spaced.tier == LengthTier.SHORT,
        f"dense tier={dp_dense.tier}, spaced tier={dp_spaced.tier} (max_tokens={dp_spaced.max_tokens})",
        "HIGH"
    )
except Exception as e:
    record("3.3 Spaced punctuation test", False, f"Exception: {e}", "MEDIUM")

# 3.4 Code Snippets
code_samples = [
    ("import os\nprint('hello world')", LengthTier.SHORT, "3 tokens simple import"),
    ("SELECT * FROM users WHERE status = 'active';", LengthTier.MEDIUM, "8 words SQL query"),
    ("SELECT * FROM users WHERE context = 'main';", LengthTier.MEDIUM, "8 words SQL with 'context'"),
    ("try:\n    run()\nexcept Exception as ex:\n    pass", LengthTier.MEDIUM, "8 words Python try/except"),
]

code_failures = []
for code, expected, desc in code_samples:
    dec = determine_response_length(code)
    if dec.tier != expected:
        code_failures.append((code.replace('\n', ' '), dec.tier, expected, desc))

record(
    "3.4 Code snippets without emotional intent do not trigger LONG tier",
    len(code_failures) == 0,
    f"{len(code_failures)}/{len(code_samples)} code snippets misclassified: {code_failures}",
    "HIGH"
)

# 3.5 Foreign non-segmented languages (CJK text)
cjk_samples = [
    ("今天天气非常好，我们一起去学校图书馆看书复习准备明天的期末考试吧，你觉得怎么样？", "Chinese study invitation (43 chars, 1 space token)"),
    ("今日はとてもいい天気ですね。一緒にお昼ご飯を食べに行きませんか？", "Japanese lunch invitation (34 chars, 1 space token)"),
]

cjk_short_count = sum(1 for text, _ in cjk_samples if determine_response_length(text).tier == LengthTier.SHORT)
record(
    "3.5 Non-segmented CJK long paragraphs undercount words due to str.split()",
    cjk_short_count == 0,
    f"{cjk_short_count}/{len(cjk_samples)} long foreign paragraphs classified as SHORT (1 word)",
    "LOW"
)


# ==============================================================================
# 4. MULTI-TURN HISTORY & RAPID TOPIC CHANGE
# ==============================================================================
print("\n--- Running Suite 4: Multi-turn History & Rapid Topic Change ---")

# 4.1 Rapid topic change after genuine emotional turn
genuine_emotional_history = [
    HumanMessage(content="Thật sự muốn đc bên An"),
    AIMessage(content="Muốn đồng ý lắm nhưng mà tiếc là không được..."),
    HumanMessage(content="ok b"),
    AIMessage(content="=)))"),
]

# Next turn is a completely casual study question
casual_question = "mai đi học ca mấy thế b?"
d_casual_after_emotion = determine_response_length(casual_question, conversation_history=genuine_emotional_history)
record(
    "4.1 Rapid topic shift: casual study question after resolved emotional turn reverts from LONG to MEDIUM/SHORT",
    d_casual_after_emotion.tier in (LengthTier.SHORT, LengthTier.MEDIUM),
    f"Classified as {d_casual_after_emotion.tier} (tokens={d_casual_after_emotion.max_tokens})",
    "HIGH"
)

# 4.2 History contamination from false-positive keyword (e.g. 'text' or 'excel')
contaminated_history = [
    HumanMessage(content="gửi text bài tập cho t"),  # Matched 'ex' false positive!
    AIMessage(content="oki"),
    HumanMessage(content="rảnh kh"),
    AIMessage(content="rảnh"),
]

casual_next = "mai đi ăn phở kh?"
d_contaminated = determine_response_length(casual_next, conversation_history=contaminated_history)
record(
    "4.2 False positive in history ('text') does not poison subsequent casual turns into LONG tier",
    d_contaminated.tier != LengthTier.LONG,
    f"Classified as {d_contaminated.tier} (tokens={d_contaminated.max_tokens})",
    "CRITICAL"
)

# 4.3 Multimodal / Structured message history format
multimodal_history = [
    HumanMessage(content=[{"type": "text", "text": "chào An"}]),
    AIMessage(content="alo"),
]
d_multimodal = determine_response_length("đi đâu đấy?", conversation_history=multimodal_history)
record(
    "4.3 Multimodal history format containing 'text' dictionary keys does not poison turns into LONG tier",
    d_multimodal.tier != LengthTier.LONG,
    f"Classified as {d_multimodal.tier} (tokens={d_multimodal.max_tokens})",
    "HIGH"
)

# 4.4 Heterogeneous & malformed history items
hetero_history = [
    None,
    123,
    {"content": "chào bạn"},
    ("human", "mai rảnh kh"),
    object(),
]
try:
    d_hetero = determine_response_length("mai đi uống nước kh b", conversation_history=hetero_history)
    record("4.4 Heterogeneous & malformed history items handled gracefully without crashing", True, f"tier={d_hetero.tier}")
except Exception as e:
    record("4.4 Heterogeneous & malformed history items handled gracefully", False, f"Exception: {e}", "CRITICAL")


# ==============================================================================
# 5. DEFENSIVE PROGRAMMING & TYPE CONTRACTS
# ==============================================================================
print("\n--- Running Suite 5: Defensive Programming & Type Contracts ---")

invalid_inputs = [None, 12345, 3.1415, ["hello"], {"msg": "hi"}, True]
type_errors_caught = 0
for inv in invalid_inputs:
    try:
        determine_response_length(inv)
    except TypeError:
        type_errors_caught += 1
    except Exception as e:
        pass

record(
    "5.1 Non-string user_input values reliably raise TypeError",
    type_errors_caught == len(invalid_inputs),
    f"{type_errors_caught}/{len(invalid_inputs)} caught"
)

# Non-list conversation_history
try:
    d_str_hist = determine_response_length("alo", conversation_history="not_a_list")
    d_none_hist = determine_response_length("alo", conversation_history=None)
    d_dict_hist = determine_response_length("alo", conversation_history={"a": 1})
    record("5.2 Non-list conversation_history handled safely as fallback", True, "All non-list histories ignored safely")
except Exception as e:
    record("5.2 Non-list conversation_history handled safely", False, f"Exception: {e}", "HIGH")


# ==============================================================================
# SUMMARY REPORT
# ==============================================================================
print("\n" + "=" * 80)
print("STRESS TEST HARNESS SUMMARY REPORT")
print("=" * 80)

total_tests = len(results)
passed_tests = sum(1 for r in results if r.passed)
failed_tests = total_tests - passed_tests

crit_fails = sum(1 for r in results if not r.passed and r.severity == "CRITICAL")
high_fails = sum(1 for r in results if not r.passed and r.severity == "HIGH")
med_fails = sum(1 for r in results if not r.passed and r.severity == "MEDIUM")
low_fails = sum(1 for r in results if not r.passed and r.severity == "LOW")

print(f"Total Tests Executed: {total_tests}")
print(f"Passed: {passed_tests}")
print(f"Failed: {failed_tests} (Critical: {crit_fails}, High: {high_fails}, Medium: {med_fails}, Low: {low_fails})")

print("\n--- Breakdown of Failures ---")
for r in results:
    if not r.passed:
        print(f"- [{r.severity}] {r.name}: {r.details}")

verdict = "REQUEST_CHANGES" if (crit_fails > 0 or high_fails > 0) else ("APPROVE" if failed_tests == 0 else "APPROVE_WITH_CAVEATS")
print(f"\nFINAL VERDICT: {verdict}")
print("=" * 80)
