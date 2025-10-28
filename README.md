# WOO Hackathon - Text Transformation Demo

A full-stack application built with FastAPI backend and React/Expo frontend for the WOO (Wet Open Overheid) hackathon.

## Features

- **Backend**: FastAPI server that transforms text by randomly replacing words
- **Frontend**: React application with React Native compatibility (mobile & desktop ready)
- **Styling**: Tailwind CSS with Nativewind for cross-platform consistency
- **API**: RESTful endpoints for text transformation

## Project Structure

```
WOO/
├── backend/
│   ├── server/
│   │   ├── __init__.py
│   │   ├── __main__.py        (Module entry point)
│   │   ├── app.py             (FastAPI application)
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── text_processor.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── _layout.tsx        (Root layout)
│   │   └── index.tsx          (Landing page)
│   ├── package.json
│   ├── tailwind.config.js
│   └── global.css
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8+ (for backend)
- Node.js 18+ (for frontend)
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the backend server:
```bash
python -m server.app
```

The backend will start at `http://localhost:8000`

**Available endpoints:**
- `GET /health` - Health check
- `POST /transform` - Transform text with random word replacements

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server (web):
```bash
npm start
```

The frontend will open at `http://localhost:8081` (or another available port)

**Alternative commands:**
- `npm run web` - Start web version
- `npm run android` - Start Android development
- `npm run ios` - Start iOS development

## API Usage

### Transform Endpoint

**Request:**
```bash
curl -X POST http://localhost:8000/transform \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test message"}'
```

**Response:**
```json
{
  "original": "This is a test message",
  "transformed": "This is a wonderful message"
}
```

## Frontend Features

- Clean, modern UI with Tailwind CSS
- Real-time text transformation
- Error handling with user feedback
- Loading states
- Responsive design for web and mobile
- Cross-platform compatibility with React Native

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### Frontend
- **React**: JavaScript library
- **Expo**: React Native framework
- **Expo Router**: Navigation
- **Tailwind CSS**: Utility-first CSS framework
- **Nativewind**: Tailwind for React Native
- **Axios**: HTTP client

## Development Notes

- The backend uses CORS middleware to allow requests from the frontend
- The frontend connects to the API at `http://localhost:8000`
- Update the `API_BASE_URL` in `frontend/app/index.tsx` if the backend runs on a different port
- The text processor randomly replaces 30% of words (configurable)

## Team Collaboration

- Backend team: Work in the `backend/` directory
- Frontend team: Work in the `frontend/` directory
- Share API contract changes through GitHub issues or discussions
- Test integration regularly between frontend and backend

## Next Steps

- Add more endpoints for different text operations
- Implement user authentication
- Add database integration
- Create additional pages/screens
- Deploy to production

---

Built for WOO Hackathon 🚀
