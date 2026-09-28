# Milestone M1 Unit Test Specification: `tests/test_ingestion.py`

**Milestone:** M1 (Dependencies & Data Ingestion Engine)  
**Target Test File:** `tests/test_ingestion.py`  
**Test Runner:** `pytest` (`.\venv\Scripts\python.exe -m pytest tests/test_ingestion.py -v`)  
**Specification Miner:** `spec_miner_m1_3`  
**Date:** 2026-09-14  
**Authoritative Sources:** `ORIGINAL_REQUEST.md`, `PROJECT.md`, `TEST_INFRA.md`, `.agents/spec_miner_survey_3/spec_requirements.md`, `F:/dowload/FacebookData/messages/An An_86.json`

---

## 1. Executive Summary & Test Suite Objectives

Milestone M1 delivers the foundational data ingestion pipeline for the An An Persona Chatbot. The ingestion engine is responsible for parsing raw Facebook Messenger JSON files, performing safe transcoding (avoiding Windows CP1252/Latin-1 `UnicodeEncodeError` traps), filtering noise (unsent messages, placeholder texts, failed downloads), and profiling An An's persona (linguistic statistics, length distributions, teen-code token frequencies, dialogue pairs).

This document provides the exhaustive specification for `tests/test_ingestion.py`, covering:
1. **Happy Path Parsing:** Real data verification with `An An_86.json` (participants, counts, chronological ordering).
2. **Safe Transcoding & Mojibake Repair:** Zero `UnicodeEncodeError` across native Vietnamese UTF-8, Latin-1 double-encoded text, and emojis.
3. **Message Filtering:** Precision exclusion of unsent messages, `"Failed to download media"` artifacts, empty texts, and system placeholders.
4. **Persona Profiling:** Empirical verification of word length distributions (70% Short, 27.6% Medium, 2.4% Long), token frequencies (`kh`, `dc`, `nma`, `r`, `=)))`, `🤡`), and dialogue pair extraction ($\ge 380$ pairs).
5. **Fault Tolerance & Edge Cases:** Non-existent files, malformed JSON, 0-byte files, empty messages array, missing fields, single-participant chats.

---

## 2. Interface Contracts Under Test

The test suite exercises the following public interfaces defined in `PROJECT.md` and `spec_requirements.md`:

```python
# Location: src/ingestion/parser.py
from pydantic import BaseModel
from typing import List, Optional, Any

class CanonicalMessage(BaseModel):
    sender_name: str
    text: str
    timestamp_ms: int
    is_an_an: bool
    reactions: List[str] = []
    is_unsent: bool = False
    media: List[Any] = []
    msg_type: str = "text"

def safe_decode_mojibake(text: Optional[str]) -> str:
    """Safely repairs double-encoded Latin-1 mojibake without crashing on native UTF-8."""
    ...

def parse_facebook_json(file_path: str) -> List[CanonicalMessage]:
    """Parses Facebook JSON (modern or standard export), sorts chronologically, filters noise."""
    ...

# Location: src/ingestion/persona_profile.py
def extract_an_an_profile(messages: List[CanonicalMessage]) -> dict:
    """Extracts linguistic stats, word length distributions, token frequencies, and dialogue pairs."""
    ...
```

### Expected Return Structure of `extract_an_an_profile`
```python
{
    "stats": {
        "total_messages": int,
        "an_an_messages": int,
        "user_messages": int,
        "an_an_ratio": float, # e.g. 0.575
        "length_distribution": {
            "short_count": int,
            "short_pct": float,   # ~0.700 (70.0%)
            "medium_count": int,
            "medium_pct": float,  # ~0.276 (27.6%)
            "long_count": int,
            "long_pct": float,    # ~0.024 (2.4%)
            "mean_words": float,  # ~4.7
            "median_words": float # ~4.0
        }
    },
    "token_frequencies": {
        "kh": int,   # >= 100
        "dc": int,   # >= 30
        "nma": int,  # >= 25
        "r": int,    # >= 75
        "=)))": int, # >= 50
        "🤡": int,   # >= 10
        "ql": int,   # >= 30
        "k": int,    # == 0
        "đc": int,   # == 0
        "nhma": int  # == 0
    },
    "dialogue_pairs": [
        {
            "user_input": str,       # e.g. "Chúc An mai thi tốt"
            "an_an_response": str    # e.g. "Cám mơn ql nhieu nhaa"
        },
        ...
    ]
}
```

---

## 3. Test Fixtures Specification

The test suite must define both standalone synthetic fixtures (for fast, isolated unit tests) and a path resolver for the primary verification dataset (`F:/dowload/FacebookData/messages/An An_86.json`).

### Fixture 1: `real_sample_json_path`
```python
@pytest.fixture
def real_sample_json_path():
    primary_path = Path("F:/dowload/FacebookData/messages/An An_86.json")
    if primary_path.exists():
        return str(primary_path)
    pytest.skip("Primary verification dataset F:/dowload/FacebookData/messages/An An_86.json not found on host.")
```

### Fixture 2: `synthetic_modern_fb_json(tmp_path)`
Generates a temporary modern schema JSON file (`senderName`, `text`, `timestamp`, `isUnsent`, `reactions`).
```python
@pytest.fixture
def synthetic_modern_fb_json(tmp_path):
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
```

### Fixture 3: `synthetic_standard_fb_json(tmp_path)`
Generates a standard Facebook export schema JSON file (`sender_name`, `content`, `timestamp_ms`, `is_unsent`).
```python
@pytest.fixture
def synthetic_standard_fb_json(tmp_path):
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
```

### Fixture 4: `dirty_filter_fb_json(tmp_path)`
Contains unsent messages, media attachments with `"Failed to download media"`, empty messages, and call logs.
```python
@pytest.fixture
def dirty_filter_fb_json(tmp_path):
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
```

---

## 4. Comprehensive Test Case Specifications

### 4.1 Group 1: Safe Transcoding & Mojibake Repair (`TestSafeMojibakeDecoder`)

| # | Test Function Name | Input | Expected Output | Critical Assertion |
|---|-------------------|-------|-----------------|-------------------|
| 1 | `test_transcode_native_utf8_vietnamese_pass_through` | `"Chào An An, bạn có ở đó không? Đi uống cà phê nhờ! 🌸"` (contains `ờ` U+1EDD, `ở` U+1EDF, `đ` U+0111) | Returns identical string | Zero `UnicodeEncodeError`, string is untouched |
| 2 | `test_transcode_latin1_double_encoded_mojibake_repaired` | `"C\u00c3\u00a1m m\u00c6\u00a1n ql nhieu nhaa"` (`CÃ¡m mÆ¡n ql nhieu nhaa`) | `"Cám mơn ql nhieu nhaa"` | Decodes double-encoded Latin-1 to clean Vietnamese |
| 3 | `test_transcode_latin1_common_vietnamese_phrases` | `"Ch\u00c3\u00a0o b\u00e1\u00ba\u00a1n"` (`ChÃ o b\u00e1\u00ba\u00a1n`) | `"Chào bạn"` | Correct repair of vowels with accents |
| 4 | `test_transcode_mixed_latin1_and_native_unicode` | `"Chào An \u00c3\u00a1 \u1edd"` | Safe string without exception | Handles mixed strings gracefully without raising `UnicodeEncodeError` |
| 5 | `test_transcode_emojis_and_emoticons_intact` | `"Quỉ=))) 🤡 ❤ 👌 💪 ☺ 🥲 😭 ☕"` | Returns identical string | No emoji corruption, surrogate pairs handled cleanly |
| 6 | `test_transcode_ascii_and_punctuation` | `"Hello world 12345! @#$%^&*()_+"` | Returns identical string | ASCII untouched |
| 7 | `test_transcode_empty_and_falsy_inputs` | `""`, `None`, whitespace `"   "` | `""` or trimmed | Returns empty string safely without error |
| 8 | `test_transcode_non_string_types` | `123`, `45.6`, `[]`, `{}` | `""` or `str` conversion | Does not throw `AttributeError` or `TypeError` |

#### Detailed Implementation Logic for Group 1
```python
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
        # Native \u1edd (Latin-1 encode fails) mixed with mojibake
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
```

---

### 4.2 Group 2: Happy Path Facebook JSON Parsing (`TestFacebookJsonParserHappyPath`)

| # | Test Function Name | Input | Expected Output | Critical Assertion |
|---|-------------------|-------|-----------------|-------------------|
| 9 | `test_parse_real_an_an_file_loads_successfully` | `An An_86.json` (2,102 raw messages) | Returns `List[CanonicalMessage]` | List length $> 2000$; elements are `CanonicalMessage` |
| 10 | `test_parse_real_an_an_message_count` | `An An_86.json` | 2,032 to 2,087 valid messages | Exactly 15 unsent messages excluded |
| 11 | `test_parse_real_an_an_participants_and_senders` | `An An_86.json` | Senders: `'An An'` and `'Hoàng Kim Quờ Lờ'` | Senders set contains exactly the two participants |
| 12 | `test_parse_real_an_an_sender_distribution` | `An An_86.json` | An An count $\approx 1200$; QL count $\approx 887$ | Ratio matches empirical chat log |
| 13 | `test_parse_real_an_an_chronological_ordering` | `An An_86.json` | Strictly ascending timestamps | `msg[i].timestamp_ms <= msg[i+1].timestamp_ms` for all $i$ |
| 14 | `test_parse_is_an_an_flag_correctness` | `An An_86.json` | `msg.is_an_an` boolean flag | `msg.is_an_an is True` $\iff$ `sender_name == 'An An'` |
| 15 | `test_parse_modern_tool_schema_fixture` | `synthetic_modern_fb_json` | 2 valid canonical messages | Unsent message dropped; fields mapped correctly |
| 16 | `test_parse_standard_fb_export_schema_fixture` | `synthetic_standard_fb_json` | 2 valid canonical messages | `content` mapped to `text`, `timestamp_ms` mapped correctly |
| 17 | `test_parse_reactions_extraction` | Message with reaction `❤` | `msg.reactions == ["❤"]` | Reactions extracted cleanly as string list |

#### Detailed Implementation Logic for Group 2
```python
class TestFacebookJsonParserHappyPath:
    def test_parse_real_an_an_file_loads_successfully(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        assert isinstance(messages, list)
        assert len(messages) > 2000
        assert all(isinstance(m, CanonicalMessage) for m in messages)

    def test_parse_real_an_an_message_count(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        # 2102 total - 15 unsent - empty media = 2032 to 2087
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
        assert 860 <= ql_count <= 895

    def test_parse_real_an_an_chronological_ordering(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        for i in range(len(messages) - 1):
            assert messages[i].timestamp_ms <= messages[i+1].timestamp_ms, (
                f"Messages out of order at index {i}: {messages[i].timestamp_ms} > {messages[i+1].timestamp_ms}"
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
        assert messages[1].sender_name == "An An"
        assert messages[1].text == "Cám mơn ql nhieu nhaa"

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
```

---

### 4.3 Group 3: Message Filtering & Noise Suppression (`TestMessageFiltering`)

| # | Test Function Name | Input | Expected Output | Critical Assertion |
|---|-------------------|-------|-----------------|-------------------|
| 18 | `test_filter_unsent_messages_boolean_flag` | Message with `isUnsent: True` or `is_unsent: True` | Dropped from output | Excluded from returned messages |
| 19 | `test_filter_unsent_placeholder_text` | Message with text `"User unsent a message"` | Dropped even if `isUnsent: False` | Unsent placeholder text never reaches persona or chain |
| 20 | `test_filter_failed_to_download_media` | Message with text containing `"Failed to download media"` | Dropped from output | Artifact excluded |
| 21 | `test_filter_empty_and_whitespace_messages` | Messages with `text: ""` or `text: "   \n\t "` | Dropped from output | Empty strings excluded from dialogue |
| 22 | `test_filter_system_call_events` | Messages with `type: "call"` or text `"missed a call"` | Dropped from output | Call notifications excluded |
| 23 | `test_dirty_fixture_filtering_accuracy` | `dirty_filter_fb_json` (7 raw messages: 4 dirty, 3 valid) | Exactly 3 valid messages returned | `"Hợp lệ 1"`, `"Hợp lệ 2"`, `"Hợp lệ 3"` retained in order |

#### Detailed Implementation Logic for Group 3
```python
class TestMessageFiltering:
    def test_dirty_fixture_filtering_accuracy(self, dirty_filter_fb_json):
        messages = parse_facebook_json(dirty_filter_fb_json)
        assert len(messages) == 3
        texts = [m.text for m in messages]
        assert texts == ["Hợp lệ 1", "Hợp lệ 2", "Hợp lệ 3"]

    def test_filter_unsent_placeholder_text(self, tmp_path):
        data = {
            "participants": ["A", "An An"],
            "messages": [
                {"senderName": "A", "text": "Hello", "timestamp": 1, "isUnsent": False},
                {"senderName": "A", "text": "User unsent a message", "timestamp": 2, "isUnsent": False}
            ]
        }
        file_path = tmp_path / "unsent.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")
        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 1
        assert messages[0].text == "Hello"

    def test_filter_failed_to_download_media(self, tmp_path):
        data = {
            "participants": ["A", "An An"],
            "messages": [
                {"senderName": "An An", "text": "Failed to download media", "timestamp": 1, "isUnsent": False},
                {"senderName": "An An", "text": "Jza", "timestamp": 2, "isUnsent": False}
            ]
        }
        file_path = tmp_path / "failed_media.json"
        file_path.write_text(json.dumps(data), encoding="utf-8")
        messages = parse_facebook_json(str(file_path))
        assert len(messages) == 1
        assert messages[0].text == "Jza"
```

---

### 4.4 Group 4: Persona Profiling & Empirical Distributions (`TestPersonaProfiling`)

| # | Test Function Name | Input | Expected Output | Critical Assertion |
|---|-------------------|-------|-----------------|-------------------|
| 24 | `test_profile_overall_stats_counts` | Canonical messages from `An An_86.json` | Correct message totals | `total_messages >= 2030`, `an_an_messages >= 1170`, `user_messages >= 860` |
| 25 | `test_profile_length_distribution_short_ratio` | An An messages from `An An_86.json` | $\approx 70.0\%$ short ($\le 5$ words) | $68.0\% \le short\_pct \le 72.0\%$ |
| 26 | `test_profile_length_distribution_medium_ratio` | An An messages from `An An_86.json` | $\approx 27.6\%$ medium ($6-15$ words) | $25.0\% \le medium\_pct \le 30.0\%$ |
| 27 | `test_profile_length_distribution_long_ratio` | An An messages from `An An_86.json` | $\approx 2.4\%$ long ($> 15$ words) | $1.5\% \le long\_pct \le 3.5\%$ |
| 28 | `test_profile_word_mean_and_median` | An An messages from `An An_86.json` | Mean $\approx 4.7$ words, Median $\approx 4.0$ words | $4.2 \le mean \le 5.2$, $3.0 \le median \le 5.0$ |
| 29 | `test_profile_signature_token_kh` | An An messages | Frequency of `kh` $\ge 100$ | Actual empirical count: 143 |
| 30 | `test_profile_signature_token_dc` | An An messages | Frequency of `dc` $\ge 30$ | Actual empirical count: 42 |
| 31 | `test_profile_signature_token_nma` | An An messages | Frequency of `nma` $\ge 25$ | Actual empirical count: 36 |
| 32 | `test_profile_signature_token_r` | An An messages | Frequency of `r` $\ge 75$ | Actual empirical count: 100 |
| 33 | `test_profile_signature_token_laugh_and_emoji` | An An messages | Frequency of `=)))` $\ge 50$, `🤡` $\ge 10$ | Actual empirical: 75 `=)))`, 14 `🤡` |
| 34 | `test_profile_signature_token_ql` | An An messages | Frequency of `ql` $\ge 30$ | Actual empirical: 40 |
| 35 | `test_profile_anti_pattern_tokens_banned` | An An messages | Frequencies of `k == 0`, `đc == 0`, `nhma == 0` | Strictly 0 occurrences of forbidden spelling |

#### Detailed Implementation Logic for Group 4
```python
class TestPersonaProfiling:
    def test_profile_overall_stats_counts(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        stats = profile.get("stats", {})
        assert stats.get("total_messages", len(messages)) >= 2030
        assert stats.get("an_an_messages", 0) >= 1170
        assert stats.get("user_messages", 0) >= 860

    def test_profile_length_distribution_ratios(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        ld = profile.get("stats", {}).get("length_distribution", profile.get("length_distribution", {}))
        
        short_pct = ld.get("short_pct", 0.0)
        med_pct = ld.get("medium_pct", 0.0)
        long_pct = ld.get("long_pct", 0.0)
        
        # Tolerances around empirical ground truth (70.0%, 27.6%, 2.4%)
        assert 0.67 <= short_pct <= 0.73, f"Short ratio {short_pct} outside [0.67, 0.73]"
        assert 0.25 <= med_pct <= 0.31, f"Medium ratio {med_pct} outside [0.25, 0.31]"
        assert 0.01 <= long_pct <= 0.04, f"Long ratio {long_pct} outside [0.01, 0.04]"

    def test_profile_signature_token_frequencies(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        tokens = profile.get("token_frequencies", profile.get("tokens", {}))
        
        assert tokens.get("kh", 0) >= 100
        assert tokens.get("dc", 0) >= 30
        assert tokens.get("nma", 0) >= 25
        assert tokens.get("r", 0) >= 75
        assert tokens.get("=)))", 0) >= 50
        assert tokens.get("🤡", 0) >= 10
        assert tokens.get("ql", 0) >= 30

    def test_profile_anti_pattern_tokens_banned(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        tokens = profile.get("token_frequencies", profile.get("tokens", {}))
        
        assert tokens.get("k", 0) == 0, "An An never uses isolated 'k'"
        assert tokens.get("đc", 0) == 0, "An An never uses 'đc' (always 'dc')"
        assert tokens.get("nhma", 0) == 0, "An An never uses 'nhma' (always 'nma')"
```

---

### 4.5 Group 5: Dialogue Pair Extraction & Turn Collapsing (`TestDialoguePairExtraction`)

| # | Test Function Name | Input | Expected Output | Critical Assertion |
|---|-------------------|-------|-----------------|-------------------|
| 36 | `test_extract_dialogue_pairs_total_count` | Canonical messages from `An An_86.json` | $\ge 380$ dialogue pairs | Empirical count: 392 - 410 pairs |
| 37 | `test_extract_dialogue_pairs_turn_aggregation` | Rapid bursts by User: `["Chúc thi tốt", "cố lên"]` | Collapsed to single `user_input` | Burst joined with `\n` or newline separator |
| 38 | `test_extract_dialogue_pairs_ground_truth_turn_0` | `An An_86.json` | Pair 0 matches conversation | User: `"Chúc An mai thi tốt"`, An An: `"Cám mơn ql nhieu nhaa"` |
| 39 | `test_extract_dialogue_pairs_ground_truth_turn_1` | `An An_86.json` | Pair 1 matches conversation | User: `"tự tin lên cố lên 💪"`, An An: `"Jza"` |
| 40 | `test_extract_dialogue_pairs_few_shot_structure` | `profile["dialogue_pairs"]` | Valid schema | Every pair has `user_input` (str) and `an_an_response` (str) |

#### Detailed Implementation Logic for Group 5
```python
class TestDialoguePairExtraction:
    def test_extract_dialogue_pairs_total_count(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        pairs = profile.get("dialogue_pairs", profile.get("pairs", []))
        assert len(pairs) >= 380, f"Expected >= 380 dialogue pairs, got {len(pairs)}"

    def test_extract_dialogue_pairs_ground_truth_sample(self, real_sample_json_path):
        messages = parse_facebook_json(real_sample_json_path)
        profile = extract_an_an_profile(messages)
        pairs = profile.get("dialogue_pairs", profile.get("pairs", []))
        
        pair_0 = pairs[0]
        assert "Chúc An mai thi tốt" in pair_0["user_input"]
        assert "Cám mơn ql nhieu nhaa" in pair_0["an_an_response"]

        pair_1 = pairs[1]
        assert "tự tin lên cố lên" in pair_1["user_input"]
        assert "Jza" in pair_1["an_an_response"]

    def test_extract_dialogue_pairs_turn_burst_collapsing(self, tmp_path):
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
```

---

### 4.6 Group 6: Fault Tolerance & Edge Cases (`TestFaultToleranceAndEdgeCases`)

| # | Test Function Name | Input | Expected Output | Critical Assertion |
|---|-------------------|-------|-----------------|-------------------|
| 41 | `test_fault_tolerance_non_existent_file` | `"non_existent_12345.json"` | Raises `FileNotFoundError` | Informative error without unhandled crash |
| 42 | `test_fault_tolerance_malformed_json_syntax` | Broken JSON (`{"participants": [ ` unclosed) | Raises `ValueError` or `json.JSONDecodeError` | Clean failure on corrupt file |
| 43 | `test_fault_tolerance_empty_file_zero_bytes` | 0-byte file | Raises `ValueError` or `json.JSONDecodeError` | Does not hang or return invalid object |
| 44 | `test_fault_tolerance_empty_messages_array` | `{"messages": [], "participants": ["A"]}` | Parser returns `[]` | Empty message list returned safely |
| 45 | `test_profile_empty_messages_zero_division_safe` | `messages = []` passed to `extract_an_an_profile` | Safe empty profile dict | Zero `ZeroDivisionError`, returns `0` counts and `0.0` ratios |
| 46 | `test_messages_missing_optional_fields` | Messages lacking `reactions`, `media`, `isUnsent` | Handled with default values | No `KeyError` or schema validation crash |
| 47 | `test_single_participant_chat_pairs` | Messages from only 1 participant (no interlocutor) | `dialogue_pairs == []` | Returns empty pairs list without error |
| 48 | `test_reverse_chronological_input_sorting` | Messages in descending timestamp order | Returned messages in ascending order | Parser re-sorts messages chronologically |
| 49 | `test_extreme_large_message_burst` | 50 sequential bubbles by same sender | Collapsed into 1 turn without stack overflow | Performance remains $< 100$ms |

#### Detailed Implementation Logic for Group 6
```python
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
```

---

## 5. Features Discovered & Probed Matrix

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Ingestion | Schema Auto-Detection | Supports modern schema (`senderName`/`text`/`timestamp`) and standard schema (`sender_name`/`content`/`timestamp_ms`). | File path (str) | `List[CanonicalMessage]` | Missing fields default safely; unknown keys ignored | Inspection of `An An_86.json` vs FB standard dump |
| 2 | Ingestion | Safe Transcoder Guard | Heuristic transcoding guard preventing Windows Latin-1 `UnicodeEncodeError` on native Vietnamese (`\u1edd`, `\u01a1`). | Raw string (str) | Clean UTF-8 string (str) | Catches `(UnicodeEncodeError, UnicodeDecodeError)` and preserves input | Direct probe of Python 3.14 cp1252 crash on `An An_86.json` |
| 3 | Ingestion | Unsent Message Cleaner | Filters out messages where `isUnsent: True` or text is `"User unsent a message"`. | Raw JSON messages | Filtered `CanonicalMessage` list | Silently drops unsent entries | Empirical finding: 15 unsent messages in `An An_86.json` |
| 4 | Ingestion | Failed Media Cleaner | Filters out messages where text contains `"Failed to download media"`. | Raw JSON messages | Filtered message list | Silently drops failed media | Real FB download artifact probe |
| 5 | Ingestion | Chronological Re-sorter | Guarantees messages are sorted chronologically ascending. | Raw JSON messages | Chronologically sorted `List[CanonicalMessage]` | Stable sort on `timestamp_ms` | Timestamp order verification |
| 6 | Profiling | Length Distribution Analyzer | Calculates empirical word count distribution: Short ($\le 5$), Medium ($6-15$), Long ($> 15$). | `List[CanonicalMessage]` | Distribution dict with counts and percentages | Protects against `ZeroDivisionError` on 0 messages | Dataset analysis: 70.0% short, 27.6% med, 2.4% long |
| 7 | Profiling | Signature Token Tracker | Counts exact occurrences of An An teen-code tokens (`kh`, `dc`, `nma`, `r`, `=)))`, `🤡`, `ql`). | `List[CanonicalMessage]` | Frequency dictionary | Safe word-boundary regex, preserves emojis | Linguistic frequency analysis of 1,174 An An messages |
| 8 | Profiling | Anti-Pattern Verifier | Verifies zero or near-zero occurrences of forbidden slang (`k`, `đc`, `nhma`, `ko`). | `List[CanonicalMessage]` | Frequency dictionary | Flags non-zero counts | Verification of persona quirks in `An An_86.json` |
| 9 | Profiling | Turn Burst Aggregator | Collapses rapid consecutive messages from same sender into logical turns. | `List[CanonicalMessage]` | Aggregated turn list | Single message turns emitted when sender alternates | Burst pattern analysis (average 2.94 bubbles/turn) |
| 10 | Profiling | Dialogue Pair Catalog | Extracts consecutive alternating pairs `(User_Turn, An_An_Turn)` for few-shot prompting. | `List[CanonicalMessage]` | List of dialogue pair dicts ($\ge 380$ pairs) | Returns `[]` if no alternating turns exist | Dialogue turn extraction probe (392-410 pairs found) |

---

## 6. Edge Cases & Boundary Conditions Matrix

| # | Feature | Input | Observed / Required Behavior |
|---|---------|-------|------------------------------|
| 1 | Transcoding | Native Vietnamese with `\u1edd`, `\u01a1`, `\u0111` | Latin-1 encode raises `UnicodeEncodeError`; caught by exception guard, original string returned without error. |
| 2 | Transcoding | Double-encoded Latin-1 (`CÃ¡m mÆ¡n`) | Successfully encoded to Latin-1 bytes and decoded to UTF-8; restored to `"Cám mơn"`. |
| 3 | Transcoding | Pure ASCII and numbers (`Hello 123!`) | Returns exact string without alteration. |
| 4 | Transcoding | Mixed emojis (`🤡`, `❤`, `👌`, `💪`, `=)))`) | Emojis preserved intact without surrogate-pair corruption. |
| 5 | Transcoding | `None`, `""`, or non-string (`123`, `[]`) | Safely returns `""` without throwing `AttributeError`. |
| 6 | Ingestion | File path does not exist on disk | Raises `FileNotFoundError` with clear message. |
| 7 | Ingestion | Broken JSON syntax (unclosed brackets/quotes) | Raises `ValueError` or `json.JSONDecodeError`. |
| 8 | Ingestion | 0-byte file | Raises `ValueError` or `json.JSONDecodeError`. |
| 9 | Ingestion | Valid JSON with `"messages": []` | Returns empty list `[]`. |
| 10 | Ingestion | `reactions: None` or missing `reactions` key | Defaults to empty list `[]`. |
| 11 | Ingestion | Messages in reverse chronological order | Automatically sorted into ascending chronological order. |
| 12 | Ingestion | Message with `type: "placeholder"` or `"call"` | Filtered out from canonical conversational messages. |
| 13 | Profiling | Empty `CanonicalMessage` list passed to `extract_an_an_profile` | Returns valid dictionary with zero counts and 0.0 percentages without `ZeroDivisionError`. |
| 14 | Profiling | Single participant only in chat log | No dialogue pairs form; returns `dialogue_pairs = []` without error. |
| 15 | Profiling | Burst of 50 consecutive messages by same sender | Merged into single turn joined with `\n` without stack overflow or performance degradation. |

---

## 7. Execution & Verification Guide

When `tests/test_ingestion.py` is implemented by the development agent, it must be verified using the virtual environment pytest runner:

```powershell
# Run the complete ingestion unit test suite
.\venv\Scripts\python.exe -m pytest tests/test_ingestion.py -v

# Run with coverage report
.\venv\Scripts\python.exe -m pytest tests/test_ingestion.py -v --cov=src/ingestion

# Run a specific test group
.\venv\Scripts\python.exe -m pytest tests/test_ingestion.py -k "TestSafeMojibakeDecoder" -v
.\venv\Scripts\python.exe -m pytest tests/test_ingestion.py -k "TestFacebookJsonParserHappyPath" -v
.\venv\Scripts\python.exe -m pytest tests/test_ingestion.py -k "TestPersonaProfiling" -v
```

### Pass Criteria
1. **Pass Rate:** 100% pass across all 49 specified unit test cases (exit code 0).
2. **Execution Time:** Entire suite runs offline in $< 3.0$ seconds.
3. **No External Network:** Relies solely on local filesystem and synthetic fixtures without external API calls.
