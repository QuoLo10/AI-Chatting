import json
import statistics

path = r'F:\dowload\FacebookData\messages\An An_86.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

messages = data.get('messages', [])

# Group into turns
turns = []
current_sender = None
current_texts = []
for m in messages:
    sender = m.get('senderName') or m.get('sender_name')
    text = m.get('text') or ''
    if m.get('isUnsent'):
        continue
    if not text.strip():
        continue
    if sender == current_sender:
        current_texts.append(text)
    else:
        if current_sender and current_texts:
            turns.append((current_sender, current_texts))
        current_sender = sender
        current_texts = [text]
if current_sender and current_texts:
    turns.append((current_sender, current_texts))

print(f"Total aggregated turns: {len(turns)}")

# Print 10 exchanges
idx = 0
for i in range(len(turns) - 1):
    s1, t1 = turns[i]
    s2, t2 = turns[i+1]
    if s1 != 'An An' and s2 == 'An An':
        print(f"\n--- Exchange {idx+1} ---")
        print(f"User ({s1}): {' // '.join(t1)}")
        print(f"An An: {' // '.join(t2)}")
        idx += 1
        if idx >= 10:
            break
