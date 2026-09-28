import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

path = r'F:\dowload\FacebookData\messages\An An_86.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print('Top level keys:', list(data.keys()))
print('Participants:', data.get('participants'))
print('Thread Name:', data.get('threadName'))
messages = data.get('messages', [])
print('Total messages:', len(messages))

# Analyze senders
senders = {}
for m in messages:
    sender = m.get('senderName') or m.get('sender_name')
    senders[sender] = senders.get(sender, 0) + 1
print('Senders distribution:', senders)

# Check message fields
if messages:
    print('Sample message 0 fields:', list(messages[0].keys()))
    for i in range(min(10, len(messages))):
        m = messages[i]
        s = m.get('senderName') or m.get('sender_name')
        c = m.get('content') or m.get('text')
        ts = m.get('timestamp') or m.get('timestamp_ms')
        print(f'[{i}] Sender: {s} | Time: {ts} | Content: {repr(c)}')
