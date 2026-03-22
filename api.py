from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional
from db import db
from google import genai
import uuid
from datetime import datetime
import os

# --- Google Genai Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", )
ai_client = None

if GOOGLE_API_KEY:
    ai_client = genai.Client(api_key=GOOGLE_API_KEY)
    print("✅ Google Genai AI Configured")
else:
    print("⚠️ WARNING: GOOGLE_API_KEY not set. Chat will be unavailable.")

# --- Initial Data ---
INITIAL_DISTROS = [
    {"name": "Lubuntu", "min_ram": 1, "gpu": "any", "desc": "Ultra-lightweight Ubuntu for old PCs", "url": "https://lubuntu.me/downloads/", "iso_url": "https://cdimage.ubuntu.com/lubuntu/releases/noble/release/lubuntu-24.04.4-desktop-amd64.iso"},
    {"name": "Linux Mint XFCE", "min_ram": 2, "gpu": "any", "desc": "Beginner friendly, Windows-like", "url": "https://linuxmint.com/download.php", "iso_url": "https://pub.linuxmint.io/stable/22.3/linuxmint-22.3-xfce-64bit.iso"},
    {"name": "Ubuntu MATE", "min_ram": 4, "gpu": "any", "desc": "Light but modern Ubuntu", "url": "https://ubuntu-mate.org/download/", "iso_url": "https://cdimage.ubuntu.com/ubuntu-mate/releases/noble/release/ubuntu-mate-24.04.4-desktop-amd64.iso"},
    {"name": "Fedora Workstation", "min_ram": 4, "gpu": "any", "desc": "Developer-focused cutting edge Linux", "url": "https://fedoraproject.org/workstation/", "iso_url": "https://download.fedoraproject.org/pub/fedora/linux/releases/43/Workstation/x86_64/iso/Fedora-Workstation-Live-43-1.6.x86_64.iso"},
    {"name": "Pop!_OS", "min_ram": 8, "gpu": "NVIDIA", "desc": "Best for NVIDIA laptops", "url": "https://pop.system76.com/", "iso_url": "https://iso.pop-os.org/24.04/amd64/nvidia/23/pop-os_24.04_amd64_nvidia_23.iso"},
    {"name": "Nobara", "min_ram": 8, "gpu": "NVIDIA", "desc": "Gaming optimized Fedora", "url": "https://nobaraproject.org/", "iso_url": "https://nobaraproject.org/"}
]

# --- Lifespan (replaces deprecated @app.on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if db is not None:
        try:
            count = await db.distros.count_documents({})
            if count == 0:
                await db.distros.insert_many(INITIAL_DISTROS)
                print("📦 Populated initial distros database")
        except Exception as e:
            print(f"Could not connect to MongoDB during startup: {e}")
    yield
    # Shutdown (nothing needed)

app = FastAPI(title="Linux Lifesaver API", lifespan=lifespan)

# --- Models ---
class Distro(BaseModel):
    name: str
    min_ram: int
    gpu: str
    desc: str
    url: str
    iso_url: str

class RecommendationRequest(BaseModel):
    ram: int
    cpu: str
    gpu: str
    storage: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: str = "general"

class ChatResponse(BaseModel):
    response: str
    session_id: str

# --- AI Helper ---
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]

def get_ai_response(system_instruction: str, prompt: str) -> str:
    if not ai_client:
        return "AI unavailable — set GOOGLE_API_KEY"
    full_prompt = f"{system_instruction}\n\n{prompt}"
    for model in GEMINI_MODELS:
        try:
            response = ai_client.models.generate_content(
                model=model,
                contents=full_prompt,
            )
            return response.text
        except Exception as e:
            print(f"Google Genai Error ({model}): {e}")
            continue
    return "I'm currently unable to reach the AI server. Please try again."

# --- Endpoints ---

@app.post("/recommend", response_model=List[Distro])
async def recommend_distros(specs: RecommendationRequest):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    query = {"min_ram": {"$lte": specs.ram}}
    cursor = db.distros.find(query)
    all_compatible = await cursor.to_list(length=100)

    final_recommendations = []
    for d in all_compatible:
        if d["gpu"] == "NVIDIA" and specs.gpu != "NVIDIA":
            continue
        final_recommendations.append(d)

    return final_recommendations[:5]

@app.post("/chat", response_model=ChatResponse)
async def chat_bot(request: ChatRequest):
    if db is None:
        raise HTTPException(status_code=503, detail="Database not connected")

    session_id = request.session_id or str(uuid.uuid4())
    message = request.message

    # Fetch last 3 messages from DB for conversation memory
    history_cursor = db.chat_sessions.find(
        {"session_id": session_id}
    ).sort("timestamp", -1).limit(3)
    history_docs = await history_cursor.to_list(length=3)
    history_text = ""
    for doc in reversed(history_docs):
        history_text += f"User: {doc['input']}\nAssistant: {doc['response']}\n"

    if request.context == "install":
        system_instruction = "You are a Linux Installation Expert. Provide concise, technical CLI commands for troubleshooting."
    else:
        system_instruction = "You are a friendly Linux Teacher. Explain clearly for beginners."

    full_prompt = f"{history_text}\nUser: {message}" if history_text else message
    response_text = get_ai_response(system_instruction, full_prompt)

    # Save to MongoDB
    await db.chat_sessions.insert_one({
        "session_id": session_id,
        "input": message,
        "response": response_text,
        "context": request.context,
        "timestamp": datetime.now(),
    })

    return ChatResponse(response=response_text, session_id=session_id)