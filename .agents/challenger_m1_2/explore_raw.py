import json
from pathlib import Path
from src.ingestion.parser import parse_facebook_json, safe_decode_mojibake
from src.ingestion.persona_profile import extract_an_an_profile

raw_path = Path("F:/dowload/FacebookData/messages/An An_86.json")

with open(raw_path, "r", encoding="utf-8", errors="replace") as f:
    raw_data = json.load(f)

print(f"Total raw messages in JSON: {len(raw_data.get('messages', []))}")

# Check participant names
participants = raw_data.get("participants", [])
print(f"Participants: {participants}")

# Parse using parser
messages = parse_facebook_json(raw_path)
print(f"Parsed CanonicalMessage count: {len(messages)}")

an_an_msgs = [m for m in messages if m.is_an_an]
user_msgs = [m for m in messages if not m.is_an_an]
print(f"An An messages: {len(an_an_msgs)}")
print(f"User messages: {len(user_msgs)}")

profile = extract_an_an_profile(messages)
print("Profile Overview:", profile["overview"])
print("Profile Stats:", profile["stats"])
print("Profile Length Distribution:", profile["length_distribution"])
print("Token Frequencies:", profile["token_frequencies"])
print("Prohibited Frequencies:", profile["prohibited_frequencies"])
