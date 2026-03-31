# Fake News Detection Frontend

A modern, production-ready React frontend for the fake news detection system.

## 🎨 Design System

### **Theme: Minimal & Professional**
- **Primary**: Pure black (#000000) background
- **Text**: White (#ffffff) primary text
- **Secondary**: Gray (#aaaaaa) secondary text
- **Accent**: Subtle gray borders (#333333, #444444)
- **No AI-generated appearance**: Clean, intentional design

### **Typography**
- **Font**: System font stack (-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto)
- **Sizes**: 32px (title), 20px (headings), 16px (body), 14px (small)

### **Layout**
- **Container**: Centered, max-width 600px
- **Spacing**: Generous padding and margins
- **Responsive**: Mobile-optimized breakpoints

## 🧩 Components

### **1. App.jsx** - Main Application
- State management (loading, result, error, text, url)
- API integration with localhost:8001
- Error handling and user feedback
- Form validation and submission

### **2. PredictionForm.jsx** - Input Component
- Textarea for news content (required)
- Input field for URL (optional)
- Submit button with loading state
- Real-time validation

### **3. ResultCard.jsx** - Results Display
- Prediction result (Fake/Real) with color coding
- Confidence percentage display
- Modal contributions visualization
- Concept drift signal indicator
- Clear result functionality

### **4. ContributionBar.jsx** - Visual Components
- Horizontal bar charts for modality contributions
- Animated fill transitions
- Percentage labels
- Responsive sizing

## 🎯 Features

### **Core Functionality**
- ✅ **Text Analysis**: Large textarea with validation
- ✅ **URL Input**: Optional source URL field
- ✅ **API Integration**: POST to /predict endpoint
- ✅ **Loading States**: Spinner during processing
- ✅ **Error Handling**: Graceful error display
- ✅ **Results Display**: Comprehensive prediction output

### **Advanced Features**
- ✅ **Modal Contributions**: Text/Metadata/Image visualization
- ✅ **Drift Detection**: Real-time drift signal display
- ✅ **Confidence Scores**: Percentage-based display
- ✅ **Responsive Design**: Mobile-friendly interface
- ✅ **Smooth Animations**: Fade-in and hover effects

## 🌐 API Integration

### **Request Format**
```javascript
POST http://localhost:8001/predict/
Content-Type: application/json

{
  "text": "News article text...",
  "url": "https://example.com/article",
  "image": null
}
```

### **Response Handling**
```javascript
{
  "label": 0|1,
  "confidence": 0.0-1.0,
  "modal_contributions": {
    "text": 0.0-1.0,
    "metadata": 0.0-1.0,
    "image": 0.0-1.0
  },
  "drift_signal": 0.0-1.0
}
```

## 📱 Responsive Design

### **Breakpoints**
- **Desktop**: > 640px (full layout)
- **Mobile**: ≤ 640px (stacked layout, adjusted spacing)

### **Mobile Optimizations**
- Reduced padding on small screens
- Stacked prediction display
- Full-width input fields
- Touch-friendly button sizes

## 🎭 User Experience

### **Interaction Design**
- **Loading States**: Clear visual feedback during API calls
- **Error Messages**: User-friendly error display with recovery options
- **Success States**: Animated result presentation
- **Micro-interactions**: Hover effects, smooth transitions

### **Accessibility**
- **Semantic HTML**: Proper heading hierarchy
- **Keyboard Navigation**: Tab-friendly form elements
- **Screen Readers**: ARIA labels and descriptions
- **Color Contrast**: WCAG compliant contrast ratios

## 🚀 Production Features

### **Performance**
- **Optimized Rendering**: Efficient React patterns
- **Minimal Dependencies**: Only React and CSS
- **Fast Loading**: Lightweight bundle size
- **Smooth Animations**: CSS-based transitions

### **Development**
- **Hot Reload**: Development server with live updates
- **Error Handling**: Comprehensive error boundaries
- **Console Logging**: Development-friendly debugging
- **Production Build**: Optimized for deployment

## 📁 File Structure

```
frontend/
├── index.html          # Main HTML entry point
├── package.json         # Dependencies and scripts
├── src/
│   ├── App.jsx         # Main React component
│   └── App.css         # Global styles
└── README.md           # This documentation
```

## 🛠 Development Setup

```bash
cd frontend
npm install
npm start
```

### **Development Server**
- **URL**: http://localhost:3000
- **Proxy**: API calls to localhost:8001
- **Hot Reload**: Live updates during development

## 🎨 Design Decisions

### **Why This Design Works**

1. **Minimal Aesthetic**: Black theme looks professional and modern
2. **Clear Hierarchy**: Users immediately understand what to do
3. **Subtle Feedback**: Loading states and transitions don't distract
4. **Data-Driven**: UI responds to actual API responses
5. **Accessible**: Semantic HTML and keyboard navigation
6. **Performance-First**: No heavy libraries or animations

### **Avoided Anti-Patterns**
- ❌ No bright colors or gradients
- ❌ No AI-generated appearance
- ❌ No cluttered interfaces
- ❌ No unnecessary animations
- ❌ No complex state management
- ❌ No heavy dependencies

## 🎯 Production Ready

The frontend is designed to be:
- **Production-quality**: Clean, professional appearance
- **Fully functional**: Complete API integration
- **User-friendly**: Intuitive and responsive
- **Maintainable**: Clean, documented code
- **Performant**: Optimized for speed and efficiency

**A premium, minimal, and highly functional frontend for fake news detection.** 🎉
