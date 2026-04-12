# Church Live Streaming System

A WebRTC-based live streaming system for church services with broadcaster and viewer interfaces.

## 🚀 Quick Start

### For Local Development Only
1. Install dependencies: `pip install -r requirements.txt`
2. Run server: `python app.py`
3. Open:
   - **Broadcaster**: `http://127.0.0.1:5000/media-panel/go-live`
   - **Viewer**: `http://127.0.0.1:5000/live`

### For Production (GitHub Pages + Backend)
1. **Deploy Backend**: Choose one of the options below
2. **Update URLs**: Replace `https://your-church-backend.herokuapp.com` in HTML files with your deployed backend URL
3. **Deploy Frontend**: Push HTML files to GitHub Pages

## 🔧 Backend Deployment Options

### Heroku (Recommended)
```bash
heroku create your-church-live-stream
git init && git add . && git commit -m "Deploy"
git push heroku main
# Note the URL: https://your-church-live-stream.herokuapp.com
```

### Railway
1. Connect GitHub repo to Railway
2. Auto-deploys on push

### DigitalOcean App Platform
1. Connect GitHub repo
2. Deploy automatically

## ⚙️ Configuration

### Update Backend URLs
After deploying your backend, update these files:

**In `live.html` and `media-panel/go-live.html`:**
```javascript
// Change this line:
'https://your-church-backend.herokuapp.com'
// To your actual backend URL:
'https://your-deployed-backend-url.com'
```

### Environment Detection
The app automatically detects:
- **GitHub Pages**: Uses deployed backend URL
- **Localhost**: Uses `http://127.0.0.1:5000`

## 📋 Features

- **WebRTC Streaming**: Real-time video between broadcaster and viewers
- **Live Chat**: Interactive messaging system
- **Status Monitoring**: Viewer count and stream duration
- **Mobile Responsive**: Works on all devices
- **CORS Ready**: Handles different deployment environments

## 🔒 Security Notes

- Camera/microphone permissions required for broadcasting
- HTTPS recommended for production
- Consider authentication for broadcaster access

## 🐛 Troubleshooting

### CORS Errors
- **Local**: Use `http://127.0.0.1:5000` URLs
- **GitHub Pages**: Deploy backend first, then update URLs

### Connection Issues
- Ensure Flask server is running
- Check backend URL configuration
- Verify network/firewall settings