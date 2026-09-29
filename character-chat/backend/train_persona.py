import os
import sys
import json
from dotenv import load_dotenv
from google import genai
from supabase import create_client

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

ai_client = genai.Client(api_key=os.environ.get('GOOGLE_AI_API_KEY'))
supabase = create_client(os.environ.get('SUPABASE_URL'), os.environ.get('SUPABASE_SERVICE_ROLE_KEY'))

print('Reading JSON...')
with open(r'F:\dowload\FacebookData\messages\An An_86.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

messages = data.get('messages', [])
messages.reverse()

convo_lines = []
for m in messages[-400:]: 
    if 'text' in m:
        sender = 'User' if m['senderName'] == 'Hoàng Kim Quờ Lờ' else 'An An'
        convo_lines.append(f"{sender}: {m['text']}")

convo_text = '\n'.join(convo_lines)

prompt = f'''Analyze the following chat log between 'User' and 'An An'.
I want you to write a comprehensive system prompt to instruct an AI to perfectly mimic 'An An' in future conversations.

The system prompt should include:
1. Her exact tone, personality, and humor.
2. Her typical message length (e.g., short bursty texts vs long paragraphs).
3. A list of her favorite catchphrases, slang, or abbreviations.
4. Her emoji usage (which emojis she uses and how often).
5. 3-5 few-shot examples of conversations showing how she would reply to the User.

Keep the final output as JUST the system prompt text that I can feed directly to an AI. DO NOT WRAP IT IN MARKDOWN CODE BLOCKS.

Chat Log:
{convo_text}'''

print('Sending to Gemini for analysis...')
response = ai_client.models.generate_content(
    model='gemini-3.5-flash-lite',
    contents=prompt
)

new_system_prompt = response.text.strip()
if new_system_prompt.startswith('`') and new_system_prompt.endswith('`'):
    new_system_prompt = new_system_prompt.split('\n', 1)[1].rsplit('\n', 1)[0]
    
print('Generated Prompt length:', len(new_system_prompt))

print('Updating database...')
supabase.table('settings').update({
    'system_prompt': new_system_prompt,
    'character_name': 'An An',
    'user_name': 'Hoàng Kim Quờ Lờ'
}).eq('id', 1).execute()

print('DONE! Persona updated in Supabase.')
