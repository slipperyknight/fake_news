# Production Deployment Guide

## Frontend Deployment

### Build for Production

```bash
cd frontend
npm install
npm run build  # If available
```

### Static File Serving

The frontend can be served as static files:

```bash
# Using any static server
npx serve -s build -p 3000

# Using nginx/Apache
# Copy build/ directory to web server root
```

### Environment Configuration

For production, update the API URL in `src/App.jsx`:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-api-domain.com';
```

## Backend Deployment

### Docker Deployment

```dockerfile
# Backend Dockerfile example
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8001:8000"
    environment:
      - PYTHONPATH=/app
  
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

## Environment Variables

```bash
# Backend
export API_HOST=0.0.0.0
export API_PORT=8000

# Frontend
export REACT_APP_API_URL=http://your-production-api.com
```

## SSL/HTTPS Setup

### Backend SSL

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

### Frontend HTTPS

Update API URL to use HTTPS in production.

## Monitoring

### Health Checks

- **Backend**: `GET /health`
- **Frontend**: Serve static files with proper headers

### Logging

- **Application Logs**: Use proper logging levels
- **Access Logs**: Monitor API calls and responses
- **Error Tracking**: Implement error reporting

## Security

### CORS Configuration

Update CORS settings for production domains:

```python
# In app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Production domain
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### Rate Limiting

Consider implementing rate limiting for the prediction endpoint.

### Input Validation

- **Backend**: Already implemented with Pydantic models
- **Frontend**: Client-side validation for better UX

## Performance Optimization

### Backend

- **Model Loading**: Global instance (already implemented)
- **Database Connection**: Connection pooling
- **Response Caching**: Consider Redis for frequent requests

### Frontend

- **Bundle Size**: Minimize JavaScript bundle
- **Image Optimization**: Compress and serve next-gen formats
- **CDN**: Consider CDN for static assets

## Scaling

### Horizontal Scaling

- **Load Balancer**: Distribute traffic across multiple instances
- **Database**: Consider read replicas for scaling
- **Caching Layer**: Redis or Memcached for common responses

### Monitoring Tools

- **APM**: New Relic, DataDog, or similar
- **Error Tracking**: Sentry for error monitoring
- **Performance**: Web Vitals for frontend monitoring

## Backup Strategy

- **Database**: Regular backups of SQLite database
- **Model Artifacts**: Version control for trained models
- **Configuration**: Backup environment configurations

## Rollback Plan

- **Database**: Point-in-time recovery
- **Models**: Keep previous model versions
- **Frontend**: Blue-green deployment strategy
