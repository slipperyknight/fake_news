const { useState, useEffect } = React;

// API configuration - Docker deployment uses port 8000
const API_BASE_URL = 'http://localhost:8000';

// Main App component
function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [text, setText] = useState('');
  const [url, setUrl] = useState('');
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [showResult, setShowResult] = useState(false);

  // Handle image selection
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    } else {
      setImage(null);
      setImagePreview(null);
    }
  };

  // Handle prediction request
  const handlePredict = async (e) => {
    e.preventDefault();
    
    if (!text.trim()) {
      setError('Please enter news text to analyze');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setShowResult(false);

    try {
      // Create FormData for multipart upload
      const formData = new FormData();
      formData.append('text', text.trim());
      if (url.trim()) formData.append('url', url.trim());
      if (image) formData.append('image', image);

      const response = await fetch(`${API_BASE_URL}/predict/multimodal`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
      setTimeout(() => setShowResult(true), 100);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Clear result
  const handleClear = () => {
    setShowResult(false);
    setTimeout(() => {
      setResult(null);
      setError(null);
      setText('');
      setUrl('');
      setImage(null);
      setImagePreview(null);
    }, 300);
  };

  return (
    <div className="app">
      {/* Background glow */}
      <div className="bg-glow"></div>
      
      <div className="container">
        {/* Hero Section */}
        <header className="hero">
          <h1 className="hero-title">
            Multimodal Fake News Detection
          </h1>
          <p className="hero-subtitle">
            Real-time analysis using text, metadata, and adaptive learning
          </p>
        </header>

        {/* Input Card */}
        <div className="input-card">
          <form onSubmit={handlePredict} className="form">
            <div className="form-group">
              <label htmlFor="text" className="label">
                News Content
              </label>
              <textarea
                id="text"
                className="textarea"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste the news article text you want to analyze..."
                required
                disabled={loading}
                rows="6"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="url" className="label">
                  Source URL (Optional)
                </label>
                <input
                  id="url"
                  type="url"
                  className="input"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com/article"
                  disabled={loading}
                />
              </div>

              <div className="form-group">
                <label htmlFor="image" className="label">
                  Image (Optional)
                </label>
                <input
                  id="image"
                  type="file"
                  className="input-file"
                  accept="image/*"
                  onChange={handleImageChange}
                  disabled={loading}
                />
              </div>
            </div>

            {imagePreview && (
              <div className="image-preview">
                <img src={imagePreview} alt="Preview" />
              </div>
            )}

            <button
              type="submit"
              className={`submit-btn ${loading ? 'loading' : ''}`}
              disabled={loading || !text.trim()}
            >
              {loading ? 'Analyzing...' : 'Analyze'}
            </button>
          </form>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </div>

        {/* Result Section */}
        {result && (
          <div className={`result-section ${showResult ? 'show' : ''}`}>
            <div className="result-card">
              <div className="result-header">
                <div className={`prediction-badge ${result.label === 1 ? 'real' : 'fake'}`}>
                  {result.label === 1 ? 'REAL NEWS' : 'FAKE NEWS'}
                </div>
                <div className="confidence">
                  <span className="confidence-value">
                    {(result.confidence * 100).toFixed(1)}%
                  </span>
                  <span className="confidence-label">confidence</span>
                </div>
              </div>

              {result.modal_contributions && (
                <div className="contributions">
                  <h3 className="section-title">Modal Contributions</h3>
                  <div className="contribution-list">
                    {Object.entries(result.modal_contributions).map(([modality, value]) => (
                      <div key={modality} className="contribution-item">
                        <div className="contribution-header">
                          <span className="modality-name">
                            {modality.charAt(0).toUpperCase() + modality.slice(1)}
                          </span>
                          <span className="contribution-value">
                            {(value * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="contribution-bar">
                          <div 
                            className="contribution-fill" 
                            style={{ width: `${(value * 100)}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {result.drift_signal !== undefined && (
                <div className="drift-info">
                  <span className="drift-label">Drift Signal</span>
                  <span className={`drift-value ${result.drift_signal > 0.3 ? 'high' : result.drift_signal > 0.1 ? 'medium' : 'low'}`}>
                    {(result.drift_signal * 100).toFixed(1)}%
                  </span>
                </div>
              )}

              <button onClick={handleClear} className="clear-btn">
                Clear
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Render the app
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
