"""
Independent Empirical Verification Harness for Persona Profiling & Statistics.
Challenger 2 (Persona Stats Challenger) - Milestone M1.

Validates:
1. Mathematical precision of word count distributions against raw Facebook JSON.
2. Turn aggregation and 2-hour inactivity clustering logic.
3. Token frequencies, slang dictionary fidelity, and prohibited tokens.
4. Few-shot catalog structure, filtering, and formatting.
5. Robustness against adversarial inputs and edge cases.
"""

import json
import statistics
import re
from pathlib import Path
import pytest

from src.ingestion.parser import parse_facebook_json, CanonicalMessage
from src.ingestion.persona_profile import (
    extract_an_an_profile,
    get_few_shot_examples,
    FEW_SHOT_EXCHANGES,
    SLANG_DICTIONARY,
    PROHIBITED_TOKENS,
    PERSONA_PROFILE,
)

RAW_JSON_PATH = Path("F:/dowload/FacebookData/messages/An An_86.json")


# ==============================================================================
# 1. Independent Raw Data Ground Truth Fixture
# ==============================================================================

@pytest.fixture(scope="module")
def raw_ground_truth():
    """Computes independent ground truth directly from raw JSON without using src.ingestion."""
    if not RAW_JSON_PATH.exists():
        pytest.skip(f"Dataset {RAW_JSON_PATH} not found.")

    with open(RAW_JSON_PATH, "r", encoding="utf-8", errors="replace") as f:
        data = json.load(f)

    raw_messages = data.get("messages", [])
    valid_messages = []

    for m in raw_messages:
        text = str(m.get("text") or m.get("content") or "").strip()
        is_unsent = bool(m.get("isUnsent") or m.get("is_unsent") or text == "User unsent a message")
        if is_unsent or not text or "failed to download media" in text.lower():
            continue
        msg_type = str(m.get("type") or m.get("msg_type") or "text").lower()
        if msg_type in ("call", "placeholder") or "missed a call" in text.lower():
            continue

        sender = str(m.get("senderName") or m.get("sender_name") or "Unknown").strip()
        ts = int(m.get("timestamp") or m.get("timestamp_ms") or 0)
        is_an_an = (sender == "An An" or "an an" in sender.lower())

        valid_messages.append({
            "sender": sender,
            "text": text,
            "timestamp_ms": ts,
            "is_an_an": is_an_an
        })

    valid_messages.sort(key=lambda x: x["timestamp_ms"])
    an_an_texts = [m["text"] for m in valid_messages if m["is_an_an"]]
    word_counts = [len(t.split()) for t in an_an_texts]

    return {
        "total_raw": len(raw_messages),
        "total_valid": len(valid_messages),
        "valid_messages": valid_messages,
        "an_an_messages": len(an_an_texts),
        "user_messages": len(valid_messages) - len(an_an_texts),
        "word_counts": word_counts,
        "an_an_texts": an_an_texts,
    }


# ==============================================================================
# 2. Mathematical Precision Tests
# ==============================================================================

class TestMathematicalPrecision:
    """Verifies mathematical calculations with zero margin for numerical illusion."""

    def test_raw_to_canonical_counts(self, raw_ground_truth):
        messages = parse_facebook_json(RAW_JSON_PATH)
        assert len(messages) == raw_ground_truth["total_valid"] == 2032
        an_count = sum(1 for m in messages if m.is_an_an)
        user_count = sum(1 for m in messages if not m.is_an_an)
        assert an_count == raw_ground_truth["an_an_messages"] == 1174
        assert user_count == raw_ground_truth["user_messages"] == 858

    def test_word_count_tier_distribution_precision(self, raw_ground_truth):
        """Validates exact counts and ratios for short (<=5), medium (6-15), and long (>15) words."""
        word_counts = raw_ground_truth["word_counts"]
        n = len(word_counts)
        assert n == 1174

        short_count = sum(1 for c in word_counts if c <= 5)
        medium_count = sum(1 for c in word_counts if 6 <= c <= 15)
        long_count = sum(1 for c in word_counts if c > 15)

        assert short_count == 822
        assert medium_count == 324
        assert long_count == 28
        assert short_count + medium_count + long_count == n

        # Independent floating point ratios
        exact_short_pct = short_count / n    # 0.7001703577512777
        exact_med_pct = medium_count / n     # 0.2759795570698467
        exact_long_pct = long_count / n      # 0.02385008517887564

        assert round(exact_short_pct * 100, 1) == 70.0
        assert round(exact_med_pct * 100, 1) == 27.6
        assert round(exact_long_pct * 100, 1) == 2.4

        # Compare directly against extract_an_an_profile
        messages = parse_facebook_json(RAW_JSON_PATH)
        profile = extract_an_an_profile(messages)
        ld = profile["length_distribution"]

        assert ld["short_count"] == 822
        assert ld["medium_count"] == 324
        assert ld["long_count"] == 28
        assert ld["short_pct"] == 0.7002
        assert ld["medium_pct"] == 0.276
        assert ld["long_pct"] == 0.0239

    def test_mean_and_median_word_counts(self, raw_ground_truth):
        """Verifies mean and median word length of An An message bubbles."""
        word_counts = raw_ground_truth["word_counts"]
        mean_calc = statistics.mean(word_counts)
        median_calc = statistics.median(word_counts)

        assert round(mean_calc, 2) == 4.7
        assert median_calc == 4.0

        messages = parse_facebook_json(RAW_JSON_PATH)
        profile = extract_an_an_profile(messages)
        ld = profile["length_distribution"]

        assert ld["mean_words"] == 4.7
        assert ld["median_words"] == 4.0

    def test_length_distribution_exhaustive_partition(self, raw_ground_truth):
        """Ensures every single An An message is counted into exactly one tier."""
        messages = parse_facebook_json(RAW_JSON_PATH)
        profile = extract_an_an_profile(messages)
        ld = profile["length_distribution"]

        total_tiered = ld["short_count"] + ld["medium_count"] + ld["long_count"]
        assert total_tiered == profile["overview"]["an_an_messages"] == 1174


# ==============================================================================
# 3. Token Frequency & Slang Dictionary Verification
# ==============================================================================

class TestTokenFrequenciesAndSlang:
    """Verifies empirical token frequencies against raw message corpus."""

    def test_signature_slang_empirical_counts(self):
        messages = parse_facebook_json(RAW_JSON_PATH)
        profile = extract_an_an_profile(messages)
        tf = profile["token_frequencies"]

        expected_counts = {
            "kh": 143,
            "hong": 12,
            "dc": 42,
            "nma": 36,
            "r": 100,
            "v": 38,
            "z": 17,
            "th": 40,
            "thui": 7,
            "oki": 31,
            "ql": 40,
            "=)))": 81,
            "🤡": 14,
        }
        for token, expected in expected_counts.items():
            assert tf.get(token) == expected, (
                f"Token '{token}' frequency mismatch: got {tf.get(token)}, expected {expected}"
            )

    def test_anti_pattern_prohibited_tokens_in_profile(self):
        """Verifies strictly banned tokens and audits the rare 'ko' occurrence."""
        messages = parse_facebook_json(RAW_JSON_PATH)
        profile = extract_an_an_profile(messages)
        tf = profile["token_frequencies"]

        # Strictly 0 occurrences in An An messages
        assert tf.get("k", 0) == 0, "An An should have 0 occurrences of 'k'"
        assert tf.get("đc", 0) == 0, "An An should have 0 occurrences of 'đc'"
        assert tf.get("nhma", 0) == 0, "An An should have 0 occurrences of 'nhma'"
        assert tf.get("oke", 0) == 0, "An An should have 0 occurrences of 'oke'"

        # Audit 'ko': exactly 2 occurrences in 1174 messages (98.6% 'kh' dominance)
        assert tf.get("ko", 0) == 2, "An An has exactly 2 occurrences of 'ko' ('Ko cl' & 'Trên chợ có nóng ko')"

    def test_slang_dictionary_coverage(self):
        """Verifies that all entries in SLANG_DICTIONARY have required metadata fields."""
        for token, info in SLANG_DICTIONARY.items():
            assert "meaning" in info and isinstance(info["meaning"], str)
            assert "empirical_count" in info and isinstance(info["empirical_count"], int)
            assert "forbidden" in info and isinstance(info["forbidden"], list)
            assert "example" in info and isinstance(info["example"], str)
            assert "rule" in info and isinstance(info["rule"], str)


# ==============================================================================
# 4. Turn Aggregation & Dialogue Pair Extraction
# ==============================================================================

class TestTurnAggregationAndPairing:
    """Verifies turn aggregation with 2-hour inactivity grouping and dialogue pairing."""

    def test_turn_aggregation_ground_truth_counts(self):
        messages = parse_facebook_json(RAW_JSON_PATH)
        profile = extract_an_an_profile(messages)

        assert profile["overview"]["total_turns"] == 806
        assert profile["overview"]["extracted_turn_pairs"] == 392

    def test_turn_clustering_two_hour_inactivity_rule(self):
        """Verifies that messages from the same sender separated by >2 hours split into distinct turns."""
        burst_same_sender = [
            CanonicalMessage(
                sender_name="QL",
                text="Morning msg",
                timestamp_ms=1000,
                is_an_an=False
            ),
            CanonicalMessage(
                sender_name="QL",
                text="Afternoon msg (>2 hrs later)",
                timestamp_ms=1000 + 7_200_001,  # 2 hours + 1 ms
                is_an_an=False
            ),
            CanonicalMessage(
                sender_name="An An",
                text="Evening reply",
                timestamp_ms=1000 + 7_200_001 + 60_000,  # 1 min after
                is_an_an=True
            ),
        ]
        profile = extract_an_an_profile(burst_same_sender)
        assert profile["overview"]["total_turns"] == 3
        # Should pair turn 1 (Afternoon msg) with turn 2 (Evening reply)
        pairs = profile["dialogue_pairs"]
        assert len(pairs) == 1
        assert pairs[0]["user_input"] == "Afternoon msg (>2 hrs later)"
        assert pairs[0]["an_an_response"] == "Evening reply"

    def test_consecutive_messages_within_threshold_clustered(self):
        """Verifies that messages from the same sender within 2 hours are merged by newline."""
        burst = [
            CanonicalMessage(
                sender_name="An An",
                text="Bubble 1",
                timestamp_ms=1000,
                is_an_an=True
            ),
            CanonicalMessage(
                sender_name="An An",
                text="Bubble 2",
                timestamp_ms=2000,
                is_an_an=True
            ),
            CanonicalMessage(
                sender_name="An An",
                text="Bubble 3",
                timestamp_ms=3000,
                is_an_an=True
            ),
        ]
        profile = extract_an_an_profile(burst)
        assert profile["overview"]["total_turns"] == 1
        assert profile["overview"]["extracted_turn_pairs"] == 0

    def test_inter_turn_gap_empirical_reality(self):
        """
        Empirical discovery test:
        Verifies that dialogue pair extraction pairs User turns followed immediately by An An turns.
        Documenting that 29 pairs have an elapsed time > 2 hours (e.g. An An initiating after days).
        """
        messages = parse_facebook_json(RAW_JSON_PATH)
        profile = extract_an_an_profile(messages)
        pairs = profile["dialogue_pairs"]
        assert len(pairs) == 392

        # First pair verification
        assert pairs[0]["user_input"] == "Chúc An mai thi tốt"
        assert pairs[0]["an_an_response"] == "Cám mơn ql nhieu nhaa"

        # Second pair verification (gap of 68.2 hours)
        assert pairs[1]["user_input"] == "tự tin lên cố lên 💪"
        assert pairs[1]["an_an_response"] == "Jza"


# ==============================================================================
# 5. Few-Shot Catalog & Formatting
# ==============================================================================

class TestFewShotCatalogAndFormatting:
    """Verifies few-shot exemplar structure, retrieval, and formatting."""

    def test_few_shot_exchange_count_and_categories(self):
        assert len(FEW_SHOT_EXCHANGES) == 15
        expected_categories = {
            "CASUAL_BANTER",
            "STUDY_COORDINATION",
            "TEASING_DEBT",
            "GOSSIP_DRAMA",
            "EMOTIONAL_BOUNDARY",
            "VENTING_FATIGUE",
        }
        actual_categories = {ex["category"] for ex in FEW_SHOT_EXCHANGES}
        assert actual_categories == expected_categories

    def test_get_few_shot_examples_contract(self):
        examples = get_few_shot_examples(limit=5)
        assert len(examples) == 5
        for ex in examples:
            assert "input" in ex and isinstance(ex["input"], str) and len(ex["input"]) > 0
            assert "output" in ex and isinstance(ex["output"], str) and len(ex["output"]) > 0

    def test_get_few_shot_examples_category_filtering(self):
        banter = get_few_shot_examples(category="CASUAL_BANTER", limit=100)
        assert len(banter) == 7
        debt = get_few_shot_examples(category="TEASING_DEBT", limit=100)
        assert len(debt) == 1

    def test_get_few_shot_examples_invalid_category(self):
        empty = get_few_shot_examples(category="NON_EXISTENT_CAT")
        assert empty == []

    @pytest.mark.xfail(reason="BUG REPRODUCTION: get_few_shot_examples(limit=0) returns 1 element instead of [] because append occurs before condition check and limit <= 0 is unhandled at entry.")
    def test_get_few_shot_examples_zero_and_negative_limits(self):
        assert get_few_shot_examples(limit=0) == []
        assert get_few_shot_examples(limit=-5) == []

    def test_few_shot_an_an_text_authenticity(self):
        """Ensures all An An responses in few-shot catalog are grounded in real message texts."""
        messages = parse_facebook_json(RAW_JSON_PATH)
        all_an_text = "\n".join(m.text for m in messages if m.is_an_an)

        for ex in FEW_SHOT_EXCHANGES:
            for turn in ex["turns"]:
                first_line = turn["an_an"].split("\n")[0].strip()
                assert first_line in all_an_text, (
                    f"Few-shot An An response '{first_line}' not found in raw dataset!"
                )


# ==============================================================================
# 6. Fault Tolerance & Adversarial Boundary Tests
# ==============================================================================

class TestAdversarialBoundaries:
    """Stress-tests assumptions, malformed inputs, and edge conditions."""

    def test_empty_messages_list(self):
        profile = extract_an_an_profile([])
        assert profile["overview"]["total_messages"] == 0
        assert profile["overview"]["an_an_messages"] == 0
        assert profile["overview"]["user_messages"] == 0
        assert profile["overview"]["total_turns"] == 0
        assert profile["overview"]["extracted_turn_pairs"] == 0
        assert profile["length_distribution"]["short_pct"] == 0.0
        assert profile["length_distribution"]["mean_words"] == 0.0
        assert profile["length_distribution"]["median_words"] == 0.0

    def test_only_user_messages(self):
        messages = [
            CanonicalMessage(sender_name="User", text="Alo", timestamp_ms=100, is_an_an=False),
            CanonicalMessage(sender_name="User", text="Có đó không", timestamp_ms=200, is_an_an=False),
        ]
        profile = extract_an_an_profile(messages)
        assert profile["overview"]["an_an_messages"] == 0
        assert profile["overview"]["extracted_turn_pairs"] == 0
        assert profile["length_distribution"]["short_count"] == 0

    def test_only_an_an_messages(self):
        messages = [
            CanonicalMessage(sender_name="An An", text="Alo ql", timestamp_ms=100, is_an_an=True),
            CanonicalMessage(sender_name="An An", text="Đi cf kh", timestamp_ms=200, is_an_an=True),
        ]
        profile = extract_an_an_profile(messages)
        assert profile["overview"]["user_messages"] == 0
        assert profile["overview"]["extracted_turn_pairs"] == 0
        assert profile["length_distribution"]["short_count"] == 2
        assert profile["length_distribution"]["short_pct"] == 1.0

    def test_whitespace_only_messages_handling(self):
        """Verifies handling of messages with whitespace only."""
        messages = [
            CanonicalMessage(sender_name="An An", text="   ", timestamp_ms=100, is_an_an=True),
            CanonicalMessage(sender_name="An An", text="Valid text", timestamp_ms=200, is_an_an=True),
        ]
        profile = extract_an_an_profile(messages)
        # Should gracefully calculate without crashing
        assert profile["overview"]["an_an_messages"] == 2
        assert profile["length_distribution"]["short_count"] == 2

    def test_emojis_and_emoticons_only(self):
        """Verifies word counts when messages consist strictly of emojis and emoticons."""
        messages = [
            CanonicalMessage(sender_name="An An", text="=))) 🤡", timestamp_ms=100, is_an_an=True),
            CanonicalMessage(sender_name="An An", text="🌸", timestamp_ms=200, is_an_an=True),
        ]
        profile = extract_an_an_profile(messages)
        assert profile["length_distribution"]["short_count"] == 2
        assert profile["token_frequencies"]["=)))"] == 1
        assert profile["token_frequencies"]["🤡"] == 1

    def test_unsorted_messages_robustness(self):
        """
        Tests what happens if unsorted messages are passed directly to extract_an_an_profile.
        Reveals that extract_an_an_profile relies on caller (parse_facebook_json) to pre-sort.
        """
        unsorted = [
            CanonicalMessage(sender_name="QL", text="Msg 2", timestamp_ms=2000, is_an_an=False),
            CanonicalMessage(sender_name="QL", text="Msg 1", timestamp_ms=1000, is_an_an=False),
            CanonicalMessage(sender_name="An An", text="Reply", timestamp_ms=3000, is_an_an=True),
        ]
        # Does not crash, but combines based on list order
        profile = extract_an_an_profile(unsorted)
        assert isinstance(profile, dict)
        assert profile["overview"]["total_messages"] == 3
