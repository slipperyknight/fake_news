# 🚀 Docker Deployment Guide

Complete guide for deploying the Fake News Detection System using Docker.

---

## 📋 Prerequisites

### Required Software:
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher

### Installation:

**Windows:**
- Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- Docker Compose is included with Docker Desktop

**Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**macOS:**
- Download and install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

### Verify Installation:
```bash
docker --version
docker-compose --version
```

---

## 🏗️ Project Structure

```
fake_news/
├── Dockerfile                  # Backend Docker configuration
├── docker-compose.yml          # Multi-container orchestration
├── .dockerignore              # Files to exclude from Docker build
├── app/                       # Backend application
├── models/                    # Trained models (required)
├── data/                      # Dataset (required)
├── frontend/
│   ├── Dockerfile            # Frontend Docker configuration
│   ├── .dockerignore         # Frontend exclusions
│   └── ...
└── DEPLOYMENT.md             # This file
```

---

## 🚀 Quick Start (One Command)

### 1. Build and Start All Services:

```bash
docker-compose up --build
```

This single command will:
- ✅ Build the backend Docker image
- ✅ Build the frontend Docker image
- ✅ Start both services
- ✅ Set up networking between containers
- ✅ Mount necessary volumes
- ✅ Run health checks

### 2. Access the Application:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 3. Stop All Services:

```bash
docker-compose down
```

---

## 📦 Detailed Deployment Steps

### Step 1: Prepare the Environment

Ensure you have the required model files:
```bash
# Check if models exist
ls models/text_model/
ls models/image_model/
ls models/meta_model/

# If missing, train models first:
python scripts/train_pipeline.py
```

### Step 2: Build Docker Images

**Build backend only:**
```bash
docker build -t fake-news-backend .
```

**Build frontend only:**
```bash
docker build -t fake-news-frontend ./frontend
```

**Build both with docker-compose:**
```bash
docker-compose build
```

### Step 3: Start Services

**Start in foreground (see logs):**
```bash
docker-compose up
```

**Start in background (detached mode):**
```bash
docker-compose up -d
```

**Start with rebuild:**
```bash
docker-compose up --build
```

### Step 4: Verify Deployment

**Check running containers:**
```bash
docker-compose ps
```

Expected output:
```
NAME                    STATUS              PORTS
fake-news-backend       Up (healthy)        0.0.0.0:8000->8000/tcp
fake-news-frontend      Up (healthy)        0.0.0.0:3000->3000/tcp
```

**Check logs:**
```bash
# All services
docker-compose logs

# Backend only
docker-compose logs backend

# Frontend only
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

**Test backend health:**
```bash
curl http://localhost:8000/health
```

**Test frontend:**
```bash
curl http://localhost:3000
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Backend Configuration
PYTHONUNBUFFERED=1
DATA_DIR=/app/data/
MODEL_DIR=/app/models/
LOG_DIR=/app/logs/
DB_PATH=/app/fake_news.db

# Frontend Configuration
NODE_ENV=production
REACT_APP_API_URL=http://localhost:8000
```

Update `docker-compose.yml` to use the `.env` file:
```yaml
services:
  backend:
    env_file:
      - .env
```

### Port Configuration

To change ports, edit `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Change 8080 to your desired port
  
  frontend:
    ports:
      - "3001:3000"  # Change 3001 to your desired port
```

---

## 🐳 Docker Commands Reference

### Container Management

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Stop specific service
docker-compose stop backend

# Start specific service
docker-compose start backend
```

### Image Management

```bash
# List images
docker images

# Remove image
docker rmi fake-news-backend

# Remove all unused images
docker image prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Volume Management

```bash
# List volumes
docker volume ls

# Remove all volumes
docker-compose down -v

# Inspect volume
docker volume inspect fake_news_models
```

### Logs and Debugging

```bash
# View logs
docker-compose logs

# Follow logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100

# Execute command in running container
docker-compose exec backend bash
docker-compose exec frontend sh

# View container details
docker inspect fake-news-backend
```

---

## 🔍 Health Checks

### Backend Health Check

The backend includes automatic health checks:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Manual health check:**
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "api_version": "1.0.0",
  "models_loaded": true
}
```

### Frontend Health Check

```yaml
healthcheck:
  test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

**Manual health check:**
```bash
curl http://localhost:3000
```

---

## 🧪 Testing the Deployment

### 1. Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Test prediction endpoint
curl -X POST http://localhost:8000/predict/ \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Sample news article text for testing",
    "url": "https://example.com/article"
  }'

# Test with image upload
curl -X POST http://localhost:8000/predict/multimodal \
  -F "text=Sample news text" \
  -F "url=https://example.com" \
  -F "image=@data/images/test-image.jpg"
```

### 2. Test Frontend

1. Open browser: http://localhost:3000
2. Enter sample text
3. Add URL (optional)
4. Upload image (optional)
5. Click "Analyze"
6. Verify result displays correctly

### 3. Test Integration

Verify frontend can communicate with backend:
1. Open browser console (F12)
2. Submit a prediction
3. Check Network tab for API calls
4. Verify no CORS errors
5. Confirm result displays

---

## 🔒 Production Considerations

### Security

1. **Use environment variables for secrets:**
   ```yaml
   environment:
     - API_KEY=${API_KEY}
     - DB_PASSWORD=${DB_PASSWORD}
   ```

2. **Don't expose unnecessary ports:**
   ```yaml
   # Only expose what's needed
   ports:
     - "8000:8000"  # Backend API
   ```

3. **Use read-only volumes where possible:**
   ```yaml
   volumes:
     - ./models:/app/models:ro  # Read-only
   ```

4. **Enable HTTPS with reverse proxy:**
   - Use Nginx or Traefik
   - Add SSL certificates
   - Redirect HTTP to HTTPS

### Performance

1. **Resource limits:**
   ```yaml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 4G
           reservations:
             cpus: '1'
             memory: 2G
   ```

2. **Optimize image size:**
   - Use multi-stage builds
   - Remove unnecessary files
   - Use slim base images

3. **Enable caching:**
   - Cache model loading
   - Use Redis for predictions
   - Enable HTTP caching

### Monitoring

1. **Add logging:**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

2. **Health monitoring:**
   - Set up monitoring tools (Prometheus, Grafana)
   - Configure alerts
   - Track metrics

3. **Backup strategy:**
   - Regular database backups
   - Model versioning
   - Configuration backups

---

## 🌐 Cloud Deployment

### AWS Deployment

1. **Using ECS (Elastic Container Service):**
   ```bash
   # Push images to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   docker tag fake-news-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/fake-news-backend:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/fake-news-backend:latest
   ```

2. **Using EC2:**
   - Launch EC2 instance
   - Install Docker and Docker Compose
   - Clone repository
   - Run `docker-compose up -d`

### Google Cloud Platform

1. **Using Cloud Run:**
   ```bash
   # Build and push to GCR
   gcloud builds submit --tag gcr.io/PROJECT_ID/fake-news-backend
   
   # Deploy to Cloud Run
   gcloud run deploy fake-news-backend \
     --image gcr.io/PROJECT_ID/fake-news-backend \
     --platform managed \
     --region us-central1
   ```

### Azure

1. **Using Azure Container Instances:**
   ```bash
   # Create resource group
   az group create --name fake-news-rg --location eastus
   
   # Deploy container
   az container create \
     --resource-group fake-news-rg \
     --name fake-news-backend \
     --image fake-news-backend:latest \
     --ports 8000
   ```

---

## 🐛 Troubleshooting

### Common Issues

**1. Port already in use:**
```bash
# Find process using port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Or change port in docker-compose.yml
```

**2. Models not loading:**
```bash
# Check if models directory is mounted
docker-compose exec backend ls -la /app/models

# Verify model files exist
docker-compose exec backend ls -la /app/models/text_model/
docker-compose exec backend ls -la /app/models/image_model/
docker-compose exec backend ls -la /app/models/meta_model/
```

**3. Frontend can't reach backend:**
```bash
# Check if backend is healthy
docker-compose ps

# Check backend logs
docker-compose logs backend

# Verify network connectivity
docker-compose exec frontend ping backend
```

**4. Out of memory:**
```bash
# Increase Docker memory limit in Docker Desktop settings
# Or add resource limits in docker-compose.yml

# Check memory usage
docker stats
```

**5. Build fails:**
```bash
# Clean build cache
docker-compose build --no-cache

# Remove old images
docker image prune -a

# Check disk space
docker system df
```

### Debug Mode

Run containers in debug mode:

```bash
# Start with verbose logging
docker-compose up --verbose

# Access container shell
docker-compose exec backend bash
docker-compose exec frontend sh

# Check environment variables
docker-compose exec backend env

# Test API from inside container
docker-compose exec backend curl http://localhost:8000/health
```

---

## 📊 Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f

# Last N lines
docker-compose logs --tail=100

# Since timestamp
docker-compose logs --since 2024-01-01T00:00:00
```

### Container Stats

```bash
# Real-time stats
docker stats

# Specific container
docker stats fake-news-backend
```

### Disk Usage

```bash
# Check Docker disk usage
docker system df

# Detailed view
docker system df -v
```

---

## 🧹 Cleanup

### Remove Everything

```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove images
docker rmi fake-news-backend fake-news-frontend

# Clean up system
docker system prune -a --volumes
```

### Selective Cleanup

```bash
# Stop containers
docker-compose stop

# Remove containers
docker-compose rm

# Remove volumes
docker volume rm fake_news_models fake_news_data

# Remove networks
docker network rm fake_news_fake-news-network
```

---

## 📝 Best Practices

1. **Always use docker-compose for multi-container apps**
2. **Use .dockerignore to reduce image size**
3. **Implement health checks for all services**
4. **Use volumes for persistent data**
5. **Set resource limits in production**
6. **Enable logging with rotation**
7. **Use environment variables for configuration**
8. **Implement proper error handling**
9. **Regular security updates**
10. **Monitor resource usage**

---

## 🎯 Summary

### One-Command Deployment:
```bash
docker-compose up --build
```

### Access Points:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Stop Everything:
```bash
docker-compose down
```

---

**Your fake news detection system is now production-ready! 🚀**
