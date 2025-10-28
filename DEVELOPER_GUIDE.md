# Developer Guide - WOO Hackathon

## Welcome! 👋

This guide will help you understand the project structure and how to contribute effectively.

## Initial Setup

### For Backend Developers

```bash
cd backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m server.app              # Starts at localhost:8000
```

### For Frontend Developers

```bash
cd frontend
npm install
npm start                           # Starts at localhost:8081
```

## Project Architecture

### Backend (FastAPI)

```
backend/server/
├── __init__.py          # Package initialization
├── __main__.py          # Module entry point (python -m server.app)
├── app.py              # FastAPI application & endpoints
└── utils/
    ├── __init__.py
    └── text_processor.py # Text transformation logic
```

**Key Files:**

- `app.py`: Contains FastAPI app initialization and all endpoints
- `text_processor.py`: Contains the text transformation algorithm
- `__main__.py`: Allows running backend as a Python module

**Running the Backend:**

```bash
# Development
python -m server.app

# Production (requires gunicorn)
gunicorn server.app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Frontend (React + Expo)

```
frontend/
├── app/
│   ├── _layout.tsx      # Root layout (Expo Router)
│   └── index.tsx        # Landing page
├── package.json         # Dependencies
├── app.json             # Expo configuration
├── tailwind.config.js   # Tailwind CSS config
├── nativewind.config.js # React Native styling
├── global.css           # Global styles
├── index.js             # Entry point
└── metro.config.js      # Metro bundler config
```

**Key Concepts:**

- **Expo Router**: File-based routing (similar to Next.js)
- **Nativewind**: Tailwind CSS for React Native
- **Styled Components**: Using `nativewind`'s `styled` function

## API Contract

### Endpoints

#### Health Check
```
GET /health
Response: { "status": "ok" }
```

#### Transform Text
```
POST /transform
Request: { "text": "Your text here" }
Response: {
  "original": "Your text here",
  "transformed": "Your spectacular here"
}
```

## Adding New Endpoints (Backend)

1. Open `backend/server/app.py`
2. Create a new Pydantic model for request/response (if needed)
3. Add your endpoint function with appropriate decorator:

```python
@app.post("/your-endpoint")
def your_endpoint(data: YourModel):
    """Description"""
    result = do_something(data)
    return result
```

## Adding New Pages (Frontend)

1. Create a new file in `frontend/app/` (e.g., `about.tsx`)
2. Export a default React component
3. Expo Router automatically creates the route

```typescript
// frontend/app/about.tsx
export default function AboutPage() {
  return (
    <SafeAreaView className="flex-1">
      <Text className="text-2xl font-bold">About</Text>
    </SafeAreaView>
  )
}
```

## Styling with Tailwind

Use Tailwind classes directly in React Native components:

```typescript
import { View, Text } from 'react-native'
import { styled } from 'nativewind'

const StyledView = styled(View)
const StyledText = styled(Text)

export default function Component() {
  return (
    <StyledView className="flex-1 items-center justify-center bg-blue-500">
      <StyledText className="text-white text-2xl font-bold">
        Hello World
      </StyledText>
    </StyledView>
  )
}
```

## API Communication (Frontend)

Using Axios to call backend:

```typescript
import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const response = await axios.post(`${API_BASE_URL}/transform`, {
  text: userInput
})

console.log(response.data)
```

## Building for Different Platforms

### Web
```bash
npm start              # or npm run web
```

### Android
```bash
npm run android
```

### iOS
```bash
npm run ios
```

### Desktop (Windows/Mac/Linux)
Requires Expo CLI setup for desktop builds.

## Common Tasks

### Adding a Python Dependency

```bash
cd backend
source venv/bin/activate
pip install package-name
pip freeze > requirements.txt
```

### Adding a Node.js Dependency

```bash
cd frontend
npm install package-name
```

### Resetting the Project

```bash
make clean
make install-backend
make install-frontend
```

### Running Tests

*To be implemented during development*

## Environment Variables

Backend:
- `BACKEND_HOST`: Default 0.0.0.0
- `BACKEND_PORT`: Default 8000
- `DEBUG`: Default False

Frontend:
- `REACT_APP_API_URL`: API endpoint (default localhost:8000)

See `.env.example` for template.

## Debugging

### Backend
- Check console output for errors
- Use Python debugger: `import pdb; pdb.set_trace()`
- Check FastAPI docs at `http://localhost:8000/docs`

### Frontend
- Check browser console (F12)
- Use React DevTools browser extension
- Expo provides helpful error overlays

## Git Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes
3. Commit: `git commit -m "Add feature description"`
4. Push: `git push origin feature/your-feature`
5. Create Pull Request

**Commit Message Format:**
```
[backend/frontend] Brief description

Longer description if needed.

Fixes #123
```

## Performance Tips

### Backend
- Use async/await for I/O operations
- Cache frequently accessed data
- Monitor API response times

### Frontend
- Use React.memo for expensive components
- Implement lazy loading for lists
- Optimize images
- Profile with React DevTools

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Expo Documentation](https://docs.expo.dev/)
- [React Native Docs](https://reactnative.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Nativewind](https://www.nativewind.dev/)

## Questions?

- Check README.md for overview
- Check QUICKSTART.md for setup
- Ask team members on Slack/Discord
- Check error messages carefully

---

Good luck! Happy coding! 🚀
