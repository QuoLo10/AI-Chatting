import json
import tempfile
import os
import time
from pathlib import Path
from src.ingestion.parser import parse_facebook_json, CanonicalMessage
from src.ingestion.persona_profile import extract_an_an_profile, get_few_shot_examples

print("--- ADVERSARIAL STRESS TEST SUITE ---")

# Test 1: Messages with None elements, corrupt types
data1 = {
    "messages": [
        None,
        123,
        "string_instead_of_dict",
        {},
        {"text": None, "timestamp": None, "senderName": None},
        {"text": "Valid message", "timestamp": 100, "senderName": "An An"}
    ]
}
with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".json") as f:
    json.dump(data1, f)
    f_path = f.name

try:
    msgs = parse_facebook_json(f_path)
    print("Test 1 (Corrupt message elements): PASSED - Found valid messages:", len(msgs))
    assert len(msgs) == 1
    assert msgs[0].text == "Valid message"
finally:
    if os.path.exists(f_path):
        os.remove(f_path)

# Test 2: Stress test 10,000 messages performance
large_msgs = [
    CanonicalMessage(
        sender_name="Hoàng Kim Quờ Lờ" if i % 2 == 0 else "An An",
        text=f"Tin nhắn số {i} với từ kh, dc, nma =))) 🤡",
        timestamp_ms=1000 + i * 500,
        is_an_an=(i % 2 != 0)
    )
    for i in range(10000)
]

t0 = time.time()
profile = extract_an_an_profile(large_msgs)
t1 = time.time()
turns_count = profile["stats"]["total_turns"]
print(f"Test 2 (10,000 messages profiling): PASSED in {t1 - t0:.3f}s - Total turns: {turns_count}")
assert profile["stats"]["total_messages"] == 10000

# Test 3: Unsorted timestamps edge case
unsorted_msgs = [
    CanonicalMessage(sender_name="An An", text="Message 2", timestamp_ms=2000, is_an_an=True),
    CanonicalMessage(sender_name="An An", text="Message 1", timestamp_ms=1000, is_an_an=True),
]
prof_unsorted = extract_an_an_profile(unsorted_msgs)
print("Test 3 (Unsorted inputs to extract_an_an_profile): PASSED")

# Test 4: Extreme unicode strings and special symbols
symbols_data = {
    "messages": [
        {"senderName": "An An", "text": "null byte \x00 in string", "timestamp": 100},
        {"senderName": "An An", "text": "Zalgo ̡ͬ̕͢͡͏͏", "timestamp": 200},
        {"senderName": "An An", "text": "RTL text: \u202eReversed\u202c", "timestamp": 300},
    ]
}
with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".json") as f:
    json.dump(symbols_data, f)
    sym_path = f.name
try:
    sym_msgs = parse_facebook_json(sym_path)
    print("Test 4 (Special symbols and unicode stress): PASSED - Parsed:", len(sym_msgs))
finally:
    if os.path.exists(sym_path):
        os.remove(sym_path)

print("ALL ADVERSARIAL STRESS TESTS COMPLETED SUCCESSFULLY!")
