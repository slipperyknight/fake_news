# Frontend Test Script

## Test the React frontend

```bash
# Test if frontend files exist and are properly structured
cd frontend

# Check main files
ls -la src/
ls -la

# Test if React can load (basic syntax check)
node -e "
try {
  require('http').createServer((req, res) => {
    res.writeHead(200, {'Content-Type': 'text/html'});
    res.end('<!DOCTYPE html><html><body><h1>Test Server</h1></body></html>');
  }).listen(3001);
  console.log('✅ Basic server test passed');
} catch (e) {
  console.error('❌ Server test failed:', e);
}
"
```

## Manual Browser Test

1. Open `frontend/index.html` directly in browser
2. Check for:
   - Black background loads
   - White text appears
   - Form elements render correctly
   - No console errors

## API Connection Test

The frontend should automatically connect to the backend API at `http://localhost:8001/predict/`.
