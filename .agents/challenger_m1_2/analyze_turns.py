import json
from pathlib import Path
from src.ingestion.parser import parse_facebook_json
from src.ingestion.persona_profile import extract_an_an_profile

messages = parse_facebook_json("F:/dowload/FacebookData/messages/An An_86.json")

# Re-run turn extraction while recording turn timestamps
turns = []
current_sender = None
current_texts = []
turn_start_ts = 0
turn_end_ts = 0
last_ts = 0

for m in messages:
    if m.sender_name != current_sender or (m.timestamp_ms - last_ts > 7_200_000 and current_sender is not None):
        if current_texts:
            turns.append({
                "sender": current_sender,
                "is_an": (current_sender == "An An" or "an an" in str(current_sender).lower()),
                "start_ts": turn_start_ts,
                "end_ts": turn_end_ts,
                "text": "\n".join(current_texts)
            })
        current_sender = m.sender_name
        current_texts = [m.text]
        turn_start_ts = m.timestamp_ms
    else:
        current_texts.append(m.text)
    turn_end_ts = m.timestamp_ms
    last_ts = m.timestamp_ms

if current_texts:
    turns.append({
        "sender": current_sender,
        "is_an": (current_sender == "An An" or "an an" in str(current_sender).lower()),
        "start_ts": turn_start_ts,
        "end_ts": turn_end_ts,
        "text": "\n".join(current_texts)
    })

print(f"Total turns: {len(turns)}")

total_pairs = 0
large_gap_pairs = []
for i in range(len(turns) - 1):
    if not turns[i]["is_an"] and turns[i+1]["is_an"]:
        total_pairs += 1
        gap_ms = turns[i+1]["start_ts"] - turns[i]["end_ts"]
        gap_hours = gap_ms / (1000 * 3600)
        if gap_hours > 2.0:
            large_gap_pairs.append((gap_hours, turns[i]["text"], turns[i+1]["text"]))

print(f"Total user->An An pairs: {total_pairs}")
print(f"Pairs where response gap > 2 hours: {len(large_gap_pairs)} ({len(large_gap_pairs)/total_pairs*100:.1f}%)")
print(f"Pairs where response gap > 24 hours: {sum(1 for g, _, _ in large_gap_pairs if g > 24)}")
print(f"Pairs where response gap > 7 days: {sum(1 for g, _, _ in large_gap_pairs if g > 24*7)}")

large_gap_pairs.sort(key=lambda x: x[0], reverse=True)
print("\nTop 5 largest gaps:")
for g, u, a in large_gap_pairs[:5]:
    print(f"--- Gap: {g:.1f} hours ({g/24:.1f} days) ---")
    print(f"  User input: {repr(u[:80])}")
    print(f"  An An reply: {repr(a[:80])}")
