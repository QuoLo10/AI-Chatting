import json
from src.ingestion.persona_profile import FEW_SHOT_EXCHANGES
from src.ingestion.parser import parse_facebook_json

messages = parse_facebook_json("F:/dowload/FacebookData/messages/An An_86.json")

for ex in FEW_SHOT_EXCHANGES:
    for t_idx, t in enumerate(ex["turns"]):
        target_an = t["an_an"].split("\n")[0].strip()
        found = False
        for idx, m in enumerate(messages):
            if m.is_an_an and target_an in m.text:
                prev_user = []
                j = idx - 1
                while j >= 0 and not messages[j].is_an_an:
                    prev_user.insert(0, messages[j].text)
                    j -= 1
                print(f"Ex {ex['id']} Turn {t_idx+1} ({ex['category']}):")
                print(f"   Few-shot User: {repr(t['user'])}")
                print(f"   Actual User:   {repr(chr(10).join(prev_user))}")
                print(f"   Few-shot An:   {repr(t['an_an'][:40])}")
                print(f"   Actual An:     {repr(m.text[:40])}")
                found = True
                break
        if not found:
            print(f"Ex {ex['id']} Turn {t_idx+1}: NOT FOUND IN DATASET")
