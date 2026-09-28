# Handoff Report: Milestone M1 Ingestion & Configuration Design

**Agent**: `explorer_m1_1` (Ingestion Implementation Planner)  
**Handoff Type**: Hard Handoff  
**Target Recipient**: Orchestrator (`parent`) & Worker M1  
**Working Directory**: `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_1`  
**Primary Deliverable**: `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_1\design.md`  
**Timestamp**: 2026-09-14T10:53:00Z  

---

## 1. Observation

### 1.1 Dataset Inspection & Transcoding Trap
- **Target File**: `F:/dowload/FacebookData/messages/An An_86.json` (515,161 bytes, 2,102 raw messages).
- **Console Encoding Observation**: Running standard Python printing of participant names without setting encoding raised:
  ```
  UnicodeEncodeError: 'charmap' codec can't encode character '\u1edd' in position 28: character maps to <undefined>
  ```
  Demonstrating that Windows terminal default (`cp1252`) requires explicit `sys.stdout.reconfigure(encoding='utf-8')`.
- **Transcoding Trap**: When running classic Facebook mojibake decoder `text.encode('latin1').decode('utf-8')` on raw message `"Chúc An mai thi tốt"`:
  ```
  UnicodeEncodeError: 'latin-1' codec can't encode character '\u1ed1' in position 17: ordinal not in range(256)
  ```
  Because `An An_86.json` is already clean UTF-8.
- **Transcoding Guard Verification**: Running the guarded function:
  ```python
  def fix_fb_text(text):
      if not text or not isinstance(text, str):
          return ""
      try:
          return text.encode('latin1').decode('utf-8')
      except (UnicodeEncodeError, UnicodeDecodeError):
          return text
  ```
  Against both clean UTF-8 and synthetic Latin-1 mojibake resulted in:
  `Transcoding verification SUCCESS!` (0 errors, 100% diacritic preservation).

### 1.2 Message Parsing & Filtering Counts
- Running the filter on `An An_86.json`:
  - Total raw messages: 2,102
  - Unsent dropped (`isUnsent == True` or `"User unsent a message"`): 15
  - Empty / media-only dropped: 55
  - Valid canonical messages: 2,032
  - An An valid messages: 1,174 (57.8%)
  - HKQL valid messages: 858 (42.2%)

### 1.3 Linguistic & Dynamic Length Statistics
- An An empirical message word distribution (from 1,174 messages):
  - Mean words per message: 4.70
  - Median words per message: 4.0
  - Short ($\le 5$ words): 822 (70.0%)
  - Medium (6–15 words): 324 (27.6%)
  - Long ($> 15$ words): 28 (2.4%)
  This matches `PROJECT.md` lines 76–80 (`SHORT`: 70%, `MEDIUM`: 27.6%, `LONG`: 2.4%).
- Empirical slang token counts in An An messages:
  - `kh`: 143, `hong`: 12 vs `ko`: 2, `k`: 0
  - `dc`: 42 vs `đc`: 0
  - `nma`: 36 vs `nhma`: 0
  - `r`: 100
  - `v`: 38, `z`: 17
  - `th`: 40, `thui`: 7
  - `oki`: 31 vs `oke`: 0
  - `=)))`: 81
  - `🤡`: 14
  - `ql`: 40

### 1.4 Interface Contracts & File Structure
- `PROJECT.md` lines 51–69 specifies:
  - `CanonicalMessage(sender_name: str, text: str, timestamp_ms: int, is_an_an: bool, reactions: List[str] = [])`
  - `parse_facebook_json(file_path: str) -> List[CanonicalMessage]`
  - `extract_an_an_profile(messages: List[CanonicalMessage]) -> dict`
- Current project root has `.env` with `GEMINI_API_KEY` and `GROQ_API_KEY`.

---

## 2. Logic Chain

1. **Premise**: `An An_86.json` contains clean UTF-8 strings. However, standard Facebook DYI exports often contain Latin-1 mojibake.
   - **Inference**: Using naive `text.encode('latin1').decode('utf-8')` crashes with `UnicodeEncodeError` on clean Vietnamese, while doing no decoding fails on mojibake.
   - **Conclusion**: Wrapping the decode attempt in `try / except (UnicodeEncodeError, UnicodeDecodeError)` safely handles both formats with zero overhead and zero crash risk.

2. **Premise**: Raw chat logs contain unsent messages and media attachments without captions.
   - **Inference**: Passing empty text or "User unsent a message" into persona statistical analysis or few-shot prompts will poison the LLM context.
   - **Conclusion**: `parse_facebook_json` must drop messages where `is_unsent == True`, text is `"User unsent a message"`, or `text.strip() == ""`.

3. **Premise**: `PROJECT.md` defines `CanonicalMessage` with `reactions: List[str] = []`.
   - **Inference**: Facebook raw JSON reactions are objects `{"actor": "...", "reaction": "..."}`.
   - **Conclusion**: The parser must extract just the reaction string (`r["reaction"]`) to satisfy the Pydantic model contract cleanly.

4. **Premise**: `PROJECT.md` lines 76–80 establishes three length tiers (`SHORT`, `MEDIUM`, `LONG`) based on empirical frequency.
   - **Inference**: Analysis of all 1,174 messages from An An reveals exactly 70.0% $\le 5$ words, 27.6% 6–15 words, and 2.4% $> 15$ words.
   - **Conclusion**: The `extract_an_an_profile` statistical extraction engine provides mathematically verifiable bounds that directly validate Milestone M2's length controller.

5. **Premise**: Downstream modules (`src/core/prompts.py` in M2 and `src/core/chain.py` in M3) need authentic few-shot dialogue turns to guide LLM persona mimicry.
   - **Inference**: Survey 1 extracted and verified 15 authentic multi-turn exchanges covering 6 key conversational genres.
   - **Conclusion**: Placing `FEW_SHOT_EXCHANGES`, `SLANG_DICTIONARY`, and `PROHIBITED_TOKENS` into `src/ingestion/persona_profile.py` gives the entire system a centralized, typed source of truth.

---

## 3. Caveats

1. **Python 3.14.6 Environment**: The virtual environment at `C:\Users\HKQL2\Documents\ExBuild\venv` currently contains only `pip 26.1.2`. Packages (`pydantic`, `python-dotenv`, `langchain-core`, etc.) will be installed by Worker M1 following `explorer_m1_2`'s dependency plan.
2. **Missing Media Files**: As expected from survey 1, actual photo/video files are not present in the export folder (URIs indicate `"Failed to download media"`). Text filtering drops them cleanly, which is the desired behavior for a text-based chatbot.
3. **Windows Stdout Encoding**: Code running in Windows command prompt or PowerShell may experience `UnicodeEncodeError` when printing Vietnamese characters to terminal. CLI and test runners must configure `sys.stdout.reconfigure(encoding='utf-8')`.

---

## 4. Conclusion

The architectural design, exact interfaces, and complete code specifications for Milestone M1 are fully defined and documented in:
`C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_1\design.md`

Summary of deliverables ready for Worker M1 implementation:
1. `src/config.py`: Complete `.env` loading, path resolution (`DEFAULT_JSON_PATH = "F:/dowload/FacebookData/messages/An An_86.json"`), cross-populated `GEMINI_API_KEY` / `GOOGLE_API_KEY`, and `GROQ_API_KEY`.
2. `src/ingestion/parser.py`: Pydantic `CanonicalMessage`, fault-tolerant `fix_fb_text()`, unsent/media filtering, and deterministic chronological sorting.
3. `src/ingestion/persona_profile.py`: `extract_an_an_profile()` empirical statistical engine, turn aggregator, `SLANG_DICTIONARY`, `PROHIBITED_TOKENS`, and 15 categorized few-shot exchanges.

---

## 5. Verification Method

To independently verify the recommendations and design:

1. **Transcoding & Parser Verification Command**:
   Run the following Python one-liner to verify that the parser logic ingests `An An_86.json` and produces exactly 2,032 valid messages:
   ```powershell
   .\venv\Scripts\python.exe -c "
   import sys, json
   sys.stdout.reconfigure(encoding='utf-8')
   with open('F:/dowload/FacebookData/messages/An An_86.json', 'r', encoding='utf-8') as f:
       data = json.load(f)
   def fix(t):
       try: return t.encode('latin1').decode('utf-8') if t else ''
       except: return t or ''
   msgs = [m for m in data['messages'] if not (m.get('isUnsent') or m.get('is_unsent')) and fix(m.get('text')).strip() and fix(m.get('text')).strip() != 'User unsent a message']
   print(f'Total valid: {len(msgs)}')
   assert len(msgs) == 2032
   print('Verification passed!')
   "
   ```

2. **Files to Inspect**:
   - `C:\Users\HKQL2\Documents\ExBuild\.agents\explorer_m1_1\design.md` (Complete implementation guide and code structure).
   - `C:\Users\HKQL2\Documents\ExBuild\PROJECT.md` (Lines 50–70 for contract alignment).
   - `F:\dowload\FacebookData\messages\An An_86.json` (Source dataset).

3. **Invalidation Conditions**:
   - If `fix_fb_text()` is implemented without the `try / except` guard, it will raise `UnicodeEncodeError` on `An An_86.json`.
   - If `CanonicalMessage` fields differ from `PROJECT.md` (e.g. non-string reactions or missing `is_an_an`), downstream contracts in M2/M3 will fail.
