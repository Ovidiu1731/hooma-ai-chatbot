# 🤖 Hooma AI Chatbot

A professional AI-powered chatbot for Hooma's business website, built with FastAPI and designed for seamless Webflow integration and Railway deployment.

## ✨ Features

### 🧠 AI-Powered Conversations
- **OpenAI GPT-4** or **Anthropic Claude** integration
- **Custom knowledge base** with comprehensive Hooma business information
- **Context-aware conversations** with session management
- **Intelligent lead qualification** and guidance

### 🎨 Professional Widget
- **Responsive design** for all devices (desktop, tablet, mobile)
- **Customizable branding** (colors, positioning, messaging)
- **Smooth animations** and professional UI
- **Typing indicators** and real-time messaging
- **Session persistence** for conversation continuity

### 🚀 Production Ready
- **Railway deployment** with automatic scaling
- **Rate limiting** and security features
- **CORS configuration** for cross-domain embedding
- **Health monitoring** and error handling
- **Admin dashboard** for monitoring and management

### 🔧 Easy Integration
- **One-click Webflow embedding** with simple code snippet
- **No external dependencies** beyond hosted files
- **Cross-browser compatibility**
- **SEO-friendly** implementation

## 📁 Project Structure

```
hooma-chatbot/
├── app.py                          # Main FastAPI application
├── admin.py                        # Admin dashboard (optional)
├── requirements.txt                # Python dependencies
├── railway.json                    # Railway deployment config
├── Dockerfile                      # Container configuration
├── Procfile                        # Process definition
├── runtime.txt                     # Python version
├── env.template                    # Environment variables template
├── .gitignore                      # Git ignore patterns
├── README.md                       # This file
├── DEPLOYMENT_GUIDE.md             # Detailed deployment instructions
├── config/
│   ├── system_prompt.txt           # AI system prompt
│   └── knowledge_base.txt          # Hooma business knowledge
├── static/
│   ├── widget.js                   # Chat widget JavaScript
│   └── widget.css                  # Widget styling
└── embed/
    ├── simple-embed.html           # Simple embed code
    └── webflow-embed-instructions.html  # Integration guide
```

## 🚀 Quick Start

### 1. Environment Setup

1. **Copy environment template:**
   ```bash
   cp env.template .env
   ```

2. **Configure API keys:**
   ```env
   # Choose your AI provider
   AI_PROVIDER=openai
   OPENAI_API_KEY=your_openai_api_key_here
   
   # OR use Anthropic
   AI_PROVIDER=anthropic
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

3. **Set security and customization:**
   ```env
   SECRET_KEY=your_random_secret_key
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=secure_password
   WIDGET_PRIMARY_COLOR=#2563eb
   ALLOWED_ORIGINS=https://hooma.io,https://www.hooma.io
   ```

### 2. Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Test the interface:**
   - Visit `http://localhost:8000` for the test chat interface
   - Visit `http://localhost:8000/admin` for the admin dashboard
   - Visit `http://localhost:8000/embed/demo.html` for widget demo

### 3. Deploy to Railway

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Railway:**
   - Connect your GitHub repository
   - Set environment variables
   - Deploy automatically

3. **Configure Webflow:**
   - Copy embed code from admin panel
   - Paste in Webflow custom code section
   - Publish your site

## 📊 Admin Dashboard

The admin dashboard provides:

- **Real-time statistics** (sessions, messages, activity)
- **Conversation monitoring** (recent chats, user insights)
- **Configuration management** (embed codes, settings)
- **Data export** (JSON format for analysis)
- **Health monitoring** (system status, performance)

Access at: `https://your-domain.railway.app/admin`

## 🎨 Customization

### Widget Appearance

```javascript
HoomaChatbot.init({
  apiEndpoint: 'https://your-domain.railway.app',
  primaryColor: '#2563eb',      // Main brand color
  secondaryColor: '#1d4ed8',    // Secondary color
  position: 'bottom-right',     // bottom-right, bottom-left, top-right, top-left
  title: 'Your Assistant',     // Chat window title
  subtitle: 'How can we help?', // Chat window subtitle
  welcomeMessage: 'Hello! How can I assist you today?',
  placeholder: 'Type your message...'
});
```

### Business Logic

Customize the AI behavior by editing:
- `config/system_prompt.txt` - AI personality and instructions
- `config/knowledge_base.txt` - Business information and FAQs

### Rate Limiting

```env
RATE_LIMIT_REQUESTS_PER_MINUTE=30   # Per IP address
RATE_LIMIT_REQUESTS_PER_HOUR=500    # Per IP address
```

## 🔒 Security Features

- **Input sanitization** and validation
- **Rate limiting** to prevent abuse
- **CORS protection** with domain whitelist
- **Session security** with secure tokens
- **Admin authentication** with HTTP Basic Auth
- **API key protection** with environment variables

## 📱 Mobile Optimization

The widget automatically adapts for mobile devices:
- **Responsive layout** that scales appropriately
- **Touch-friendly interface** with proper sizing
- **Full-screen mode** on small screens
- **Performance optimization** for mobile networks

## 🧪 Testing

### Manual Testing Checklist

- [ ] Chat bubble appears in correct position
- [ ] Widget opens and closes properly
- [ ] Messages send and receive responses
- [ ] Mobile responsiveness works
- [ ] Admin dashboard accessible
- [ ] Health check endpoint responds
- [ ] Custom branding applies correctly

### Automated Testing

```bash
# Health check
curl https://your-domain.railway.app/api/health

# Test chat API
curl -X POST https://your-domain.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how can you help?"}'
```

## 🐛 Troubleshooting

### Common Issues

**Widget not appearing:**
- Check Railway deployment status
- Verify embed code URL is correct
- Ensure CORS origins include your domain

**AI not responding:**
- Verify API keys are set correctly
- Check rate limits haven't been exceeded
- Review application logs for errors

**CORS errors:**
- Add your domain to `ALLOWED_ORIGINS`
- Ensure proper protocol (https/http)
- Check for subdomain variations

### Debug Mode

Enable debug mode for development:
```env
DEBUG=true
```

This provides:
- Detailed error messages
- FastAPI documentation at `/docs`
- Auto-reload on code changes

## 📈 Performance Optimization

### Production Settings

```env
DEBUG=false
RATE_LIMIT_REQUESTS_PER_MINUTE=30
RATE_LIMIT_REQUESTS_PER_HOUR=500
```

### Scaling Considerations

- **Railway Pro plan** for unlimited usage
- **Redis integration** for session storage at scale
- **CDN setup** for static files
- **Response caching** for common queries

## 🔧 API Reference

### Chat Endpoint

```http
POST /api/chat
Content-Type: application/json

{
  "message": "User message",
  "session_id": "optional_session_id",
  "user_info": {
    "url": "current_page_url",
    "referrer": "referrer_url"
  }
}
```

### Health Check

```http
GET /api/health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "ai_provider": "openai"
}
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

## 📄 License

This project is proprietary software for Hooma AI business use.

## 📞 Support

- **Email:** hello@hooma.io
- **Website:** [hooma.io](https://hooma.io)
- **Documentation:** See `DEPLOYMENT_GUIDE.md` for detailed setup instructions

## 🙏 Acknowledgments

- **FastAPI** for the robust web framework
- **OpenAI** and **Anthropic** for AI capabilities
- **Railway** for seamless deployment
- **Webflow** for website integration

---

**🎯 Ready to get started?** Check out the `DEPLOYMENT_GUIDE.md` for step-by-step deployment instructions!
