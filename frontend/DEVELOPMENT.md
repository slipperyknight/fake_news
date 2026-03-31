# Frontend Development Setup

## Quick Start

```bash
cd frontend
npm install
npm start
```

## Development Server

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **Hot Reload**: Enabled for development

## Testing

1. Start the backend API first:
```bash
cd ..
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

2. Start the frontend:
```bash
cd frontend
npm start
```

3. Open http://localhost:3000 in your browser

## Production Build

```bash
cd frontend
npm run build  # If build script is added
```

The frontend will automatically proxy API requests to the backend during development.
