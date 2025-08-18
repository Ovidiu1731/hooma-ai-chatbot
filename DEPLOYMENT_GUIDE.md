# 🚀 Hooma AI Chatbot - Railway Deployment Guide

This guide will help you deploy your Hooma AI Chatbot to Railway for 24/7 operation.

## 📋 Prerequisites

- Railway account (sign up at [railway.app](https://railway.app))
- GitHub account for code repository
- OpenAI API key OR Anthropic API key
- Basic familiarity with environment variables

## 🔧 Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. **Create a new GitHub repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Hooma AI Chatbot"
   git branch -M main
   git remote add origin https://github.com/yourusername/hooma-chatbot.git
   git push -u origin main
   ```

2. **Ensure all files are included:**
   - `app.py` (main application)
   - `requirements.txt` (Python dependencies)
   - `railway.json` (Railway configuration)
   - `Procfile` (process definition)
   - `Dockerfile` (container configuration)
   - `config/` directory with system prompt and knowledge base
   - `static/` directory with widget files

### Step 2: Deploy to Railway

1. **Connect to Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Connect your GitHub account and select your repository

2. **Configure Environment Variables:**
   In your Railway project dashboard, go to Variables and add:

   ```env
   # Required: Choose your AI provider
   AI_PROVIDER=openai
   # OR
   # AI_PROVIDER=anthropic

   # Required: Add your API key (choose one)
   OPENAI_API_KEY=your_openai_api_key_here
   # OR
   ANTHROPIC_API_KEY=your_anthropic_api_key_here

   # Optional: Customize models
   OPENAI_MODEL=gpt-4-turbo-preview
   ANTHROPIC_MODEL=claude-3-sonnet-20240229

   # Security
   SECRET_KEY=your_random_secret_key_change_this

   # CORS - Add your domains
   ALLOWED_ORIGINS=https://hooma.io,https://www.hooma.io,https://hooma.webflow.io

   # Rate Limiting
   RATE_LIMIT_REQUESTS_PER_MINUTE=30
   RATE_LIMIT_REQUESTS_PER_HOUR=500

   # Business Configuration
   CONTACT_EMAIL=hello@hooma.io
   WEBSITE_URL=https://hooma.io

   # Widget Customization
   WIDGET_PRIMARY_COLOR=#2563eb
   WIDGET_POSITION=bottom-right
   ```

3. **Deploy:**
   - Railway will automatically detect the configuration and deploy
   - Monitor the build logs for any issues
   - Once deployed, you'll get a public URL (e.g., `https://your-app.railway.app`)

### Step 3: Configure Custom Domain (Optional)

1. **Add Custom Domain:**
   - In Railway dashboard, go to Settings
   - Add your custom domain (e.g., `chatbot.hooma.io`)
   - Update DNS records as instructed by Railway

2. **Update CORS Origins:**
   - Add your custom domain to `ALLOWED_ORIGINS` environment variable
   - Redeploy if necessary

### Step 4: Test Your Deployment

1. **Health Check:**
   ```bash
   curl https://your-app.railway.app/api/health
   ```

2. **Test Chat Interface:**
   - Visit `https://your-app.railway.app` for the test interface
   - Send a test message to verify AI responses

3. **Test Widget:**
   - Visit `https://your-app.railway.app/embed/demo.html`
   - Verify the widget loads and functions correctly

## 🔒 Security Configuration

### Environment Variables Security

**Never commit sensitive data to your repository!** Always use environment variables for:
- API keys
- Secret keys  
- Database credentials
- Third-party service tokens

### CORS Configuration

Update `ALLOWED_ORIGINS` to include only your domains:
```env
ALLOWED_ORIGINS=https://hooma.io,https://www.hooma.io,https://hooma.webflow.io
```

### Rate Limiting

Adjust rate limits based on your expected traffic:
```env
RATE_LIMIT_REQUESTS_PER_MINUTE=30  # Per IP address
RATE_LIMIT_REQUESTS_PER_HOUR=500   # Per IP address
```

## 📊 Monitoring and Maintenance

### Health Monitoring

Railway provides built-in monitoring, but you can also set up external monitoring:
- **Endpoint:** `https://your-app.railway.app/api/health`
- **Expected Response:** `{"status": "healthy", ...}`

### Log Monitoring

Access logs in Railway dashboard:
- Deploy logs (build process)
- Application logs (runtime)
- Error tracking

### Performance Optimization

1. **Monitor Response Times:**
   - AI API calls should be < 5 seconds
   - Widget loading should be < 1 second

2. **Resource Usage:**
   - Monitor memory usage
   - Scale up if needed (Railway Pro plan)

3. **Database Considerations:**
   - Current setup uses in-memory storage
   - For production, consider Redis for session storage

## 🔧 Troubleshooting

### Common Deployment Issues

**Build Failure:**
- Check `requirements.txt` for correct package versions
- Verify Python version in `runtime.txt`
- Review build logs for specific error messages

**Environment Variable Issues:**
- Ensure all required variables are set
- Check for typos in variable names
- Verify API keys are valid

**CORS Errors:**
- Add your domain to `ALLOWED_ORIGINS`
- Check for `https://` vs `http://` differences
- Verify domain spelling

**Widget Not Loading:**
- Check if Railway app is running
- Verify the embed code URL is correct
- Test in incognito mode to avoid cache issues

### Debug Mode

For development, set:
```env
DEBUG=true
```

This enables:
- FastAPI documentation at `/docs`
- Detailed error messages
- Auto-reload on code changes

## 📈 Scaling Considerations

### Traffic Growth

As your chatbot usage grows:

1. **Upgrade Railway Plan:**
   - Starter: 500 hours/month (limited)
   - Pro: Unlimited usage, better performance

2. **Optimize Performance:**
   - Implement Redis for session storage
   - Add response caching
   - Consider CDN for static files

3. **Monitor Costs:**
   - Track AI API usage
   - Monitor Railway compute hours
   - Set up billing alerts

### Advanced Features

Consider adding:
- **Analytics Integration:** Google Analytics, Mixpanel
- **A/B Testing:** Different welcome messages, colors
- **Lead Capture:** Form integration, CRM connections
- **Multi-language Support:** i18n for global reach

## 🆘 Support

If you encounter issues:

1. **Check Railway Logs:**
   - Build logs for deployment issues
   - Application logs for runtime errors

2. **Community Resources:**
   - Railway Discord community
   - FastAPI documentation
   - OpenAI/Anthropic API docs

3. **Professional Support:**
   - Contact Hooma team: hello@hooma.io
   - Book a technical consultation

## 🎯 Success Checklist

- [ ] Repository created and code committed
- [ ] Railway project deployed successfully
- [ ] Environment variables configured
- [ ] Health check endpoint responding
- [ ] Test chat interface working
- [ ] Widget demo functioning
- [ ] Custom domain configured (if applicable)
- [ ] CORS origins properly set
- [ ] Rate limiting configured
- [ ] Monitoring set up
- [ ] Embed code ready for Webflow

🎉 **Congratulations!** Your Hooma AI Chatbot is now live and ready to engage with your website visitors 24/7.

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [Webflow Custom Code Guide](https://university.webflow.com/lesson/custom-code-in-webflow)
