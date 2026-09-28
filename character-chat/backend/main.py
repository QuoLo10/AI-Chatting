import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("Warning: Supabase credentials not found in .env")
    supabase: Client = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Google AI client
GOOGLE_AI_API_KEY = os.environ.get("GOOGLE_AI_API_KEY")
if not GOOGLE_AI_API_KEY:
    print("Warning: Google AI API key not found in .env")
    ai_client = None
else:
    ai_client = genai.Client(api_key=GOOGLE_AI_API_KEY)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SettingsUpdate(BaseModel):
    character_name: str
    system_prompt: str
    user_name: str

@app.get("/api/settings")
def get_settings():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    response = supabase.table("settings").select("*").eq("id", 1).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Settings not found")
    return response.data[0]

@app.put("/api/settings")
def update_settings(settings: SettingsUpdate):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    response = supabase.table("settings").upsert({
        "id": 1,
        "character_name": settings.character_name,
        "system_prompt": settings.system_prompt,
        "user_name": settings.user_name
    }).execute()
    
    return response.data[0]

@app.get("/api/messages")
def get_messages():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    # Order by created_at ascending
    response = supabase.table("messages").select("*").order("created_at").execute()
    return response.data

@app.post("/api/chat")
async def chat(text: str = Form(None), image: UploadFile = File(None)):
    if not supabase or not ai_client:
        raise HTTPException(status_code=500, detail="Services not fully configured")
    
    if not text and not image:
        raise HTTPException(status_code=400, detail="Must provide text or image")

    image_url = None
    if image:
        file_name = f"{image.filename}"
        file_bytes = await image.read()
        try:
            supabase.storage.from_("chat-images").upload(
                path=file_name,
                file=file_bytes,
                file_options={"content-type": image.content_type, "upsert": "true"}
            )
            image_url = supabase.storage.from_("chat-images").get_public_url(file_name)
        except Exception as e:
            print(f"Failed to upload image: {e}")
            raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")

    # 2. Save user message to database
    supabase.table("messages").insert({
        "role": "user",
        "content": text or "[Image Only]",
        "image_url": image_url
    }).execute()

    # 3. Fetch settings for context
    settings_res = supabase.table("settings").select("*").eq("id", 1).execute()
    settings = settings_res.data[0] if settings_res.data else {
        "character_name": "Assistant",
        "system_prompt": "You are a helpful assistant.",
        "user_name": "User"
    }

    # 4. Fetch recent messages for history
    history_res = supabase.table("messages").select("*").order("created_at", desc=True).limit(20).execute()
    history = list(reversed(history_res.data))

    contents = []
    for msg in history:
        contents.append(types.Content(
            role="user" if msg["role"] == "user" else "model",
            parts=[types.Part.from_text(text=msg["content"])]
        ))

    current_parts = []
    if text:
        current_parts.append(types.Part.from_text(text=text))
    if image:
        current_parts.append(types.Part.from_bytes(data=file_bytes, mime_type=image.content_type))
        
    if len(contents) > 0 and contents[-1].role == "user" and contents[-1].parts[0].text == (text or "[Image Only]"):
        contents[-1] = types.Content(role="user", parts=current_parts)
    else:
        contents.append(types.Content(role="user", parts=current_parts))

    # 5. Call Gemini
    system_instruction = f"{settings['system_prompt']}\n\nYou are {settings['character_name']}. The user's name is {settings['user_name']}."
    
    response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction
        )
    )

    assistant_reply = response.text

    # 6. Save assistant reply to database
    supabase.table("messages").insert({
        "role": "assistant",
        "content": assistant_reply,
        "image_url": None
    }).execute()

    return {"reply": assistant_reply}
