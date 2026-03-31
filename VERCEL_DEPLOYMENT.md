# Vercel Deployment Guide

## Overview

This guide covers deploying the Fake News Detection System to Vercel (frontend) and a Python hosting service (backend).

## Important Note

**Vercel is optimized for frontend applications.** For this full-stack application:
- **Frontend**: Deploy to Vercel
- **Backend**: Deploy to Railway, Render, or Heroku (Python-compatible platforms)

## Frontend Deployment to Vercel

### Prerequisites
- GitHub account
- Vercel account (free tier available)
- Code pushed to GitHub repository

### Step 1: Prepare Frontend for Vercel

The frontend is already configured for Vercel deployment with:
- `frontend/package.json` - Dependencies
- `frontend/index.html` - Entry point
- `frontend/src/` - React components

### Step 2: Update API URL for Production

Before deploying, update the API URL in `frontend/src/App.jsx`:

```javascript
// Replace this line:
const API_BASE_URL = 'http://localhost:8000';

// With your production backend URL:
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-backend-url.com';
```

### Step 3: Deploy to Vercel

**Option A: Via Vercel Dashboard**

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Other
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (if you have a build script)
   - **Output Directory**: `.` (current directory)
5. Add Environment Variable:
   - Key: `REACT_APP_API_URL`
   - Value: Your backend URL (e.g., `https://your-backend.railway.app`)
6. Click "Deploy"

**Option B: Via Vercel CLI**

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy from project root
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? fake-news-detection
# - Directory? ./frontend
```

### Step 4: Configure Custom Domain (Optional)

1. Go to your project settings in Vercel
2. Navigate to "Domains"
3. Add your custom domain
4. Update DNS records as instructed

## Backend Deployment Options

Since Vercel doesn't support Python backends well, deploy the backend to:

### Option 1: Railway (Recommended)

**Why Railway?**
- Free tier available
- Supports Python/FastAPI
- Easy deployment
- Automatic HTTPS

**Steps:**

1. Create account at [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Python
5. Add environment variables if needed
6. Deploy!

**Railway Configuration:**

Create `railway.json` in project root:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Option 2: Render

1. Go to [render.com](https://render.com)
2. Create "New Web Service"
3. Connect GitHub repository
4. Configure:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Deploy

### Option 3: Heroku

```bash
# Install Heroku CLI
# Create Procfile in project root
echo "web: uvicorn app.main:app --host 0.0.0.0 --port $PORT" > Procfile

# Create runtime.txt
echo "python-3.10.0" > runtime.txt

# Deploy
heroku login
heroku create your-app-name
git push heroku main
```

## Environment Variables

### Frontend (Vercel)
```
REACT_APP_API_URL=https://your-backend-url.com
```

### Backend (Railway/Render/Heroku)
```
DATA_DIR=data/
MODEL_DIR=models/
LOG_DIR=logs/
DB_PATH=fake_news.db
API_HOST=0.0.0.0
API_PORT=$PORT
```

## CORS Configuration

Update `app/main.py` to allow your Vercel domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",
        "https://your-custom-domain.com",
        "http://localhost:3000"  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Deployment Checklist

- [ ] Push code to GitHub
- [ ] Update API URL in frontend
- [ ] Deploy backend to Railway/Render/Heroku
- [ ] Get backend URL
- [ ] Add backend URL as environment variable in Vercel
- [ ] Deploy frontend to Vercel
- [ ] Update CORS settings in backend
- [ ] Test the deployed application
- [ ] Configure custom domain (optional)

## Testing Deployment

1. **Test Backend**:
   ```bash
   curl https://your-backend-url.com/health
   ```

2. **Test Frontend**:
   - Open `https://your-vercel-app.vercel.app`
   - Submit a test article
   - Verify prediction works

## Troubleshooting

### Frontend can't connect to backend
- Check CORS settings in backend
- Verify API_URL environment variable
- Check browser console for errors

### Backend deployment fails
- Verify `requirements.txt` is complete
- Check Python version compatibility
- Review deployment logs

### Models not loading
- Ensure model files are included in deployment
- Check file paths are correct
- Verify sufficient memory allocation

## Cost Considerations

**Free Tier Limits:**
- **Vercel**: 100GB bandwidth/month, unlimited projects
- **Railway**: $5 free credit/month, ~500 hours
- **Render**: 750 hours/month free tier

**Recommendations:**
- Start with free tiers
- Monitor usage
- Upgrade if needed for production

## Alternative: Full Docker Deployment

For a simpler deployment, consider:
- **DigitalOcean App Platform**: Supports Docker
- **AWS ECS/Fargate**: Enterprise-grade
- **Google Cloud Run**: Serverless containers

These platforms can deploy your entire `docker-compose.yml` setup.

## Support

For deployment issues:
1. Check platform documentation
2. Review deployment logs
3. Test locally with Docker first
4. Verify all environment variables

---

**Note**: This is a machine learning application with large model files. Ensure your hosting platform supports:
- Python 3.8+
- Sufficient memory (2GB+ recommended)
- Model file storage
- Long-running processes
