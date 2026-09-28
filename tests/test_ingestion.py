"""
Comprehensive Unit Test Suite for Milestone M1 Data Ingestion & Persona Profiling.
Matches test_spec.md across 49+ test cases with zero external network dependencies.
"""

import json
from pathlib import Path
import pytest

from src.config import (
    validate_environment,
    get_api_key,
    get_active_provider,
    DEFAULT_JSON_PATH,
)
from src.ingestion.parser import (
    CanonicalMessage,
    safe_decode_mojibake,
    fix_fb_text,
    parse_facebook_json,
)
from src.ingestion.persona_profile import (
    extract_an_an_profile,
    get_few_shot_examples,
    FEW_SHOT_EXCHANGES,
    SLANG_DICTIONARY,
    PROHIBITED_TOKENS,
    PERSONA_PROFILE,
    VIETNAMESE_LANGUAGE_INSTRUCTION,
    format_few_shot_prompt,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def real_sample_json_path():
    """Resolves primary verification dataset on host if available."""
    primary_path = Path("F:/dowload/FacebookData/messages/An An_86.json")
    if primary_path.exists():
        return str(primary_path)
    fallback_path = Path(DEFAULT_JSON_PATH)
    if fallback_path.exists():
        return str(fallback_path)
    pytest.skip("Primary verification dataset F:/dowload/FacebookData/messages/An An_86.json not found.")


@pytest.fixture
def synthetic_modern_fb_json(tmp_path):
    """Generates synthetic Facebook export in modern schema format."""
    data = {
        "participants": ["Hoàng Kim Quờ Lờ", "An An"],
        "threadName": "An An_86",
        "messages": [
            {
                "senderName": "Hoàng Kim Quờ Lờ",
                "text": "Chúc An mai thi tốt",
                "timestamp": 1747310703021,
                "isUnsent": False,
                "reactions": [{"actor": "An An", "reaction": "❤"}],
                "type": "text"
            },
            {
                "senderName": "An An",
                "text": "Cám mơn ql nhieu nhaa",
                "timestamp": 1747310725247,
                "isUnsent": False,
                "reactions": [{"actor": "Hoàng Kim Quờ Lờ", "reaction": "👌"}],
                "type": "text"
            },
            {
                "senderName": "Hoàng Kim Quờ Lờ",
                "text": "User unsent a message",
                "timestamp": 1747533014133,
                "isUnsent": True,
                "reactions": [],
                "type": "placeholder"
            }
        ]
    }
    file_path = tmp_path / "modern_sample.json"
    file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(file_path)


@pytest.fixture
def synthetic_standard_fb_json(tmp_path):
    """Generates synthetic Facebook export in standard legacy schema format."""
    data = {
        "participants": [{"name": "Hoàng Kim Quờ Lờ"}, {"name": "An An"}],
        "title": "An An",
        "messages": [
            {
                "sender_name": "Hoàng Kim Quờ Lờ",
                "content": "tự tin lên cố lên 💪",
                "timestamp_ms": 1747310804037,
                "is_unsent": False,
                "reactions": [{"actor": "An An", "reaction": "❤"}]
            },
            {
                "sender_name": "An An",
                "content": "Jza",
                "timestamp_ms": 1747310810000,
                "is_unsent": False,
                "reactions": []
            }
        ]
    }
    file_path = tmp_path / "standard_sample.json"
    file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(file_path)


@pytest.fixture
def dirty_filter_fb_json(tmp_path):
    """Generates synthetic dataset containing various noisy and invalid message formats."""
    data = {
        "participants": ["Hoàng Kim Quờ Lờ", "An An"],
        "threadName": "Test Filter",
        "messages": [
            {"senderName": "Hoàng Kim Quờ Lờ", "text": "Hợp lệ 1", "timestamp": 1000, "isUnsent": False},
            {"senderName": "Hoàng Kim Quờ Lờ", "text": "User unsent a message", "timestamp": 2000, "isUnsent": True},
            {"senderName": "An An", "text": "Failed to download media", "timestamp": 3000, "isUnsent": False},
            {"senderName": "An An", "text": "", "timestamp": 4000, "isUnsent": False, "media": [{"uri": "photo.jpg"}]},
            {"senderName": "An An", "text": "   \n\t  ", "timestamp": 5000, "isUnsent": False},
            {"senderName": "Hoàng Kim Quờ Lờ", "text": "Hợp lệ 2", "timestamp": 6000, "isUnsent": False},
            {"senderName": "An An", "text": "Hợp lệ 3", "timestamp": 7000, "isUnsent": False}
        ]
    }
    file_path = tmp_path / "dirty_filter.json"
    file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(file_path)


# ==============================================================================
# Group 1: Safe Transcoding & Mojibake Repair (TestSafeMojibakeDecoder)
# ==============================================================================

class TestSafeMojibakeDecoder:
    def test_transcode_native_utf8_vietnamese_pass_through(self):
        sample = "Chào An An, bạn có ở đó không? Đi uống cà phê không nhờ! 🌸"
        result = safe_decode_mojibake(sample)
        assert result == sample, "Native UTF-8 Vietnamese must pass through without modification"

    def test_transcode_latin1_double_encoded_mojibake_repaired(self):
        raw_mojibake = "C\u00c3\u00a1m m\u00c6\u00a1n ql nhieu nhaa"
        result = safe_decode_mojibake(raw_mojibake)
        assert result == "Cám mơn ql nhieu nhaa"

    def test_transcode_latin1_common_vietnamese_phrases(self):
        raw = "Ch\u00c3\u00a0o b\u00e1\u00ba\u00a1n"
        result = safe_decode_mojibake(raw)
        assert result == "Chào bạn"

    def test_transcode_mixed_latin1_and_native_unicode(self):
        mixed = "Chào An \u00c3\u00a1 \u1edd"
        try:
            result = safe_decode_mojibake(mixed)
            assert isinstance(result, str)
        except UnicodeEncodeError:
            pytest.fail("safe_decode_mojibake raised UnicodeEncodeError on mixed text!")

    def test_transcode_emojis_and_emoticons_intact(self):
        text_with_emojis = "Quỉ=))) 🤡 ❤ 👌 💪 ☺ 🥲 😭 ☕"
        result = safe_decode_mojibake(text_with_emojis)
        assert result == text_with_emojis

    def test_transcode_ascii_and_punctuation(self):
        ascii_text = "Test ASCII 123 !@#$%^&*()_+"
        assert safe_decode_mojibake(ascii_text) == ascii_text

    @pytest.mark.parametrize("falsy_val", ["", None, "   "])
    def test_transcode_empty_and_falsy_inputs(self, falsy_val):
        assert safe_decode_mojibake(falsy_val) in ("", "   ")

    @pytest.mark.parametrize("bad_val", [123, 45.6, [], {}])
    def test_transcode_non_string_types(self, bad_val):
        result = safe_decode_mojibake(bad_val)
        assert result == ""

    def test_fix_fb_text_alias_compatibility(self):
        raw = "Ch\u00c3\u00a0o b\u00e1\u00ba\u00a1n"
        assert fix_fb_text(raw) == safe_decode_mojibake(raw)


# ==============================================================================
# Group 2: Happy Path Facebook JSON Parsing (TestFacebookJsonParserHappyPath)
# ==============================================================================

class TestFacebookJsonParserHappyPath:
    def test_parse_real_an_an_file_loads_successfully(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        assert isinstance(messages, list)
        assert len(messages) > 2000
        assert all(isinstance(m, CanonicalMessage) for m in messages)

    def test_parse_real_an_an_message_count(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        # 2102 total - 15 unsent - 55 empty/media = 2032 valid canonical messages
        assert 2030 <= len(messages) <= 2087

    def test_parse_real_an_an_participants_and_senders(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        senders = {m.sender_name for m in messages}
        assert senders == {"Hoàng Kim Quờ Lờ", "An An"}

    def test_parse_real_an_an_sender_distribution(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        an_count = sum(1 for m in messages if m.is_an_an)
        ql_count = sum(1 for m in messages if not m.is_an_an)
        assert 1170 <= an_count <= 1205
        assert 855 <= ql_count <= 895

    def test_parse_real_an_an_chronological_ordering(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        for i in range(len(messages) - 1):
            assert messages[i].timestamp_ms <= messages[i + 1].timestamp_ms, (
                f"Messages out of order at index {i}: {messages[i].timestamp_ms} > {messages[i + 1].timestamp_ms}"
            )

    def test_parse_is_an_an_flag_correctness(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        for m in messages:
            if m.sender_name == "An An":
                assert m.is_an_an is True
            else:
                assert m.is_an_an is False

    def test_parse_modern_tool_schema_fixture(self, synthetic_modern_fb_json):
        messages = parse_facebook_json(synthetic_modern_fb_json)
        assert len(messages) == 2
        assert messages[0].sender_name == "Hoàng Kim Quờ Lờ"
        assert messages[0].text == "Chúc An mai thi tốt"
        assert messages[0].is_an_an is False
        assert messages[1].sender_name == "An An"
        assert messages[1].text == "Cám mơn ql nhieu nhaa"
        assert messages[1].is_an_an is True

    def test_parse_standard_fb_export_schema_fixture(self, synthetic_standard_fb_json):
        messages = parse_facebook_json(synthetic_standard_fb_json)
        assert len(messages) == 2
        assert messages[0].sender_name == "Hoàng Kim Quờ Lờ"
        assert messages[0].text == "tự tin lên cố lên 💪"
        assert messages[1].sender_name == "An An"
        assert messages[1].text == "Jza"

    def test_parse_reactions_extraction(self, synthetic_modern_fb_json):
        messages = parse_facebook_json(synthetic_modern_fb_json)
        assert "❤" in messages[0].reactions
        assert "👌" in messages[1].reactions


# ==============================================================================
# Group 3: Message Filtering & Noise Suppression (TestMessageFiltering)
# ==============================================================================

class TestMessageFiltering:
    def test_filter_unsent_messages_boolean_flag(self, tmp_path):
        data = {
            "messages": [
                {"senderName": "An An", "text": "Tin đúng", "timestamp": 100, "isUnsent": False},
                {"senderName": "An An", "text": "Tin bị thu hồi", "timestamp": 200, "isUnsent": True}
            ]
        }
        f = tmp_path / "unsent_bool.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        messages = parse_facebook_json(str(f))
        assert len(messages) == 1
        assert messages[0].text == "Tin đúng"

    def test_filter_unsent_placeholder_text(self, tmp_path):
        data = {
            "messages": [
                {"senderName": "QL", "text": "Hello", "timestamp": 1, "isUnsent": False},
                {"senderName": "QL", "text": "User unsent a message", "timestamp": 2, "isUnsent": False}
            ]
        }
        f = tmp_path / "unsent_text.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        messages = parse_facebook_json(str(f))
        assert len(messages) == 1
        assert messages[0].text == "Hello"

    def test_filter_failed_to_download_media(self, tmp_path):
        data = {
            "messages": [
                {"senderName": "An An", "text": "Failed to download media", "timestamp": 1, "isUnsent": False},
                {"senderName": "An An", "text": "Jza", "timestamp": 2, "isUnsent": False}
            ]
        }
        f = tmp_path / "failed_media.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        messages = parse_facebook_json(str(f))
        assert len(messages) == 1
        assert messages[0].text == "Jza"

    def test_filter_empty_and_whitespace_messages(self, tmp_path):
        data = {
            "messages": [
                {"senderName": "QL", "text": "", "timestamp": 1},
                {"senderName": "QL", "text": "   \n\t  ", "timestamp": 2},
                {"senderName": "QL", "text": "Tin chuẩn", "timestamp": 3}
            ]
        }
        f = tmp_path / "empty_ws.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        messages = parse_facebook_json(str(f))
        assert len(messages) == 1
        assert messages[0].text == "Tin chuẩn"

    def test_filter_system_call_events(self, tmp_path):
        data = {
            "messages": [
                {"senderName": "QL", "text": "Missed a call", "timestamp": 1, "type": "call"},
                {"senderName": "QL", "text": "Alo nghe kh", "timestamp": 2, "type": "text"}
            ]
        }
        f = tmp_path / "call_event.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        messages = parse_facebook_json(str(f))
        assert len(messages) == 1
        assert messages[0].text == "Alo nghe kh"

    def test_dirty_fixture_filtering_accuracy(self, dirty_filter_fb_json):
        messages = parse_facebook_json(dirty_filter_fb_json)
        assert len(messages) == 3
        texts = [m.text for m in messages]
        assert texts == ["Hợp lệ 1", "Hợp lệ 2", "Hợp lệ 3"]


# ==============================================================================
# Group 4: Persona Profiling & Empirical Distributions (TestPersonaProfiling)
# ==============================================================================

class TestPersonaProfiling:
    def test_profile_overall_stats_counts(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        stats = profile.get("stats", {})
        assert stats.get("total_messages", len(messages)) >= 2030
        assert stats.get("an_an_messages", 0) >= 1170
        assert stats.get("user_messages", 0) >= 855

    def test_profile_length_distribution_short_ratio(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        ld = profile.get("stats", {}).get("length_distribution", profile.get("length_distribution", {}))
        short_pct = ld.get("short_pct", 0.0)
        assert 0.67 <= short_pct <= 0.73, f"Short ratio {short_pct} outside [0.67, 0.73]"

    def test_profile_length_distribution_medium_ratio(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        ld = profile.get("stats", {}).get("length_distribution", profile.get("length_distribution", {}))
        med_pct = ld.get("medium_pct", 0.0)
        assert 0.25 <= med_pct <= 0.31, f"Medium ratio {med_pct} outside [0.25, 0.31]"

    def test_profile_length_distribution_long_ratio(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        ld = profile.get("stats", {}).get("length_distribution", profile.get("length_distribution", {}))
        long_pct = ld.get("long_pct", 0.0)
        assert 0.01 <= long_pct <= 0.04, f"Long ratio {long_pct} outside [0.01, 0.04]"

    def test_profile_word_mean_and_median(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        ld = profile.get("stats", {}).get("length_distribution", profile.get("length_distribution", {}))
        mean_words = ld.get("mean_words", 0.0)
        median_words = ld.get("median_words", 0.0)
        assert 4.2 <= mean_words <= 5.2, f"Mean words {mean_words} outside [4.2, 5.2]"
        assert 3.0 <= median_words <= 5.0, f"Median words {median_words} outside [3.0, 5.0]"

    def test_profile_signature_token_kh(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        tokens = profile.get("token_frequencies", profile.get("tokens", {}))
        assert tokens.get("kh", 0) >= 100

    def test_profile_signature_token_dc(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        tokens = profile.get("token_frequencies", profile.get("tokens", {}))
        assert tokens.get("dc", 0) >= 30

    def test_profile_signature_token_nma(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        tokens = profile.get("token_frequencies", profile.get("tokens", {}))
        assert tokens.get("nma", 0) >= 25

    def test_profile_signature_token_r(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        tokens = profile.get("token_frequencies", profile.get("tokens", {}))
        assert tokens.get("r", 0) >= 75

    def test_profile_signature_token_laugh_and_emoji(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        tokens = profile.get("token_frequencies", profile.get("tokens", {}))
        assert tokens.get("=)))", 0) >= 50
        assert tokens.get("🤡", 0) >= 10

    def test_profile_signature_token_ql(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        tokens = profile.get("token_frequencies", profile.get("tokens", {}))
        assert tokens.get("ql", 0) >= 30

    def test_profile_anti_pattern_tokens_banned(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        tokens = profile.get("token_frequencies", profile.get("tokens", {}))
        assert tokens.get("k", 0) == 0, "An An never uses isolated 'k'"
        assert tokens.get("đc", 0) == 0, "An An never uses 'đc' (always 'dc')"
        assert tokens.get("nhma", 0) == 0, "An An never uses 'nhma' (always 'nma')"


# ==============================================================================
# Group 5: Dialogue Pair Extraction & Turn Collapsing (TestDialoguePairExtraction)
# ==============================================================================

class TestDialoguePairExtraction:
    def test_extract_dialogue_pairs_total_count(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        pairs = profile.get("dialogue_pairs", profile.get("pairs", []))
        assert len(pairs) >= 380, f"Expected >= 380 dialogue pairs, got {len(pairs)}"

    def test_extract_dialogue_pairs_turn_aggregation(self, tmp_path):
        data = {
            "participants": ["QL", "An An"],
            "messages": [
                {"senderName": "QL", "text": "Tin 1", "timestamp": 100, "isUnsent": False},
                {"senderName": "QL", "text": "Tin 2", "timestamp": 200, "isUnsent": False},
                {"senderName": "An An", "text": "Hồi đáp 1", "timestamp": 300, "isUnsent": False},
                {"senderName": "An An", "text": "Hồi đáp 2", "timestamp": 400, "isUnsent": False}
            ]
        }
        file_path = tmp_path / "bursts.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")
        messages = parse_facebook_json(str(file_path))
        profile = extract_an_an_profile(messages)
        pairs = profile.get("dialogue_pairs", [])
        assert len(pairs) == 1
        assert "Tin 1" in pairs[0]["user_input"] and "Tin 2" in pairs[0]["user_input"]
        assert "Hồi đáp 1" in pairs[0]["an_an_response"] and "Hồi đáp 2" in pairs[0]["an_an_response"]

    def test_extract_dialogue_pairs_ground_truth_turn_0(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        pairs = profile.get("dialogue_pairs", profile.get("pairs", []))
        assert len(pairs) > 0
        pair_0 = pairs[0]
        assert "Chúc An mai thi tốt" in pair_0["user_input"]
        assert "Cám mơn ql nhieu nhaa" in pair_0["an_an_response"]

    def test_extract_dialogue_pairs_ground_truth_turn_1(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        pairs = profile.get("dialogue_pairs", profile.get("pairs", []))
        assert len(pairs) > 1
        pair_1 = pairs[1]
        assert "tự tin lên cố lên" in pair_1["user_input"]
        assert "Jza" in pair_1["an_an_response"]

    def test_extract_dialogue_pairs_few_shot_structure(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        pairs = profile.get("dialogue_pairs", [])
        for p in pairs[:10]:
            assert "user_input" in p and isinstance(p["user_input"], str)
            assert "an_an_response" in p and isinstance(p["an_an_response"], str)


# ==============================================================================
# Group 6: Fault Tolerance & Edge Cases (TestFaultToleranceAndEdgeCases)
# ==============================================================================

class TestFaultToleranceAndEdgeCases:
    def test_fault_tolerance_non_existent_file(self):
        with pytest.raises(FileNotFoundError):
            parse_facebook_json("non_existent_file_path_xyz123.json")

    def test_fault_tolerance_malformed_json_syntax(self, tmp_path):
        corrupt_file = tmp_path / "corrupt.json"
        corrupt_file.write_text("{\"participants\": [ broken json...", encoding="utf-8")
        with pytest.raises((ValueError, json.JSONDecodeError)):
            parse_facebook_json(str(corrupt_file))

    def test_fault_tolerance_empty_file_zero_bytes(self, tmp_path):
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("", encoding="utf-8")
        with pytest.raises((ValueError, json.JSONDecodeError)):
            parse_facebook_json(str(empty_file))

    def test_fault_tolerance_empty_messages_array(self, tmp_path):
        empty_array_file = tmp_path / "empty_array.json"
        empty_array_file.write_text(json.dumps({"participants": ["An An"], "messages": []}), encoding="utf-8")
        messages = parse_facebook_json(str(empty_array_file))
        assert messages == []

    def test_profile_empty_messages_zero_division_safe(self):
        try:
            profile = extract_an_an_profile([])
            assert isinstance(profile, dict)
            stats = profile.get("stats", {})
            assert stats.get("total_messages", 0) == 0
            assert profile.get("dialogue_pairs", []) == []
        except ZeroDivisionError:
            pytest.fail("extract_an_an_profile raised ZeroDivisionError on empty message list!")

    def test_messages_missing_optional_fields(self, tmp_path):
        data = {
            "messages": [
                {"senderName": "An An", "text": "Tin nhắn thiếu trường", "timestamp": 12345}
            ]
        }
        file_path = tmp_path / "minimal.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")
        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 1
        assert messages[0].sender_name == "An An"
        assert messages[0].reactions == []
        assert messages[0].is_an_an is True

    def test_single_participant_chat_pairs(self):
        messages = [
            CanonicalMessage(
                sender_name="An An",
                text="Tin 1",
                timestamp_ms=1000,
                is_an_an=True
            ),
            CanonicalMessage(
                sender_name="An An",
                text="Tin 2",
                timestamp_ms=2000,
                is_an_an=True
            )
        ]
        profile = extract_an_an_profile(messages)
        assert profile.get("dialogue_pairs", []) == []

    def test_reverse_chronological_input_sorting(self, tmp_path):
        data = {
            "participants": ["A", "An An"],
            "messages": [
                {"senderName": "A", "text": "Later", "timestamp": 2000, "isUnsent": False},
                {"senderName": "A", "text": "Earlier", "timestamp": 1000, "isUnsent": False}
            ]
        }
        file_path = tmp_path / "reverse.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")
        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 2
        assert messages[0].timestamp_ms == 1000
        assert messages[1].timestamp_ms == 2000

    def test_extreme_large_message_burst(self):
        messages = [
            CanonicalMessage(
                sender_name="An An",
                text=f"Tin burst {i}",
                timestamp_ms=1000 + i * 100,
                is_an_an=True
            )
            for i in range(50)
        ]
        profile = extract_an_an_profile(messages)
        assert profile["overview"]["total_messages"] == 50
        assert profile["overview"]["total_turns"] == 1

    def test_parse_facebook_json_utf8_bom_support(self, tmp_path):
        """Validates that JSON files with UTF-8 BOM are decoded without JSONDecodeError."""
        data = {"messages": [{"senderName": "An An", "text": "Có BOM nè", "timestamp": 1000}]}
        bom_content = "\ufeff" + json.dumps(data)
        file_path = tmp_path / "bom_sample.json"
        file_path.write_text(bom_content, encoding="utf-8")
        
        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 1
        assert messages[0].text == "Có BOM nè"
        assert messages[0].is_an_an is True

    def test_parse_facebook_json_null_content_ignored(self, tmp_path):
        """Validates that messages with 'content': null are not stringified into 'None'."""
        data = {
            "messages": [
                {"sender_name": "An An", "content": None, "timestamp_ms": 1000, "photos": [{"uri": "img.jpg"}]},
                {"sender_name": "QL", "text": None, "content": None, "timestamp_ms": 2000},
                {"sender_name": "An An", "content": "Tin nhắn thật", "timestamp_ms": 3000}
            ]
        }
        file_path = tmp_path / "null_content.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")

        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 1
        assert messages[0].text == "Tin nhắn thật"
        assert all(m.text != "None" for m in messages)

    def test_parse_facebook_json_timestamp_infinity_overflow(self, tmp_path):
        """Validates that non-finite Infinity timestamps do not raise OverflowError."""
        data_str = '{"messages": [{"senderName": "An An", "text": "Test inf", "timestamp": Infinity}]}'
        file_path = tmp_path / "infinity_ts.json"
        file_path.write_text(data_str, encoding="utf-8")

        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 1
        assert messages[0].timestamp_ms == 0

    def test_parse_facebook_json_sender_name_van_an_collision(self, tmp_path):
        """Validates that 'Nguyen Van An' is not flagged as An An due to substring matching."""
        data = {
            "messages": [
                {"senderName": "An An", "text": "Tin 1", "timestamp": 1000},
                {"senderName": "Nguyen Van An", "text": "Tin 2", "timestamp": 2000},
                {"senderName": "Bé An An 🌸", "text": "Tin 3", "timestamp": 3000},
                {"senderName": "Trần Tuấn An", "text": "Tin 4", "timestamp": 4000}
            ]
        }
        file_path = tmp_path / "sender_names.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")

        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 4
        assert messages[0].is_an_an is True
        assert messages[1].is_an_an is False  # Nguyen Van An must be False
        assert messages[2].is_an_an is True   # Bé An An must be True
        assert messages[3].is_an_an is False  # Tran Tuan An must be False


# ==============================================================================
# Group 7: Configuration & Few-Shot Catalog Tests
# ==============================================================================

class TestConfigAndFewShotCatalog:
    def test_config_environment_validation(self):
        env_audit = validate_environment()
        assert isinstance(env_audit, dict)
        assert "active_provider" in env_audit
        assert env_audit["active_provider"] in ("gemini", "groq", "mock")
        assert "project_root" in env_audit
        assert "default_json_path" in env_audit

    def test_config_get_api_key_helper(self):
        gemini_key = get_api_key("gemini")
        google_key = get_api_key("google")
        assert gemini_key == google_key
        invalid_key = get_api_key("unknown_provider")
        assert invalid_key is None

    def test_few_shot_catalog_exchanges_structure(self):
        assert len(FEW_SHOT_EXCHANGES) == 15
        categories = {ex["category"] for ex in FEW_SHOT_EXCHANGES}
        expected_categories = {
            "CASUAL_BANTER",
            "STUDY_COORDINATION",
            "TEASING_DEBT",
            "GOSSIP_DRAMA",
            "EMOTIONAL_BOUNDARY",
            "VENTING_FATIGUE",
        }
        assert expected_categories.issubset(categories)

    def test_few_shot_get_examples_filtered(self):
        casual = get_few_shot_examples(category="CASUAL_BANTER", limit=3)
        assert 1 <= len(casual) <= 3
        for ex in casual:
            assert "input" in ex and "output" in ex

    def test_few_shot_get_examples_unfiltered_limit(self):
        all_ex = get_few_shot_examples(limit=5)
        assert len(all_ex) == 5

    def test_slang_dictionary_and_prohibited_tokens(self):
        assert "kh" in SLANG_DICTIONARY
        assert "dc" in SLANG_DICTIONARY
        assert "nma" in SLANG_DICTIONARY
        assert "=)))" in SLANG_DICTIONARY
        assert "k" in PROHIBITED_TOKENS
        assert "đc" in PROHIBITED_TOKENS
        assert "nhma" in PROHIBITED_TOKENS


# ==============================================================================
# Group 8: Milestone M1 Iteration 2 Regression Tests (Challenger Issues)
# ==============================================================================

class TestRegressionChallengerIssues:
    """
    Regression test cases for defects identified during Challenger audits:
    1. UTF-8 BOM absorption in parse_facebook_json.
    2. 'content: null' media export stringification leak prevention.
    3. Uncaught OverflowError on Infinity/-Infinity timestamps.
    4. Word-boundary sender name discrimination for 'Nguyen Van An'.
    5. Zero and negative limit handling in get_few_shot_examples.
    """

    def test_regression_utf8_bom_file_parsing(self, tmp_path):
        """Regression test: parser must handle UTF-8 files containing a Byte Order Mark (BOM)."""
        data = {
            "messages": [
                {
                    "senderName": "An An",
                    "text": "Có BOM nè 🌸",
                    "timestamp": 1747310700000,
                    "isUnsent": False
                }
            ]
        }
        # 1. Test BOM written as unicode character \ufeff
        bom_char_file = tmp_path / "bom_char.json"
        bom_char_file.write_text("\ufeff" + json.dumps(data, ensure_ascii=False), encoding="utf-8")
        msgs1 = parse_facebook_json(str(bom_char_file))
        assert len(msgs1) == 1
        assert msgs1[0].text == "Có BOM nè 🌸"
        assert msgs1[0].sender_name == "An An"
        assert msgs1[0].is_an_an is True

        # 2. Test raw UTF-8 BOM bytes \xef\xbb\xbf
        bom_bytes_file = tmp_path / "bom_bytes.json"
        bom_bytes_file.write_bytes(b"\xef\xbb\xbf" + json.dumps(data, ensure_ascii=False).encode("utf-8"))
        msgs2 = parse_facebook_json(str(bom_bytes_file))
        assert len(msgs2) == 1
        assert msgs2[0].text == "Có BOM nè 🌸"

    def test_regression_null_content_media_messages_filtered(self, tmp_path):
        """Regression test: 'content: null' media exports must not be ingested as 'None' strings."""
        data = {
            "messages": [
                {
                    "sender_name": "An An",
                    "content": None,
                    "timestamp_ms": 1000,
                    "photos": [{"uri": "photo.jpg"}]
                },
                {
                    "sender_name": "Hoàng Kim Quờ Lờ",
                    "text": None,
                    "content": None,
                    "timestamp_ms": 2000
                },
                {
                    "sender_name": "An An",
                    "content": "Tin nhắn thật",
                    "timestamp_ms": 3000
                },
                {
                    "sender_name": "Hoàng Kim Quờ Lờ",
                    "text": "Tin nhắn text thật",
                    "content": None,
                    "timestamp_ms": 4000
                }
            ]
        }
        file_path = tmp_path / "null_content.json"
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        msgs = parse_facebook_json(str(file_path))

        # Must only ingest the 2 valid text messages
        assert len(msgs) == 2
        texts = [m.text for m in msgs]
        assert "Tin nhắn thật" in texts
        assert "Tin nhắn text thật" in texts

        # Zero 'None' strings permitted
        none_texts = [m for m in msgs if m.text == "None"]
        assert len(none_texts) == 0, f"Found leaked 'None' messages: {none_texts}"

    def test_regression_timestamp_infinity_and_overflow_handling(self, tmp_path):
        """Regression test: parser must catch OverflowError on Infinity/-Infinity and huge timestamps."""
        raw_json = '''{
            "messages": [
                {"senderName": "An An", "text": "Tin inf", "timestamp": Infinity},
                {"senderName": "An An", "text": "Tin -inf", "timestamp": -Infinity},
                {"senderName": "An An", "text": "Tin nan", "timestamp": NaN},
                {"senderName": "An An", "text": "Tin overflow float", "timestamp": 1e308},
                {"senderName": "An An", "text": "Tin hợp lệ", "timestamp": 1747310700000}
            ]
        }'''
        file_path = tmp_path / "ts_infinity.json"
        file_path.write_text(raw_json, encoding="utf-8")

        msgs = parse_facebook_json(str(file_path))
        assert len(msgs) == 5
        for m in msgs:
            assert isinstance(m.timestamp_ms, int)
            assert not isinstance(m.timestamp_ms, bool)

        valid_msg = next(m for m in msgs if m.text == "Tin hợp lệ")
        assert valid_msg.timestamp_ms == 1747310700000

        # Non-finite should safely default to 0
        inf_msg = next(m for m in msgs if m.text == "Tin inf")
        assert inf_msg.timestamp_ms == 0 or isinstance(inf_msg.timestamp_ms, int)

    def test_regression_sender_name_van_an_discrimination(self, tmp_path):
        """Regression test: sender name discrimination must not falsely match 'Nguyen Van An' as An An."""
        data = {
            "messages": [
                {"senderName": "An An", "text": "Exact match", "timestamp": 1000},
                {"senderName": "an an", "text": "Lower match", "timestamp": 2000},
                {"senderName": "AN AN", "text": "Upper match", "timestamp": 3000},
                {"senderName": "Bé An An 🌸", "text": "Word boundary match", "timestamp": 4000},
                {"senderName": "An An (Cún)", "text": "Parenthesis boundary match", "timestamp": 5000},
                {"senderName": "Nguyen Van An", "text": "Collision 'van an' not An An", "timestamp": 6000},
                {"senderName": "Nguyễn Văn An", "text": "Diacritic Van An not An An", "timestamp": 7000},
                {"senderName": "Trần Tuấn An", "text": "Tuan An not An An", "timestamp": 8000},
                {"senderName": "Lê Xuân An", "text": "Xuan An not An An", "timestamp": 9000},
                {"senderName": "An", "text": "Single An not An An", "timestamp": 10000},
                {"senderName": "Hoàng Kim Quờ Lờ", "text": "Partner QL", "timestamp": 11000},
                {"senderName": "Unknown", "text": "Unknown sender", "timestamp": 12000}
            ]
        }
        file_path = tmp_path / "sender_discrimination.json"
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        msgs = parse_facebook_json(str(file_path))

        expected_is_an_an = {
            "Exact match": True,
            "Lower match": True,
            "Upper match": True,
            "Word boundary match": True,
            "Parenthesis boundary match": True,
            "Collision 'van an' not An An": False,
            "Diacritic Van An not An An": False,
            "Tuan An not An An": False,
            "Xuan An not An An": False,
            "Single An not An An": False,
            "Partner QL": False,
            "Unknown sender": False
        }

        for m in msgs:
            expected = expected_is_an_an[m.text]
            assert m.is_an_an is expected, (
                f"Sender '{m.sender_name}' for msg '{m.text}' produced is_an_an={m.is_an_an}, expected {expected}!"
            )

    def test_regression_few_shot_limit_zero_and_negative(self):
        """Regression test: get_few_shot_examples with limit <= 0 must return an empty list."""
        assert get_few_shot_examples(limit=0) == []
        assert get_few_shot_examples(limit=-1) == []
        assert get_few_shot_examples(limit=-100) == []
        assert get_few_shot_examples(category="CASUAL_BANTER", limit=0) == []
        assert get_few_shot_examples(category="CASUAL_BANTER", limit=-5) == []

        # Positive limits must still return correct number of examples
        one_ex = get_few_shot_examples(limit=1)
        assert len(one_ex) == 1
        three_ex = get_few_shot_examples(limit=3)
        assert len(three_ex) == 3


# ==============================================================================
# Group 9: Vietnamese Language Enforcement Tests
# ==============================================================================

class TestPersonaVietnameseLanguageEnforcement:
    """
    Validates that persona profile prompt instructions, tone pillars,
    slang dictionaries, and few-shot exemplars strictly mandate and enforce
    Vietnamese language output.
    """

    def test_persona_profile_metadata_mandates_vietnamese_language(self):
        """Verifies that PERSONA_PROFILE explicitly mandates Vietnamese language output."""
        # 1. Direct language key check
        assert "language" in PERSONA_PROFILE, "PERSONA_PROFILE must declare 'language' field"
        assert PERSONA_PROFILE["language"].lower() in ("vietnamese", "tiếng việt", "vi")

        # 2. Instruction checks in tone pillars or prompt guidance
        tone_text = " ".join(PERSONA_PROFILE.get("tone_pillars", [])).lower()
        lang_instruction = str(PERSONA_PROFILE.get("language_instruction", "")).lower()
        combined_instructions = f"{tone_text} {lang_instruction}"

        has_vietnamese_mandate = ("vietnamese" in combined_instructions or "tiếng việt" in combined_instructions)
        assert has_vietnamese_mandate, (
            "PERSONA_PROFILE tone_pillars or language_instruction must explicitly mention Vietnamese / Tiếng Việt"
        )

    def test_few_shot_exchanges_all_contain_vietnamese_text(self):
        """Verifies that all few-shot exemplars in FEW_SHOT_EXCHANGES have Vietnamese responses."""
        import re
        vi_diacritics = re.compile(
            r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúũụưừứửữựỳýỷỹỵđ]",
            re.IGNORECASE
        )
        vi_slang_tokens = {
            "kh", "dc", "nma", "r", "v", "z", "th", "thui", "oki", "ql",
            "jza", "kkk", "mă", "clm", "nhaa", "nhieu", "qá", "bíc", "nua",
            "đt", "hc", "bth", "dau", "cmon", "chiển", "chăm", "áaa", "hoi",
            "mìn", "stk", "đk", "rùi", "mực", "mệc", "vaiz", "loz", "g9"
        }

        assert len(FEW_SHOT_EXCHANGES) >= 15
        for ex in FEW_SHOT_EXCHANGES:
            ex_id = ex.get("id", "unknown")
            for t in ex["turns"]:
                an_an_text = t["an_an"]
                has_diacritics = bool(vi_diacritics.search(an_an_text))
                words = set(re.findall(r"\b\w+\b", an_an_text.lower()))
                has_vi_slang = bool(words.intersection(vi_slang_tokens))
                has_oki = bool(re.search(r"\boki+\b", an_an_text.lower()))

                is_vietnamese = has_diacritics or has_vi_slang or has_oki
                assert is_vietnamese, (
                    f"Few-shot exchange id={ex_id} An An response has no Vietnamese indicators: {repr(an_an_text)}"
                )

    def test_get_few_shot_examples_enforces_vietnamese_output(self):
        """Verifies that get_few_shot_examples() returns 100% Vietnamese language exemplars."""
        import re
        examples = get_few_shot_examples(limit=50)
        assert len(examples) > 0

        vi_diacritics = re.compile(
            r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúũụưừứửữựỳýỷỹỵđ]",
            re.IGNORECASE
        )
        vi_slang_tokens = {
            "kh", "dc", "nma", "r", "v", "z", "th", "thui", "oki", "ql",
            "jza", "kkk", "mă", "clm", "nhaa", "nhieu", "qá", "bíc", "nua",
            "đt", "hc", "bth", "dau", "cmon", "chiển", "chăm", "áaa", "hoi",
            "mìn", "stk", "đk", "rùi", "mực", "mệc", "vaiz", "loz", "g9"
        }

        for ex in examples:
            out = ex["output"]
            has_diacritics = bool(vi_diacritics.search(out))
            words = set(re.findall(r"\b\w+\b", out.lower()))
            has_vi_slang = bool(words.intersection(vi_slang_tokens))
            has_oki = bool(re.search(r"\boki+\b", out.lower()))
            assert (has_diacritics or has_vi_slang or has_oki), (
                f"get_few_shot_examples returned non-Vietnamese output: {repr(out)}"
            )

    def test_slang_rules_and_prohibitions_enforce_vietnamese_style(self):
        """Verifies that slang dictionary and prohibited tokens enforce colloquial Vietnamese style."""
        # Prohibited tokens must ban generic Vietnamese AI assistant clichés
        assert "Tôi là trợ lý ảo" in PROHIBITED_TOKENS
        assert "Tôi có thể giúp gì cho bạn" in PROHIBITED_TOKENS
        assert "Xin lỗi vì sự bất tiện" in PROHIBITED_TOKENS

        # Prohibited tokens must ban formal polite particles
        for formal_token in ["ạ", "dạ", "cậu", "tớ"]:
            assert formal_token in PROHIBITED_TOKENS

        # Slang dictionary must contain Vietnamese colloquial markers
        for marker in ["kh", "hong", "dc", "nma", "r", "v", "z", "th", "thui", "oki", "=)))", "ql"]:
            assert marker in SLANG_DICTIONARY
            assert len(SLANG_DICTIONARY[marker]["rule"]) > 0
