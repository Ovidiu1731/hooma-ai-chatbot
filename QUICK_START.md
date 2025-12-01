# 🚀 Hooma AI Chatbot - Quick Start Guide

Get your Hooma AI Chatbot up and running in under 10 minutes!

## ⚡ Prerequisites (2 minutes)

1. **Get an AI API key** (choose one):
   - [OpenAI API Key](https://platform.openai.com/api-keys) (recommended)
   - [Anthropic API Key](https://console.anthropic.com/)

2. **Sign up for Railway**: [railway.app](https://railway.app) (free tier available)

3. **GitHub account** for code deployment

## 🎯 Deploy in 5 Steps (8 minutes)

### Step 1: Get the Code (1 minute)
```bash
# Clone or download this repository
# The hooma-chatbot folder contains everything you need
```

### Step 2: Push to GitHub (2 minutes)
```bash
cd hooma-chatbot
git init
git add .
git commit -m "Initial Hooma AI Chatbot"
git remote add origin https://github.com/yourusername/hooma-chatbot.git
git push -u origin main
```

### Step 3: Deploy to Railway (3 minutes)
1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `hooma-chatbot` repository
5. Railway will automatically detect and deploy!

### Step 4: Configure Environment (2 minutes)
In Railway dashboard, add these variables:

**Required:**
```
AI_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here
ALLOWED_ORIGINS=https://hooma.io,https://www.hooma.io
```

**Optional:**
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure_password_here
WIDGET_PRIMARY_COLOR=#2563eb
```

### Step 5: Get Your Embed Code (30 seconds)
1. Copy your Railway URL (e.g., `https://hooma-chatbot-abc123.railway.app`)
2. Replace `YOUR-RAILWAY-DOMAIN` in the embed code below:

```html
<!-- Hooma AI Chatbot -->
<link rel="stylesheet" href="https://YOUR-RAILWAY-DOMAIN.railway.app/embed/widget.css">
<script src="https://YOUR-RAILWAY-DOMAIN.railway.app/embed/widget.js"></script>
<script>
  HoomaChatbot.init({
    apiEndpoint: 'https://YOUR-RAILWAY-DOMAIN.railway.app',
    primaryColor: '#2563eb',
    position: 'bottom-right'
  });
</script>
```

## 🌐 Add to Webflow (2 minutes)

1. **Open Webflow Designer**
2. **Go to Project Settings** (gear icon)
3. **Navigate to Custom Code tab**
4. **Paste embed code in Footer Code section**
5. **Save and Publish**

🎉 **Done!** Your AI chatbot is now live on your website.

## ✅ Quick Test

Visit these URLs to verify everything works:

- `https://your-domain.railway.app` - Test chat interface
- `https://your-domain.railway.app/api/health` - Health check
- `https://your-domain.railway.app/admin` - Admin dashboard
- `https://your-domain.railway.app/embed/demo.html` - Widget demo

## 🛠️ Customization (Optional)

### Change Colors
```javascript
HoomaChatbot.init({
  apiEndpoint: 'https://your-domain.railway.app',
  primaryColor: '#your-brand-color',    // Your brand color
  position: 'bottom-left',              // or top-right, top-left
  title: 'Your Company AI',             // Custom title
  welcomeMessage: 'How can we help you today?'
});
```

### Business Hours
```javascript
const hour = new Date().getHours();
const isOpen = hour >= 9 && hour < 18; // 9 AM - 6 PM

HoomaChatbot.init({
  apiEndpoint: 'https://your-domain.railway.app',
  subtitle: isOpen ? 'Team Online' : 'AI Assistant 24/7',
  welcomeMessage: isOpen 
    ? 'Our team is online! How can we help?' 
    : 'Our AI is here 24/7. How can we assist you?'
});
```

## 🔧 Troubleshooting

**Chatbot not appearing?**
- Check Railway deployment is running
- Verify embed code URL is correct
- Make sure you published your Webflow site

**No AI responses?**
- Verify API key is set correctly in Railway
- Check Railway logs for errors
- Ensure API key has sufficient credits

**Need help?**
- Run the test script: `python test_deployment.py`
- Check the admin dashboard for diagnostics
- Email: contact@hooma.ro

## 🎯 Next Steps

1. **Monitor usage** via admin dashboard
2. **Customize branding** to match your site
3. **Review conversations** to optimize responses
4. **Set up alerts** for high traffic
5. **Scale up** Railway plan as needed

## 📚 Resources

- **Full Documentation**: `README.md`
- **Deployment Guide**: `DEPLOYMENT_GUIDE.md`
- **Webflow Integration**: `embed/webflow-embed-instructions.html`
- **Admin Panel**: `https://your-domain.railway.app/admin`

---

**🚀 Ready to go pro?** Contact the Hooma team for advanced customization and enterprise features!
