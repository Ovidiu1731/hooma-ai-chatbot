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
            return "I'm sorry, but the AI service is currently unavailable. Please try again later or contact our team directly."
            
    except Exception as e:
        print(f"AI API Error: {e}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment, or feel free to contact our team directly for immediate assistance."

# API Routes
@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main chat interface for testing"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hooma AI Chatbot - Test Interface</title>
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
                <h1>Hooma AI Chatbot</h1>
                <p>Test Interface - AI Business Solutions & Growth Systems</p>
            </div>
            <div id="chatArea" class="chat-area">
                <div class="message assistant">
                    <strong>Hooma AI:</strong> Hello! I'm here to help you learn about Hooma's AI business solutions and growth systems. How can I assist you today?
                </div>
            </div>
            <div class="input-area">
                <input type="text" id="messageInput" placeholder="Type your message here..." />
                <button id="sendButton" onclick="sendMessage()">Send</button>
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
                userDiv.innerHTML = `<strong>You:</strong> ${message}`;
                chatArea.appendChild(userDiv);
                
                // Clear input and disable button
                input.value = '';
                button.disabled = true;
                button.textContent = 'Sending...';
                
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
                    assistantDiv.innerHTML = `<strong>Hooma AI:</strong> ${data.response}`;
                    chatArea.appendChild(assistantDiv);
                    
                } catch (error) {
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'message assistant';
                    errorDiv.innerHTML = `<strong>Error:</strong> Failed to send message. Please try again.`;
                    chatArea.appendChild(errorDiv);
                }
                
                // Re-enable button and scroll to bottom
                button.disabled = false;
                button.textContent = 'Send';
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
async def get_widget_js():
    """Serve the widget JavaScript file"""
    return FileResponse(
        path=Path(__file__).parent / "static" / "widget.js",
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600"}
    )

@app.get("/embed/widget.css")
async def get_widget_css():
    """Serve the widget CSS file"""
    return FileResponse(
        path=Path(__file__).parent / "static" / "widget.css",
        media_type="text/css",
        headers={"Cache-Control": "public, max-age=3600"}
    )

@app.get("/test", response_class=HTMLResponse)
async def simple_test():
    """Simple test page for debugging widget"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Widget Test</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f0f0f0; }
            .debug { background: yellow; padding: 10px; margin: 10px 0; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>Hooma Widget Test Page</h1>
        <div class="debug">
            <strong>Debug Info:</strong>
            <div id="debug-info">Loading...</div>
        </div>
        
        <p>Check the bottom-right corner for the chat widget.</p>
        <p>Open browser console (F12) to see debug logs.</p>
        
        <link rel="stylesheet" href="/embed/widget.css">
        <script src="/embed/widget.js"></script>
        <script>
            document.getElementById('debug-info').innerHTML = 'Files loaded. Initializing widget...';
            
            console.log('=== WIDGET DEBUG START ===');
            console.log('window.HoomaChatbot:', window.HoomaChatbot);
            
            if (window.HoomaChatbot) {
                console.log('HoomaChatbot found, initializing...');
                HoomaChatbot.init({
                    apiEndpoint: window.location.origin,
                    primaryColor: '#ff0080',
                    secondaryColor: '#e91e63',
                    position: 'bottom-right'
                });
                document.getElementById('debug-info').innerHTML = 'Widget initialized!';
            } else {
                console.error('HoomaChatbot not found!');
                document.getElementById('debug-info').innerHTML = 'ERROR: HoomaChatbot not found!';
            }
            
            console.log('=== WIDGET DEBUG END ===');
        </script>
    </body>
    </html>
    """

@app.get("/embed/demo.html", response_class=HTMLResponse)
async def embed_demo(request: Request):
    """Demo page showing how to embed the widget"""
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hooma Chatbot Widget Demo</title>
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
            <h1>Hooma AI Chatbot Widget Demo</h1>
            <p>This page demonstrates how the Hooma AI chatbot widget appears on your website.</p>
            
            <h2>How to Embed</h2>
            <p>Add this code to your website's HTML (preferably before the closing &lt;/body&gt; tag):</p>
            
            <div class="code-block">
&lt;!-- Hooma AI Chatbot --&gt;<br>
&lt;link rel="stylesheet" href="{base_url}/embed/widget.css"&gt;<br>
&lt;script src="{base_url}/embed/widget.js"&gt;&lt;/script&gt;<br>
&lt;script&gt;<br>
&nbsp;&nbsp;HoomaChatbot.init({{<br>
&nbsp;&nbsp;&nbsp;&nbsp;apiEndpoint: '{base_url}',<br>
&nbsp;&nbsp;&nbsp;&nbsp;primaryColor: '#ff0080',<br>
&nbsp;&nbsp;&nbsp;&nbsp;secondaryColor: '#e91e63',<br>
&nbsp;&nbsp;&nbsp;&nbsp;position: 'bottom-right',<br>
&nbsp;&nbsp;&nbsp;&nbsp;title: 'Hooma AI Assistant',<br>
&nbsp;&nbsp;&nbsp;&nbsp;subtitle: 'Online • AI Business Solutions'<br>
&nbsp;&nbsp;}});<br>
&lt;/script&gt;
            </div>
            
            <h2>Features</h2>
            <ul>
                <li>Responsive design that works on all devices</li>
                <li>Customizable colors and positioning</li>
                <li>Session management for conversation continuity</li>
                <li>Professional UI matching Hooma's brand</li>
                <li>AI-powered responses using Hooma's knowledge base</li>
            </ul>
            
            <p>Try the chatbot widget in the bottom-right corner of this page!</p>
        </div>
        
        <link rel="stylesheet" href="/embed/widget.css">
        <script src="/embed/widget.js"></script>
        <script>
            // Wait for DOM to be ready
            document.addEventListener('DOMContentLoaded', function() {{
                console.log('Initializing Hooma Chatbot...');
                if (window.HoomaChatbot) {{
                    HoomaChatbot.init({{
                        apiEndpoint: window.location.origin,
                        primaryColor: '#ff0080',
                        secondaryColor: '#e91e63',
                        position: 'bottom-right',
                        title: 'Hooma AI Assistant',
                        subtitle: 'Online • AI Business Solutions',
                        welcomeMessage: 'Welcome to Hooma! I\'m your AI assistant, ready to help you discover how our AI-powered growth systems can transform your business. What would you like to know?'
                    }});
                    console.log('Hooma Chatbot initialized successfully!');
                }} else {{
                    console.error('HoomaChatbot not found. Check if widget.js loaded properly.');
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
