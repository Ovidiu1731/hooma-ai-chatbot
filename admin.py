"""
Hooma AI Chatbot Admin Panel
Simple admin interface for monitoring and configuration
"""

import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
import secrets

# Import from main app
from app import sessions, config

# Admin configuration
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-this-password")

# Security
security = HTTPBasic()
templates = Jinja2Templates(directory="templates")

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def get_session_stats() -> Dict[str, Any]:
    """Get statistics about chat sessions"""
    now = datetime.now(timezone.utc)
    total_sessions = len(sessions)
    active_sessions = 0
    
    message_counts = []
    session_durations = []
    
    for session_id, session_data in sessions.items():
        last_activity = datetime.fromisoformat(session_data["last_activity"].replace("Z", "+00:00"))
        created_at = datetime.fromisoformat(session_data["created_at"].replace("Z", "+00:00"))
        
        # Active if activity within last hour
        if (now - last_activity).total_seconds() < 3600:
            active_sessions += 1
        
        message_counts.append(len(session_data["messages"]))
        session_durations.append((last_activity - created_at).total_seconds() / 60)  # minutes
    
    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "avg_messages_per_session": sum(message_counts) / len(message_counts) if message_counts else 0,
        "avg_session_duration_minutes": sum(session_durations) / len(session_durations) if session_durations else 0,
        "total_messages": sum(message_counts)
    }

def get_recent_conversations(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent conversations for review"""
    recent_sessions = []
    
    for session_id, session_data in sessions.items():
        if session_data["messages"]:
            last_activity = datetime.fromisoformat(session_data["last_activity"].replace("Z", "+00:00"))
            
            # Get last few messages
            recent_messages = session_data["messages"][-3:]  # Last 3 messages
            
            recent_sessions.append({
                "session_id": session_id[:8] + "...",  # Truncated for privacy
                "last_activity": last_activity.strftime("%Y-%m-%d %H:%M UTC"),
                "message_count": len(session_data["messages"]),
                "recent_messages": recent_messages,
                "user_info": session_data.get("user_info", {})
            })
    
    # Sort by last activity
    recent_sessions.sort(key=lambda x: x["last_activity"], reverse=True)
    return recent_sessions[:limit]

# Admin routes (to be included in main app)
admin_routes = []

def create_admin_routes(app: FastAPI):
    """Create admin routes and add them to the main app"""
    
    @app.get("/admin", response_class=HTMLResponse)
    async def admin_dashboard(request: Request, admin_user: str = Depends(verify_admin)):
        """Admin dashboard"""
        stats = get_session_stats()
        recent_conversations = get_recent_conversations()
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Hooma AI Chatbot - Admin Dashboard</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #2563eb; }}
                .stat-label {{ color: #666; margin-top: 5px; }}
                .section {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
                .conversation {{ border: 1px solid #e5e5e5; border-radius: 6px; padding: 15px; margin: 10px 0; }}
                .message {{ margin: 8px 0; padding: 8px; border-radius: 6px; }}
                .user-message {{ background: #e3f2fd; }}
                .assistant-message {{ background: #f3e5f5; }}
                .controls {{ display: flex; gap: 10px; margin: 20px 0; }}
                .btn {{ padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; }}
                .btn:hover {{ background: #1d4ed8; }}
                .btn-danger {{ background: #ef4444; }}
                .btn-danger:hover {{ background: #dc2626; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e5e5e5; }}
                th {{ background: #f8f9fa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Hooma AI Chatbot - Admin Dashboard</h1>
                    <p>Monitor and manage your AI chatbot deployment</p>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">{stats['total_sessions']}</div>
                        <div class="stat-label">Total Sessions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{stats['active_sessions']}</div>
                        <div class="stat-label">Active Sessions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{stats['total_messages']}</div>
                        <div class="stat-label">Total Messages</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{stats['avg_messages_per_session']:.1f}</div>
                        <div class="stat-label">Avg Messages/Session</div>
                    </div>
                </div>
                
                <div class="controls">
                    <a href="/admin/clear-sessions" class="btn btn-danger" onclick="return confirm('Clear all sessions? This cannot be undone.')">Clear All Sessions</a>
                    <a href="/admin/export-data" class="btn">Export Data</a>
                    <a href="/admin/config" class="btn">Configuration</a>
                    <a href="/api/health" class="btn">Health Check</a>
                </div>
                
                <div class="section">
                    <h2>Recent Conversations</h2>
                    {generate_conversations_html(recent_conversations)}
                </div>
                
                <div class="section">
                    <h2>System Information</h2>
                    <table>
                        <tr><th>AI Provider</th><td>{config.AI_PROVIDER}</td></tr>
                        <tr><th>Model</th><td>{config.OPENAI_MODEL if config.AI_PROVIDER == 'openai' else config.ANTHROPIC_MODEL}</td></tr>
                        <tr><th>Rate Limit (per minute)</th><td>{config.RATE_LIMIT_PER_MINUTE}</td></tr>
                        <tr><th>Debug Mode</th><td>{'Yes' if config.DEBUG else 'No'}</td></tr>
                        <tr><th>Contact Email</th><td>{config.CONTACT_EMAIL}</td></tr>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content

    @app.get("/admin/clear-sessions")
    async def clear_sessions(admin_user: str = Depends(verify_admin)):
        """Clear all chat sessions"""
        global sessions
        sessions.clear()
        return RedirectResponse("/admin", status_code=302)

    @app.get("/admin/export-data")
    async def export_data(admin_user: str = Depends(verify_admin)):
        """Export session data as JSON"""
        from fastapi.responses import JSONResponse
        
        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "stats": get_session_stats(),
            "sessions": [
                {
                    "session_id": session_id,
                    "created_at": session_data["created_at"],
                    "last_activity": session_data["last_activity"],
                    "message_count": len(session_data["messages"]),
                    "messages": session_data["messages"],
                    "user_info": session_data.get("user_info", {})
                }
                for session_id, session_data in sessions.items()
            ]
        }
        
        return JSONResponse(
            content=export_data,
            headers={
                "Content-Disposition": f"attachment; filename=hooma-chatbot-data-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            }
        )

    @app.get("/admin/config", response_class=HTMLResponse)
    async def config_page(request: Request, admin_user: str = Depends(verify_admin)):
        """Configuration page"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Hooma AI Chatbot - Configuration</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .section {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
                .form-group {{ margin-bottom: 15px; }}
                label {{ display: block; margin-bottom: 5px; font-weight: 500; }}
                input, textarea, select {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }}
                .btn {{ padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; }}
                .btn:hover {{ background: #1d4ed8; }}
                .back-link {{ color: #2563eb; text-decoration: none; }}
                .config-item {{ padding: 10px; border-bottom: 1px solid #e5e5e5; }}
                .config-item:last-child {{ border-bottom: none; }}
                .code {{ background: #f8f9fa; padding: 15px; border-radius: 4px; font-family: monospace; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Configuration</h1>
                    <a href="/admin" class="back-link">← Back to Dashboard</a>
                </div>
                
                <div class="section">
                    <h2>Current Configuration</h2>
                    <div class="config-item"><strong>AI Provider:</strong> {config.AI_PROVIDER}</div>
                    <div class="config-item"><strong>Model:</strong> {config.OPENAI_MODEL if config.AI_PROVIDER == 'openai' else config.ANTHROPIC_MODEL}</div>
                    <div class="config-item"><strong>Rate Limit:</strong> {config.RATE_LIMIT_PER_MINUTE}/minute</div>
                    <div class="config-item"><strong>Widget Color:</strong> {config.WIDGET_PRIMARY_COLOR}</div>
                    <div class="config-item"><strong>Contact Email:</strong> {config.CONTACT_EMAIL}</div>
                </div>
                
                <div class="section">
                    <h2>Widget Embed Code</h2>
                    <p>Copy this code to your Webflow site:</p>
                    <div class="code">
&lt;!-- Hooma AI Chatbot --&gt;<br>
&lt;link rel="stylesheet" href="{request.url.scheme}://{request.url.netloc}/embed/widget.css"&gt;<br>
&lt;script src="{request.url.scheme}://{request.url.netloc}/embed/widget.js"&gt;&lt;/script&gt;<br>
&lt;script&gt;<br>
&nbsp;&nbsp;HoomaChatbot.init({{<br>
&nbsp;&nbsp;&nbsp;&nbsp;apiEndpoint: '{request.url.scheme}://{request.url.netloc}',<br>
&nbsp;&nbsp;&nbsp;&nbsp;primaryColor: '{config.WIDGET_PRIMARY_COLOR}',<br>
&nbsp;&nbsp;&nbsp;&nbsp;position: 'bottom-right'<br>
&nbsp;&nbsp;}});<br>
&lt;/script&gt;
                    </div>
                </div>
                
                <div class="section">
                    <h2>Environment Variables</h2>
                    <p>To change configuration, update these environment variables in Railway:</p>
                    <div class="code">
AI_PROVIDER={config.AI_PROVIDER}<br>
RATE_LIMIT_REQUESTS_PER_MINUTE={config.RATE_LIMIT_PER_MINUTE}<br>
WIDGET_PRIMARY_COLOR={config.WIDGET_PRIMARY_COLOR}<br>
CONTACT_EMAIL={config.CONTACT_EMAIL}<br>
DEBUG={str(config.DEBUG).lower()}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content

def generate_conversations_html(conversations: List[Dict[str, Any]]) -> str:
    """Generate HTML for recent conversations"""
    if not conversations:
        return "<p>No recent conversations found.</p>"
    
    html = ""
    for conv in conversations:
        html += f"""
        <div class="conversation">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <strong>Session: {conv['session_id']}</strong>
                <small>{conv['last_activity']} ({conv['message_count']} messages)</small>
            </div>
        """
        
        for msg in conv['recent_messages']:
            role_class = "user-message" if msg['role'] == 'user' else "assistant-message"
            content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
            html += f'<div class="message {role_class}"><strong>{msg["role"].title()}:</strong> {content}</div>'
        
        if conv['user_info']:
            html += f"<div style='margin-top: 10px; font-size: 0.9em; color: #666;'>User Info: {conv['user_info'].get('url', 'N/A')}</div>"
        
        html += "</div>"
    
    return html

# Export function to integrate with main app
def setup_admin(app: FastAPI):
    """Setup admin routes in the main FastAPI app"""
    create_admin_routes(app)
