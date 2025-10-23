"""
Hooma AI Chatbot Backend
A FastAPI application for the Hooma AI chatbot with OpenAI/Anthropic integration
"""

import os
import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, Field
import openai
import anthropic
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
class Config:
    # AI Provider settings
    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai").lower()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
    
    # App settings
    APP_NAME = os.getenv("APP_NAME", "Hooma AI Chatbot")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "30"))
    RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "500"))
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Business settings
    CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "contact@hooma.io")
    WEBSITE_URL = os.getenv("WEBSITE_URL", "https://hooma.io")
    
    # Widget customization
    WIDGET_PRIMARY_COLOR = os.getenv("WIDGET_PRIMARY_COLOR", "#2563eb")
    WIDGET_POSITION = os.getenv("WIDGET_POSITION", "bottom-right")

config = Config()

# Initialize AI clients
openai_client = None
anthropic_client = None

if config.AI_PROVIDER == "openai" and config.OPENAI_API_KEY:
    openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
elif config.AI_PROVIDER == "anthropic" and config.ANTHROPIC_API_KEY:
    anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    description="AI-powered chatbot for Hooma business website",
    version="1.0.0",
    docs_url="/docs" if config.DEBUG else None,
    redoc_url="/redoc" if config.DEBUG else None
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load knowledge base and system prompt
def load_text_file(filename: str) -> str:
    """Load text content from config files"""
    try:
        file_path = Path(__file__).parent / "config" / filename
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: {filename} not found")
        return ""

SYSTEM_PROMPT = load_text_file("system_prompt.txt")
KNOWLEDGE_BASE = load_text_file("knowledge_base.txt")

# In-memory session storage (for production, consider Redis)
sessions: Dict[str, Dict[str, Any]] = {}

# Pydantic models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(default=None, description="Message timestamp")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    user_info: Optional[Dict[str, Any]] = Field(default=None, description="Optional user information")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant response")
    session_id: str = Field(..., description="Session identifier")
    timestamp: str = Field(..., description="Response timestamp")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    ai_provider: str

# Helper functions
def generate_session_id() -> str:
    """Generate a unique session ID"""
    return f"session_{int(time.time() * 1000)}_{os.urandom(4).hex()}"

def get_session(session_id: str) -> Dict[str, Any]:
    """Get or create a chat session"""
    if session_id not in sessions:
        sessions[session_id] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "messages": [],
            "user_info": {},
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
    else:
        sessions[session_id]["last_activity"] = datetime.now(timezone.utc).isoformat()
    
    return sessions[session_id]

def cleanup_old_sessions():
    """Remove sessions older than 24 hours"""
    current_time = datetime.now(timezone.utc)
    to_remove = []
    
    for session_id, session_data in sessions.items():
        last_activity = datetime.fromisoformat(session_data["last_activity"].replace("Z", "+00:00"))
        if (current_time - last_activity).total_seconds() > 86400:  # 24 hours
            to_remove.append(session_id)
    
    for session_id in to_remove:
        del sessions[session_id]

async def get_ai_response(messages: List[Dict[str, str]]) -> str:
    """Get response from AI provider"""
    try:
        # Prepare system message with knowledge base
        system_message = f"{SYSTEM_PROMPT}\n\nKNOWLEDGE BASE:\n{KNOWLEDGE_BASE}"
        
        if config.AI_PROVIDER == "openai" and openai_client:
            # OpenAI API call
            response = await asyncio.to_thread(
                openai_client.chat.completions.create,
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_message},
                    *messages
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
            
        elif config.AI_PROVIDER == "anthropic" and anthropic_client:
            # Anthropic API call
            # Convert messages to Claude format
            claude_messages = []
            for msg in messages:
                if msg["role"] != "system":
                    claude_messages.append({
                        "role": msg["role"], 
                        "content": msg["content"]
                    })
            
            response = await asyncio.to_thread(
                anthropic_client.messages.create,
                model=config.ANTHROPIC_MODEL,
                max_tokens=1000,
                system=system_message,
                messages=claude_messages
            )
            return response.content[0].text
            
        else:
            return "Îmi pare rău, serviciul AI nu este disponibil momentan. Te rog încearcă mai târziu sau contactează-ne direct."
            
    except Exception as e:
        print(f"AI API Error: {e}")
        return "Îmi pare rău, întâmpin probleme tehnice. Te rog încearcă din nou în scurt timp sau scrie-ne direct."

# API Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main chat interface for testing"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ro">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Asistentul Hooma - Interfață de test</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden; }
            .header { background: #2563eb; color: white; padding: 20px; text-align: center; }
            .chat-area { height: 400px; overflow-y: auto; padding: 20px; border-bottom: 1px solid #e5e5e5; }
            .message { margin: 10px 0; padding: 10px; border-radius: 8px; max-width: 80%; }
            .user { background: #e3f2fd; margin-left: auto; text-align: right; }
            .assistant { background: #f3e5f5; }
            .input-area { padding: 20px; display: flex; gap: 10px; }
            .input-area input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 6px; }
            .input-area button { padding: 12px 24px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; }
            .input-area button:hover { background: #1d4ed8; }
            .input-area button:disabled { background: #9ca3af; cursor: not-allowed; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Asistentul Hooma</h1>
                <p>Interfață de test — Consultanță și automatizări AI</p>
            </div>
            <div id="chatArea" class="chat-area">
                <div class="message assistant">
                    <strong>Hooma:</strong> Salut! Sunt asistentul lui Ovidiu. Te pot ajuta cu întrebări despre strategie și automatizări AI pentru afaceri educaționale.
                </div>
            </div>
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Scrie mesajul tău..." />
                <button id="sendButton" onclick="sendMessage()">Trimite</button>
            </div>
        </div>

        <script>
            let sessionId = null;
            
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const button = document.getElementById('sendButton');
                const chatArea = document.getElementById('chatArea');
                
                const message = input.value.trim();
                if (!message) return;
                
                // Add user message to chat
                const userDiv = document.createElement('div');
                userDiv.className = 'message user';
                userDiv.innerHTML = `<strong>Tu:</strong> ${message}`;
                chatArea.appendChild(userDiv);
                
                // Clear input and disable button
                input.value = '';
                button.disabled = true;
                button.textContent = 'Se trimite...';
                
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            message: message,
                            session_id: sessionId
                        })
                    });
                    
                    const data = await response.json();
                    sessionId = data.session_id;
                    
                    // Add assistant response to chat
                    const assistantDiv = document.createElement('div');
                    assistantDiv.className = 'message assistant';
                    assistantDiv.innerHTML = `<strong>Hooma:</strong> ${data.response}`;
                    chatArea.appendChild(assistantDiv);
                    
                } catch (error) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'message assistant';
                    errorDiv.innerHTML = `<strong>Eroare:</strong> Nu am putut trimite mesajul. Încearcă din nou.`;
                    chatArea.appendChild(errorDiv);
                }
                
                // Re-enable button and scroll to bottom
                button.disabled = false;
                button.textContent = 'Trimite';
                chatArea.scrollTop = chatArea.scrollHeight;
            }
            
            // Allow Enter key to send message
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/health")
async def basic_health():
    """Basic health check for Railway"""
    return {"status": "ok", "service": "hooma-chatbot"}

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check endpoint"""
    # Check if we have basic configuration
    ai_status = "configured" if (config.OPENAI_API_KEY or config.ANTHROPIC_API_KEY) else "no_api_key"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        ai_provider=f"{config.AI_PROVIDER}_{ai_status}"
    )

@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute")
async def chat(request: Request, chat_request: ChatRequest, background_tasks: BackgroundTasks):
    """Main chat endpoint"""
    # Generate session ID if not provided
    session_id = chat_request.session_id or generate_session_id()
    
    # Get or create session
    session = get_session(session_id)
    
    # Update user info if provided
    if chat_request.user_info:
        session["user_info"].update(chat_request.user_info)
    
    # Add user message to session
    user_message = {
        "role": "user",
        "content": chat_request.message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    session["messages"].append(user_message)
    
    # Prepare messages for AI (keep last 10 messages for context)
    recent_messages = session["messages"][-10:]
    ai_messages = [{"role": msg["role"], "content": msg["content"]} for msg in recent_messages]
    
    # Get AI response
    ai_response = await get_ai_response(ai_messages)
    
    # Add assistant message to session
    assistant_message = {
        "role": "assistant", 
        "content": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    session["messages"].append(assistant_message)
    
    # Schedule cleanup of old sessions
    background_tasks.add_task(cleanup_old_sessions)
    
    return ChatResponse(
        response=ai_response,
        session_id=session_id,
        timestamp=assistant_message["timestamp"]
    )

@app.get("/embed/widget.js")
async def get_widget_js(v: str = None):
    """Serve the widget JavaScript file with cache-busting"""
    return FileResponse(
        path=Path(__file__).parent / "static" / "widget.js",
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "ETag": f"hooma-js-{v or 'latest'}"
        }
    )

@app.get("/static/images/hooma-logo.png")
async def get_logo():
    """Serve the Hooma logo"""
    return FileResponse(
        path=Path(__file__).parent / "static" / "images" / "hooma-logo.png",
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )

@app.get("/embed/widget.css")
async def get_widget_css(v: str = None):
    """Serve the widget CSS file with cache-busting"""
    return FileResponse(
        path=Path(__file__).parent / "static" / "widget.css",
        media_type="text/css",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "ETag": f"hooma-css-{v or 'latest'}"
        }
    )

@app.get("/test", response_class=HTMLResponse)
async def simple_test():
    """Simple test page for debugging widget"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test widget</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f0f0f0; }
            .debug { background: yellow; padding: 10px; margin: 10px 0; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>Pagină test widget Hooma</h1>
        <div class="debug">
            <strong>Informații debug:</strong>
            <div id="debug-info">Se încarcă...</div>
        </div>
        
        <p>Verifică colțul din dreapta jos pentru widgetul de chat.</p>
        <p>Deschide consola browserului (F12) pentru jurnalele de debug.</p>
        
        <link rel="stylesheet" href="/embed/widget.css">
        <script src="/embed/widget.js"></script>
        <script>
            document.getElementById('debug-info').innerHTML = 'Fișiere încărcate. Inițializez widgetul...';
            
            console.log('=== WIDGET DEBUG START ===');
            console.log('window.HoomaChatbot:', window.HoomaChatbot);
            
            if (window.HoomaChatbot) {
                console.log('HoomaChatbot găsit, inițializez...');
                HoomaChatbot.init({
                    apiEndpoint: window.location.origin,
                    primaryColor: '#ff5da2',
                    secondaryColor: '#e91e63',
                    position: 'bottom-right'
                });
                document.getElementById('debug-info').innerHTML = 'Widget inițializat!';
            } else {
                console.error('HoomaChatbot nu a fost găsit!');
                document.getElementById('debug-info').innerHTML = 'EROARE: HoomaChatbot nu a fost găsit!';
            }
            
            console.log('=== WIDGET DEBUG END ===');
        </script>
    </body>
    </html>
    """

@app.get("/embed/standalone.html", response_class=HTMLResponse)
async def standalone_widget(request: Request):
    """Self-contained widget for testing - includes all CSS/JS inline"""
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    # Read the CSS and JS files
    css_path = Path(__file__).parent / "static" / "widget.css"
    js_path = Path(__file__).parent / "static" / "widget.js"
    
    css_content = css_path.read_text()
    js_content = js_path.read_text()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ro">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Asistentul Hooma — Test standalone</title>
        <style>
        {css_content}
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 40px; background: #000; color: white; }}
        .debug-info {{ position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 5px; font-size: 12px; z-index: 10000; }}
        </style>
    </head>
    <body>
        <div class="debug-info">
            ✅ Test widget standalone<br>
            🎯 CSS & JS încărcate inline<br>
            🔗 API: {base_url}
        </div>
        
        <h1>Asistentul Hooma — Test standalone</h1>
        <p>Această versiune are CSS/JS integrate inline pentru a evita probleme de cache.</p>
        <p>Caută bula roz din colțul din dreapta jos.</p>
        
        <script>
        {js_content}
        
        // Initialize immediately
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('🚀 Inițializez widgetul standalone...');
            if (window.HoomaChatbot) {{
                HoomaChatbot.init({{
                    apiEndpoint: '{base_url}',
                    primaryColor: '#ff5da2',
                    secondaryColor: '#e91e63',
                    position: 'bottom-right',
                    title: 'Asistentul Hooma',
                    subtitle: 'Consultanță și automatizări AI',
                    welcomeMessage: 'Salut! Te pot ajuta să afli despre soluțiile noastre AI pentru afaceri și sistemele de creștere. Ce ai dori să știi?'
                }});
                console.log('✅ Widgetul standalone a fost inițializat cu succes!');
            }} else {{
                console.error('❌ HoomaChatbot nu a fost găsit în modul standalone');
            }}
        }});
        </script>
    </body>
    </html>
    """
    return html_content

@app.get("/embed/demo.html", response_class=HTMLResponse)
async def embed_demo(request: Request):
    """Demo page showing how to embed the widget"""
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ro">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Demo widget Asistentul Hooma</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 40px; background: #f8f9fa; }}
            .demo-content {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2563eb; }}
            .code-block {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 20px; margin: 20px 0; font-family: 'Courier New', monospace; overflow-x: auto; }}
        </style>
        <link rel="stylesheet" href="/embed/widget.css">
    </head>
    <body>
        <div class="demo-content">
            <h1>Demo widget — Asistentul Hooma</h1>
            <p>Această pagină demonstrează cum apare widgetul Asistentului Hooma pe site‑ul tău.</p>
            
            <h2>Cum îl integrezi</h2>
            <p>Adaugă acest cod în HTML (ideal înainte de &lt;/body&gt;):</p>
            
            <div class="code-block">
&lt;!-- Hooma AI Chatbot --&gt;<br>
&lt;link rel="stylesheet" href="{base_url}/embed/widget.css"&gt;<br>
&lt;script src="{base_url}/embed/widget.js"&gt;&lt;/script&gt;<br>
&lt;script&gt;<br>
&nbsp;&nbsp;HoomaChatbot.init({{<br>
&nbsp;&nbsp;&nbsp;&nbsp;apiEndpoint: '{base_url}',<br>
&nbsp;&nbsp;&nbsp;&nbsp;primaryColor: '#ff5da2',<br>
&nbsp;&nbsp;&nbsp;&nbsp;secondaryColor: '#e91e63',<br>
&nbsp;&nbsp;&nbsp;&nbsp;position: 'bottom-right',<br>
&nbsp;&nbsp;&nbsp;&nbsp;title: 'Asistentul Hooma',<br>
&nbsp;&nbsp;&nbsp;&nbsp;subtitle: 'Consultanță și automatizări AI'<br>
&nbsp;&nbsp;}});<br>
&lt;/script&gt;
            </div>
            
            <h2>Funcționalități</h2>
            <ul>
                <li>Design responsiv pe toate dispozitivele</li>
                <li>Culori și poziționare personalizabile</li>
                <li>Gestionarea sesiunii pentru context de conversație</li>
                <li>UI profesional, aliniat cu brandul Hooma</li>
                <li>Răspunsuri AI bazate pe baza de cunoștințe Hooma</li>
            </ul>
            
            <p>Încearcă widgetul în colțul din dreapta jos al paginii!</p>
        </div>
        
        <link rel="stylesheet" href="/embed/widget.css">
        <script src="/embed/widget.js"></script>
        <script>
            // Wait for DOM to be ready
            document.addEventListener('DOMContentLoaded', function() {{
                console.log('Inițializez Asistentul Hooma...');
                if (window.HoomaChatbot) {{
                    HoomaChatbot.init({{
                        apiEndpoint: window.location.origin,
                        primaryColor: '#ff5da2',
                        secondaryColor: '#e91e63',
                        position: 'bottom-right',
                        title: 'Asistentul Hooma',
                        subtitle: 'Consultanță și automatizări AI',
                        welcomeMessage: 'Salut! Te pot ajuta să afli despre soluțiile noastre AI pentru afaceri și sistemele de creștere. Ce ai dori să știi?'
                    }});
                    console.log('Asistentul Hooma a fost inițializat!');
                }} else {{
                    console.error('HoomaChatbot nu a fost găsit. Verifică încărcarea widget.js.');
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_content

# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

# Setup admin panel (optional - only if admin credentials are set)
if os.getenv("ADMIN_USERNAME") and os.getenv("ADMIN_PASSWORD"):
    try:
        from admin import setup_admin
        setup_admin(app)
        print("✅ Admin panel enabled at /admin")
    except Exception as e:
        print(f"⚠️ Admin panel not available: {e}")
else:
    print("ℹ️ Admin panel disabled (set ADMIN_USERNAME and ADMIN_PASSWORD to enable)")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=config.DEBUG
    )
