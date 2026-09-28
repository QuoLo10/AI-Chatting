"""
Empirical Challenge & Stress Test Harness for src/ingestion/parser.py
Challenger 1 (Data Stress Challenger) - Milestone M1
"""

import os
import sys
import time
import json
import math
import tempfile
import traceback
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.parser import (
    CanonicalMessage,
    safe_decode_mojibake,
    fix_fb_text,
    parse_facebook_json,
)


class ChallengeResult:
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.passed = False
        self.severity = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
        self.details = ""
        self.duration_ms = 0.0
        self.exception: Exception = None


class StressTestRunner:
    def __init__(self):
        self.results: List[ChallengeResult] = []

    def record(self, res: ChallengeResult):
        self.results.append(res)
        status = "PASS" if res.passed else f"FAIL [{res.severity}]"
        print(f"[{status}] {res.category} :: {res.name} ({res.duration_ms:.2f}ms)")
        if not res.passed:
            print(f"   -> Details: {res.details}")

    # =========================================================================
    # CATEGORY 1: Mojibake & Encoding Stress (safe_decode_mojibake)
    # =========================================================================
    def test_encoding_native_vietnamese(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Native Vietnamese Vowels & Diacritics", "Encoding")
        sample = (
            "aàảãáạăằẳẵắặâầẩẫấậeèẻẽéẹêềểễếệiìỉĩíịoòỏõóọôồổỗốộơờởỡớợuùủũúụưừửữứựyỳỷỹýỵ "
            "AÀẢÃÁẠĂẰẲẴẮẶÂẦẨẪẤẬEÈẺẼÉẸÊỀỂỄẾỆIÌỈĨÍỊOÒỎÕÓỌÔỒỔỖỐỘƠỜỞỠỚỢUÙỦŨÚỤƯỪỬỮỨỰYỲỶỸÝỴ"
        )
        out = safe_decode_mojibake(sample)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if out == sample:
            res.passed = True
        else:
            res.passed = False
            res.severity = "CRITICAL"
            res.details = f"Corrupted native Vietnamese text: {out[:50]}..."
        self.record(res)

    def test_encoding_nfd_decomposition(self):
        t0 = time.perf_counter()
        res = ChallengeResult("NFD Decomposed Unicode Vowels", "Encoding")
        nfd_sample = "e\u0301 o\u031b\u0300 a\u0306\u0301 u\u031b\u0303"
        out = safe_decode_mojibake(nfd_sample)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if out == nfd_sample:
            res.passed = True
        else:
            res.passed = False
            res.severity = "HIGH"
            res.details = f"NFD decomposition was mutated or raised error: {repr(out)}"
        self.record(res)

    def test_encoding_latin1_mojibake_standard(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Standard Double-Encoded Latin-1 Mojibake", "Encoding")
        raw_mojibake = "C\u00c3\u00a1m m\u00c6\u00a1n ql nhieu nhaa"
        expected = "Cám mơn ql nhieu nhaa"
        out = safe_decode_mojibake(raw_mojibake)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if out == expected:
            res.passed = True
        else:
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Expected '{expected}', got '{out}'"
        self.record(res)

    def test_encoding_latin1_mojibake_emoji(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Double-Encoded 4-Byte Emoji Mojibake", "Encoding")
        emoji_mojibake = "\u00f0\u009f\u0092\u0096"
        expected = "💖"
        out = safe_decode_mojibake(emoji_mojibake)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if out == expected:
            res.passed = True
        else:
            res.passed = False
            res.severity = "MEDIUM"
            res.details = f"Expected '{expected}', got '{out}'"
        self.record(res)

    def test_encoding_mixed_mojibake_and_native(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Mixed Mojibake and Native Unicode String", "Encoding")
        mixed = "C\u00c3\u00a1m mơn An An 🌸"
        out = safe_decode_mojibake(mixed)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if out == mixed:
            res.passed = True
        else:
            res.passed = False
            res.severity = "LOW"
            res.details = f"Unexpected output for mixed string: '{out}'"
        self.record(res)

    def test_encoding_multilingual_scripts(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Multilingual Scripts (CJK, Arabic, Cyrillic, Thai)", "Encoding")
        sample = "你好 こんにちは Привет мир مرحبا بالعالم สวัสดี नमस्ते"
        out = safe_decode_mojibake(sample)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if out == sample:
            res.passed = True
        else:
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Multilingual text corrupted: '{out}'"
        self.record(res)

    def test_encoding_control_chars_and_null_bytes(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Control Chars, Null Bytes, RTL, ZWJ", "Encoding")
        tricky = "Hello\x00World\r\n\t\x0b\x0c\u200b\u200c\u200d\u202eRTL\ufeffBOM"
        out = safe_decode_mojibake(tricky)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if "Hello" in out and "World" in out and "BOM" in out:
            res.passed = True
        else:
            res.passed = False
            res.severity = "MEDIUM"
            res.details = f"Control char handling corrupted text: '{repr(out)}'"
        self.record(res)

    def test_encoding_lone_surrogates(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Lone Unicode Surrogates (U+D800, U+DFFF)", "Encoding")
        surrogate_str = "Surrogate \ud800 test \udfff"
        try:
            out = safe_decode_mojibake(surrogate_str)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = True
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed on lone surrogate: {type(exc).__name__}: {exc}"
        self.record(res)

    def test_encoding_all_latin1_bytes(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Full 0x00-0xFF Byte Spectrum", "Encoding")
        full_spectrum = "".join(chr(i) for i in range(256))
        try:
            out = safe_decode_mojibake(full_spectrum)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = True
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "CRITICAL"
            res.details = f"Crashed on Latin-1 byte spectrum: {type(exc).__name__}: {exc}"
        self.record(res)

    def test_encoding_type_safety(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Non-String & Falsy Type Safety", "Encoding")
        bad_types = [None, "", 0, 123, 45.6, True, False, [], {}, object()]
        failed_cases = []
        for val in bad_types:
            try:
                out = safe_decode_mojibake(val)
                if out != "":
                    failed_cases.append(f"{type(val).__name__} -> {repr(out)} (expected '')")
            except Exception as exc:
                failed_cases.append(f"{type(val).__name__} crashed with {exc}")
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if not failed_cases:
            res.passed = True
        else:
            res.passed = False
            res.severity = "HIGH"
            res.details = "; ".join(failed_cases)
        self.record(res)

    def test_encoding_massive_string_throughput(self):
        t0 = time.perf_counter()
        res = ChallengeResult("10 MB Massive String Processing Throughput", "Encoding")
        chunk = "C\u00c3\u00a1m m\u00c6\u00a1n ql nhieu nhaa! An An rat vui. 🌸 "
        multiplier = (10 * 1024 * 1024) // len(chunk.encode("utf-8"))
        massive_text = chunk * multiplier
        actual_size_mb = len(massive_text.encode("utf-8")) / (1024 * 1024)

        t_start = time.perf_counter()
        out = safe_decode_mojibake(massive_text)
        t_end = time.perf_counter()

        duration = t_end - t_start
        throughput_mb_s = actual_size_mb / duration if duration > 0 else 0
        res.duration_ms = duration * 1000

        if len(out) > 0 and duration < 5.0:
            res.passed = True
            res.details = f"Processed {actual_size_mb:.2f} MB in {duration:.3f}s ({throughput_mb_s:.2f} MB/s)"
        else:
            res.passed = False
            res.severity = "MEDIUM"
            res.details = f"Throughput too low or failed: {duration:.3f}s for {actual_size_mb:.2f} MB"
        self.record(res)

    # =========================================================================
    # CATEGORY 2: File System & JSON Malformation Stress
    # =========================================================================
    def test_file_non_existent(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Non-Existent File Path", "File/JSON")
        try:
            parse_facebook_json("path_that_does_not_exist_987654321.json")
            res.passed = False
            res.severity = "CRITICAL"
            res.details = "Did not raise FileNotFoundError"
        except FileNotFoundError:
            res.passed = True
        except Exception as exc:
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Raised unexpected exception: {type(exc).__name__}: {exc}"
        res.duration_ms = (time.perf_counter() - t0) * 1000
        self.record(res)

    def test_file_is_directory(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Path is Directory instead of File", "File/JSON")
        with tempfile.TemporaryDirectory() as tmp_dir:
            try:
                parse_facebook_json(tmp_dir)
                res.passed = False
                res.severity = "HIGH"
                res.details = "Did not raise error when passing directory path"
            except (PermissionError, IsADirectoryError, ValueError):
                res.passed = True
            except Exception as exc:
                res.passed = False
                res.severity = "MEDIUM"
                res.details = f"Unexpected exception: {type(exc).__name__}: {exc}"
        res.duration_ms = (time.perf_counter() - t0) * 1000
        self.record(res)

    def test_file_empty_and_whitespace(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Empty & Whitespace-Only File", "File/JSON")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write("   \n\t  \r\n")
            path = f.name
        try:
            parse_facebook_json(path)
            res.passed = False
            res.severity = "CRITICAL"
            res.details = "Did not raise ValueError on empty/whitespace file"
        except ValueError:
            res.passed = True
        except Exception as exc:
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Unexpected exception: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        self.record(res)

    def test_file_malformed_json_syntax(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Malformed / Truncated JSON Syntax", "File/JSON")
        malformed_snippets = [
            '{"messages": [',
            '{"messages": [{"text": "hi",}]}',
            '{messages: []}',
            '{"messages": [/* comment */]}',
            '{"messages": unquoted_string}',
        ]
        all_passed = True
        failed = []
        for i, snippet in enumerate(malformed_snippets):
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
                f.write(snippet)
                path = f.name
            try:
                parse_facebook_json(path)
                all_passed = False
                failed.append(f"Snippet {i} did not raise error: {snippet}")
            except ValueError:
                pass
            except Exception as exc:
                all_passed = False
                failed.append(f"Snippet {i} raised unexpected {type(exc).__name__}")
            finally:
                if os.path.exists(path):
                    os.remove(path)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if all_passed:
            res.passed = True
        else:
            res.passed = False
            res.severity = "HIGH"
            res.details = "; ".join(failed)
        self.record(res)

    def test_file_non_dict_root(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Non-Dict Root JSON (array, primitive, null)", "File/JSON")
        bad_roots = [
            '[{"messages": []}]',
            '"just a string"',
            '12345',
            'true',
            'null',
        ]
        all_passed = True
        failed = []
        for root in bad_roots:
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
                f.write(root)
                path = f.name
            try:
                parse_facebook_json(path)
                all_passed = False
                failed.append(f"Root '{root}' did not raise ValueError")
            except ValueError:
                pass
            except Exception as exc:
                all_passed = False
                failed.append(f"Root '{root}' raised unexpected {type(exc).__name__}")
            finally:
                if os.path.exists(path):
                    os.remove(path)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if all_passed:
            res.passed = True
        else:
            res.passed = False
            res.severity = "HIGH"
            res.details = "; ".join(failed)
        self.record(res)

    def test_file_missing_or_invalid_messages_key(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Missing or Non-List 'messages' Field", "File/JSON")
        invalid_schemas = [
            json.dumps({"participants": ["An An"]}),
            json.dumps({"messages": None}),
            json.dumps({"messages": "not a list"}),
            json.dumps({"messages": 12345}),
            json.dumps({"messages": {}}),
        ]
        all_passed = True
        failed = []
        for schema in invalid_schemas:
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
                f.write(schema)
                path = f.name
            try:
                parse_facebook_json(path)
                all_passed = False
                failed.append(f"Schema {schema} did not raise ValueError")
            except ValueError:
                pass
            except Exception as exc:
                all_passed = False
                failed.append(f"Schema {schema} raised unexpected {type(exc).__name__}")
            finally:
                if os.path.exists(path):
                    os.remove(path)
        res.duration_ms = (time.perf_counter() - t0) * 1000
        if all_passed:
            res.passed = True
        else:
            res.passed = False
            res.severity = "HIGH"
            res.details = "; ".join(failed)
        self.record(res)

    def test_file_utf8_bom(self):
        t0 = time.perf_counter()
        res = ChallengeResult("UTF-8 with Byte Order Mark (BOM)", "File/JSON")
        data = {"messages": [{"senderName": "An An", "text": "Có BOM nè", "timestamp": 1000}]}
        content = "\ufeff" + json.dumps(data)
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(content)
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            if len(msgs) == 1 and msgs[0].text == "Có BOM nè":
                res.passed = True
            else:
                res.passed = False
                res.severity = "MEDIUM"
                res.details = f"Failed to parse messages from BOM file: {msgs}"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed on BOM: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_file_deeply_nested_fields(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Deeply Nested Unrelated Objects (150 Levels)", "File/JSON")
        nested = {"level": 0}
        curr = nested
        for i in range(150):
            curr["next"] = {"level": i + 1}
            curr = curr["next"]

        data = {
            "metadata": nested,
            "messages": [
                {"senderName": "An An", "text": "Deep nest test", "timestamp": 1000, "extra": nested}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(data))
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            if len(msgs) == 1:
                res.passed = True
            else:
                res.passed = False
                res.severity = "MEDIUM"
                res.details = f"Failed with deep nest: {msgs}"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed with deep nesting: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    # =========================================================================
    # CATEGORY 3: Schema Corruption & Noise Filtering Stress
    # =========================================================================
    def test_messages_non_dict_elements(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Non-Dict Items in 'messages' Array", "Schema/Filtering")
        data = {
            "messages": [
                None,
                12345,
                "string item",
                ["nested", "list"],
                True,
                False,
                {"senderName": "An An", "text": "Valid message", "timestamp": 1000},
                {}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(data))
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            if len(msgs) == 1 and msgs[0].text == "Valid message":
                res.passed = True
            else:
                res.passed = False
                res.severity = "MEDIUM"
                res.details = f"Expected 1 valid message, got {len(msgs)}"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed on non-dict elements: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_messages_null_content_stringification_bug(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Null Content Stringification (content: null leak)", "Schema/Filtering")
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
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(data))
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            none_leaks = [m for m in msgs if m.text == "None"]
            if none_leaks:
                res.passed = False
                res.severity = "HIGH"
                res.details = (
                    f"VULNERABILITY CONFIRMED: {len(none_leaks)} message(s) ingested with text='None' "
                    f"due to stringification of null content! Total msgs: {len(msgs)}"
                )
            else:
                if len(msgs) == 1 and msgs[0].text == "Tin nhắn thật":
                    res.passed = True
                else:
                    res.passed = False
                    res.severity = "MEDIUM"
                    res.details = f"Expected 1 message, got {len(msgs)}"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed on null content: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_messages_unsent_edge_cases(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Unsent Messages Permutations & String Booleans", "Schema/Filtering")
        data = {
            "messages": [
                {"senderName": "A", "text": "User unsent a message", "timestamp": 1000},
                {"senderName": "A", "text": "  User unsent a message   ", "timestamp": 2000},
                {"senderName": "A", "text": "Valid 1", "timestamp": 3000, "isUnsent": True},
                {"senderName": "A", "text": "Valid 2", "timestamp": 4000, "is_unsent": True},
                {"senderName": "A", "text": "Valid 3", "timestamp": 5000, "isUnsent": False},
                {"senderName": "A", "text": "Valid 4", "timestamp": 6000, "is_unsent": False},
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(data))
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            texts = [m.text for m in msgs]
            if texts == ["Valid 3", "Valid 4"]:
                res.passed = True
            else:
                res.passed = False
                res.severity = "MEDIUM"
                res.details = f"Expected ['Valid 3', 'Valid 4'], got {texts}"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_messages_system_calls_and_placeholders(self):
        t0 = time.perf_counter()
        res = ChallengeResult("System Calls, Placeholders, Media Failures", "Schema/Filtering")
        data = {
            "messages": [
                {"senderName": "A", "text": "Missed a call with An An.", "timestamp": 1000, "type": "call"},
                {"senderName": "A", "text": "YOU MISSED A CALL", "timestamp": 2000},
                {"senderName": "A", "text": "FAILED TO DOWNLOAD MEDIA", "timestamp": 3000},
                {"senderName": "A", "text": "Failed to download media file", "timestamp": 4000},
                {"senderName": "A", "text": "Placeholder notice", "timestamp": 5000, "msg_type": "placeholder"},
                {"senderName": "A", "text": "Real message", "timestamp": 6000, "type": "text"}
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(data))
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            texts = [m.text for m in msgs]
            if texts == ["Real message"]:
                res.passed = True
            else:
                res.passed = False
                res.severity = "MEDIUM"
                res.details = f"Expected ['Real message'], got {texts}"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_timestamp_infinity_overflow_bug(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Timestamp Infinity OverflowError Crash", "Schema/Filtering")
        data_str = '{"messages": [{"senderName": "An An", "text": "Test inf", "timestamp": Infinity}]}'
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(data_str)
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = True
            res.details = f"Parsed safely with timestamp_ms={msgs[0].timestamp_ms}"
        except OverflowError as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = (
                f"VULNERABILITY CONFIRMED: int(raw_ts) crashed with uncaught OverflowError on Infinity! "
                f"Line 140 only catches (ValueError, TypeError)."
            )
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "MEDIUM"
            res.details = f"Unexpected error: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_timestamp_various_formats(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Timestamp Formats (float, str, negative, huge)", "Schema/Filtering")
        data = {
            "messages": [
                {"senderName": "A", "text": "Float ts", "timestamp": 1747310703021.99},
                {"senderName": "A", "text": "Str ts", "timestamp": "1747310703050"},
                {"senderName": "A", "text": "Negative ts", "timestamp": -5000},
                {"senderName": "A", "text": "Invalid str ts", "timestamp": "not_a_ts"},
                {"senderName": "A", "text": "None ts", "timestamp": None, "timestamp_ms": None},
                {"senderName": "A", "text": "Huge ts", "timestamp": 999999999999999999},
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(data))
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            if len(msgs) == 6:
                if all(isinstance(m.timestamp_ms, int) for m in msgs):
                    res.passed = True
                else:
                    res.passed = False
                    res.severity = "MEDIUM"
                    res.details = "Not all timestamp_ms are ints"
            else:
                res.passed = False
                res.severity = "MEDIUM"
                res.details = f"Expected 6 messages, got {len(msgs)}"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed on timestamp variants: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_sender_name_and_is_an_an_resolution(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Sender Resolution & is_an_an Matching", "Schema/Filtering")
        data = {
            "messages": [
                {"senderName": "An An", "text": "Exact match", "timestamp": 1000},
                {"senderName": "an an", "text": "Lower match", "timestamp": 2000},
                {"senderName": "AN AN", "text": "Upper match", "timestamp": 3000},
                {"senderName": "Bé An An 🌸", "text": "Substring match", "timestamp": 4000},
                {"senderName": "Nguyen Van An", "text": "Single An (not An An)", "timestamp": 5000},
                {"senderName": "Hoàng Kim Quờ Lờ", "text": "Partner", "timestamp": 6000},
                {"sender_name": "An An", "text": "Legacy key sender_name", "timestamp": 7000},
                {"text": "Missing sender key", "timestamp": 8000},
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(data))
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            expected_flags = [True, True, True, True, False, False, True, False]
            actual_flags = [m.is_an_an for m in msgs]
            if actual_flags == expected_flags and msgs[-1].sender_name == "Unknown":
                res.passed = True
            else:
                res.passed = False
                res.severity = "HIGH"
                res.details = f"Flags mismatch: expected {expected_flags}, got {actual_flags}"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_reactions_adversarial_types(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Reactions Corrupted Types & Mojibake Emojis", "Schema/Filtering")
        data = {
            "messages": [
                {
                    "senderName": "An An",
                    "text": "React test",
                    "timestamp": 1000,
                    "reactions": [
                        {"actor": "QL", "reaction": "❤"},
                        {"actor": "QL", "reaction": "\u00f0\u009f\u0091\u008d"},  # mojibake 👍
                        {"actor": "Nobody"},
                        {"reaction": ""},
                        {"reaction": None},
                        "🔥",
                        12345,
                        None,
                        [],
                    ]
                },
                {
                    "senderName": "An An",
                    "text": "Reactions not a list",
                    "timestamp": 2000,
                    "reactions": "not a list"
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(data))
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            m1_reactions = msgs[0].reactions
            m2_reactions = msgs[1].reactions
            if "❤" in m1_reactions and "👍" in m1_reactions and "🔥" in m1_reactions and m2_reactions == []:
                res.passed = True
            else:
                res.passed = False
                res.severity = "MEDIUM"
                res.details = f"Extracted reactions unexpected: m1={m1_reactions}, m2={m2_reactions}"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed on reactions: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_sorting_and_chronological_stability(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Chronological Sorting Stability (5,000 Shuffled Msgs)", "Sorting")
        import random
        random.seed(42)
        timestamps = list(range(1000, 1000 + 5000 * 10, 10))
        shuffled_ts = timestamps.copy()
        random.shuffle(shuffled_ts)

        data = {
            "messages": [
                {"senderName": "An An", "text": f"Msg {ts}", "timestamp": ts}
                for ts in shuffled_ts
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(data))
            path = f.name
        try:
            msgs = parse_facebook_json(path)
            res.duration_ms = (time.perf_counter() - t0) * 1000
            actual_ts = [m.timestamp_ms for m in msgs]
            if actual_ts == timestamps:
                res.passed = True
            else:
                res.passed = False
                res.severity = "CRITICAL"
                res.details = "Messages not properly sorted chronologically"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "CRITICAL"
            res.details = f"Crashed on sorting: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_high_volume_scalability(self):
        t0 = time.perf_counter()
        res = ChallengeResult("High Volume Ingestion (20,000 Messages)", "Scalability")
        data = {
            "messages": [
                {
                    "senderName": "An An" if i % 2 == 0 else "Hoàng Kim Quờ Lờ",
                    "text": f"Tin nhắn số {i}: Chúc một ngày tốt lành! 🌸",
                    "timestamp": 1000000 + i * 100,
                    "reactions": [{"actor": "User", "reaction": "❤"}] if i % 5 == 0 else []
                }
                for i in range(20000)
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(json.dumps(data))
            path = f.name
        try:
            t_start = time.perf_counter()
            msgs = parse_facebook_json(path)
            t_end = time.perf_counter()
            duration = t_end - t_start
            rate = len(msgs) / duration if duration > 0 else 0
            res.duration_ms = duration * 1000

            if len(msgs) == 20000 and duration < 10.0:
                res.passed = True
                res.details = f"Parsed 20,000 msgs in {duration:.2f}s ({rate:.0f} msgs/sec)"
            else:
                res.passed = False
                res.severity = "MEDIUM"
                res.details = f"Failed or too slow: {len(msgs)} msgs in {duration:.2f}s"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "HIGH"
            res.details = f"Crashed on high volume: {type(exc).__name__}: {exc}"
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.record(res)

    def test_real_dataset_benchmark(self):
        t0 = time.perf_counter()
        res = ChallengeResult("Real Dataset Verification (An An_86.json)", "Real Data")
        real_path = Path("F:/dowload/FacebookData/messages/An An_86.json")
        if not real_path.exists():
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = True
            res.details = "Real dataset not available on this path, skipped"
            self.record(res)
            return

        try:
            msgs = parse_facebook_json(str(real_path))
            res.duration_ms = (time.perf_counter() - t0) * 1000
            if len(msgs) == 2032:
                none_texts = [m for m in msgs if m.text == "None"]
                empty_texts = [m for m in msgs if not m.text.strip()]
                an_an_count = sum(1 for m in msgs if m.is_an_an)

                if not none_texts and not empty_texts and an_an_count == 1174:
                    res.passed = True
                    res.details = (
                        f"Parsed 2,032 canonical messages (1,174 An An, 858 QL) in {res.duration_ms:.1f}ms. "
                        f"Zero empty or 'None' texts."
                    )
                else:
                    res.passed = False
                    res.severity = "HIGH"
                    res.details = (
                        f"Real data anomaly: none_texts={len(none_texts)}, "
                        f"empty_texts={len(empty_texts)}, an_an_count={an_an_count} (expected 1174)"
                    )
            else:
                res.passed = False
                res.severity = "HIGH"
                res.details = f"Expected 2032 messages, got {len(msgs)}"
        except Exception as exc:
            res.duration_ms = (time.perf_counter() - t0) * 1000
            res.passed = False
            res.severity = "CRITICAL"
            res.details = f"Crashed parsing real dataset: {type(exc).__name__}: {exc}"
        self.record(res)

    def run_all(self) -> Dict[str, Any]:
        print("\n" + "=" * 80)
        print("STARTING EMPIRICAL CHALLENGE SUITE: src/ingestion/parser.py")
        print("=" * 80 + "\n")

        # Category 1: Mojibake & Encoding Stress
        self.test_encoding_native_vietnamese()
        self.test_encoding_nfd_decomposition()
        self.test_encoding_latin1_mojibake_standard()
        self.test_encoding_latin1_mojibake_emoji()
        self.test_encoding_mixed_mojibake_and_native()
        self.test_encoding_multilingual_scripts()
        self.test_encoding_control_chars_and_null_bytes()
        self.test_encoding_lone_surrogates()
        self.test_encoding_all_latin1_bytes()
        self.test_encoding_type_safety()
        self.test_encoding_massive_string_throughput()

        # Category 2: File System & JSON Malformation
        self.test_file_non_existent()
        self.test_file_is_directory()
        self.test_file_empty_and_whitespace()
        self.test_file_malformed_json_syntax()
        self.test_file_non_dict_root()
        self.test_file_missing_or_invalid_messages_key()
        self.test_file_utf8_bom()
        self.test_file_deeply_nested_fields()

        # Category 3: Schema Corruption & Noise Filtering
        self.test_messages_non_dict_elements()
        self.test_messages_null_content_stringification_bug()
        self.test_messages_unsent_edge_cases()
        self.test_messages_system_calls_and_placeholders()
        self.test_timestamp_infinity_overflow_bug()
        self.test_timestamp_various_formats()
        self.test_sender_name_and_is_an_an_resolution()
        self.test_reactions_adversarial_types()
        self.test_sorting_and_chronological_stability()
        self.test_high_volume_scalability()
        self.test_real_dataset_benchmark()

        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        print("\n" + "=" * 80)
        print(f"CHALLENGE SUMMARY: {passed}/{total} Passed ({passed/total*100:.1f}%) | {failed} Failed")
        print("=" * 80 + "\n")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "results": self.results
        }


if __name__ == "__main__":
    runner = StressTestRunner()
    summary = runner.run_all()
    if summary["failed"] > 0:
        print(f"\n[ALERT] {summary['failed']} stress tests failed. Review details above.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All stress tests passed!")
        sys.exit(0)
