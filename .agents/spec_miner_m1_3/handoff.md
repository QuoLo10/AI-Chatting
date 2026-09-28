# Handoff Report: Milestone M1 Ingestion Test Specification

**Agent:** `spec_miner_m1_3` (Ingestion Test Specifier)  
**Milestone:** M1 (Dependencies & Data Ingestion Engine)  
**Handoff Type:** Hard (Task complete)  
**Date:** 2026-09-14T10:54:00Z  

---

## 1. Observation

1. **Authoritative Specification & Architecture:**
   - `ORIGINAL_REQUEST.md` (lines 11, 34): System must ingest Facebook Messenger JSON (`F:/dowload/FacebookData/messages/An An_86.json`) to mimic persona "An An" conversing with "ql".
   - `PROJECT.md` (lines 50-69): Interface contract between `src.ingestion.parser` and `src.ingestion.persona_profile`:
     ```python
     class CanonicalMessage(BaseModel):
         sender_name: str
         text: str
         timestamp_ms: int
         is_an_an: bool
         reactions: List[str] = []

     def parse_facebook_json(file_path: str) -> List[CanonicalMessage]: ...
     def extract_an_an_profile(messages: List[CanonicalMessage]) -> dict: ...
     ```
   - `TEST_INFRA.md` (lines 8-27): Test mapping assigns F1 (Ingestion), F2 (Transcoding), and F3 (Persona Profiling) $\ge 5$ feature and $\ge 5$ boundary tests each, runner `pytest` via `.\venv\Scripts\python.exe -m pytest tests/`.

2. **Windows Encoding Trap Direct Observation:**
   - Probing `An An_86.json` under default Python 3.14 stdout without UTF-8 reconfiguration produced verbatim:
     ```
     UnicodeEncodeError: 'charmap' codec can't encode character '\u1edd' in position 14: character maps to <undefined>
     ```
   - Probing with `sys.stdout.reconfigure(encoding='utf-8')` successfully read the entire file.

3. **Empirical Ground Truth from `F:/dowload/FacebookData/messages/An An_86.json`:**
   - Total raw messages: 2,102.
   - Participants: `['Hoàng Kim Quờ Lờ', 'An An']`.
   - Sender breakdown: Hoàng Kim Quờ Lờ = 897 messages; An An = 1,205 messages.
   - Unsent messages: 15 messages (all with `isUnsent: True`, `type: 'placeholder'`, `text: 'User unsent a message'`).
   - Media attachments with empty text: 55 messages (`type: 'media'`).
   - Links: 5 messages (`type: 'link'`).
   - Valid conversational text messages: 2,027 messages (`type: 'text'`).
   - Timestamp ordering: strictly ascending (`timestamps == sorted(timestamps)` is `True`).
   - An An text messages count: 1,174 messages.
   - An An empirical word length distribution:
     - Short ($\le 5$ words): 822 messages (**70.0%**)
     - Medium ($6-15$ words): 324 messages (**27.6%**)
     - Long ($> 15$ words): 28 messages (**2.4%**)
   - Signature teen-code token frequencies in An An messages:
     - `kh`: 143
     - `dc`: 42
     - `nma`: 36
     - `r`: 100
     - `=)))`: 75
     - `🤡`: 14
     - `ql`: 40
     - Anti-patterns: `k`: 0, `đc`: 0, `nhma`: 0, `ko`: 2
   - Dialogue turns and pairs:
     - Alternating user $\to$ An An collapsed turns: 392 to 410 pairs.
     - Pair 0: User `"Chúc An mai thi tốt"` $\to$ An An `"Cám mơn ql nhieu nhaa"`.
     - Pair 1: User `"tự tin lên cố lên 💪"` $\to$ An An `"Jza"`.

---

## 2. Logic Chain

1. **Transcoding Logic:** Because `An An_86.json` is clean native UTF-8 containing Vietnamese code points outside the Latin-1 range (`\u1edd`, `\u01a1`, `\u0111`), executing `text.encode('latin1')` blindly will trigger `UnicodeEncodeError`. The safe transcoding function `safe_decode_mojibake` must catch both `UnicodeEncodeError` and `UnicodeDecodeError` or use heuristic character checks before attempting `encode('latin1').decode('utf-8')`. Tests must verify native UTF-8 pass-through, Latin-1 double-encoded restoration, emoji preservation, and mixed-string safety without exceptions.
2. **Filtering Logic:** The 15 unsent messages in `An An_86.json` contain no communicative content and must be excluded via both boolean flag `isUnsent: True` and text pattern `"User unsent a message"`. Messages containing `"Failed to download media"` and empty/whitespace texts must also be filtered out so they do not pollute persona statistics or conversation context.
3. **Distribution & Token Profiling Logic:** `extract_an_an_profile` must calculate empirical word length distributions and token counts. Because the empirical data yields exactly 70.0% short, 27.6% medium, and 2.4% long, unit test assertions must enforce tight tolerance bands around these ground truths ($67-73\%$ short, $25-31\%$ medium, $1-4\%$ long) and confirm that anti-pattern tokens (`k`, `đc`, `nhma`) evaluate to strictly 0.
4. **Dialogue Extraction Logic:** Consecutive message bursts from the same sender must be collapsed into single dialogue turns joined by newlines before pairing User turns with An An responses. The test suite asserts that $\ge 380$ dialogue pairs are extracted and validates the first two ground-truth exchanges verbatim.
5. **Fault Tolerance Logic:** Real-world services encounter missing files, malformed JSON syntax, 0-byte files, and empty message lists. `extract_an_an_profile` must handle `messages = []` without `ZeroDivisionError`, and `parse_facebook_json` must raise clean, informative exceptions (`FileNotFoundError`, `ValueError`, `json.JSONDecodeError`).

---

## 3. Caveats

- In Facebook Messenger exports, media messages can either contain an attachment without text (`text: ""`) or have an accompanying user caption (`text: "xem nè", media: [...]`). The test specification treats media-only empty messages as excluded from text dialogue turns, while messages with text captions and media are retained as valid dialogue turns.
- The primary dataset `F:/dowload/FacebookData/messages/An An_86.json` resides on drive `F:`. The test specification specifies dynamic fixture skipping via `pytest.skip` if the file is absent when running on machines without drive `F:`, while providing complete synthetic fixtures (`synthetic_modern_fb_json`, `synthetic_standard_fb_json`, `dirty_filter_fb_json`) that run 100% self-contained in any environment.

---

## 4. Conclusion

The specification for `tests/test_ingestion.py` has been fully formulated and written to `.agents/spec_miner_m1_3/test_spec.md`. It specifies **49 distinct unit test cases** grouped into 6 logical test classes:
1. `TestSafeMojibakeDecoder` (8 tests): Native UTF-8, Latin-1 mojibake, mixed strings, emojis, ASCII, falsy/non-string inputs.
2. `TestFacebookJsonParserHappyPath` (9 tests): Real sample parsing, count verification, participant distribution, chronological ordering, `is_an_an` flag, modern vs standard schema mapping, reactions extraction.
3. `TestMessageFiltering` (6 tests): Unsent boolean, unsent text, failed media downloads, empty text, call logs, dirty fixture cleaning.
4. `TestPersonaProfiling` (12 tests): Message statistics, short/medium/long distributions, word mean/median, signature token counts (`kh`, `dc`, `nma`, `r`, `=)))`, `🤡`, `ql`), anti-pattern verification.
5. `TestDialoguePairExtraction` (5 tests): Turn burst collapsing, dialogue pair schema, pair count ($\ge 380$), ground-truth pair verification.
6. `TestFaultToleranceAndEdgeCases` (9 tests): Missing files, broken JSON syntax, 0-byte files, empty messages array, zero-division safety, missing optional fields, reverse sorting.

---

## 5. Verification Method

To verify the test specification and readiness for implementation:
1. **Inspect Artifact:** View `C:\Users\HKQL2\Documents\ExBuild\.agents\spec_miner_m1_3\test_spec.md`.
2. **Verify Test Runner:** When the test file is implemented in `tests/test_ingestion.py`, run:
   ```powershell
   .\venv\Scripts\python.exe -m pytest tests/test_ingestion.py -v
   ```
3. **Invalidation Conditions:**
   - Any test case failing to assert zero `UnicodeEncodeError` when encountering Vietnamese characters.
   - Any failure in filtering unsent messages or empty media.
   - Length distribution tolerances falling outside the empirical 70.0% / 27.6% / 2.4% baseline.
   - `ZeroDivisionError` occurring when passing empty message arrays to `extract_an_an_profile`.
