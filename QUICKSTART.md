# Quick Start Guide

## Running Locally (Development)

### Terminal 1 - Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m server.app
```

✅ Backend runs at `http://localhost:8000`

### Terminal 2 - Frontend

```bash
cd frontend
npm install
npm start
```

✅ Frontend opens at `http://localhost:8081`

## Testing the Application

1. Type text in the frontend input field
2. Click "Transform"
3. See the original and transformed text

## Troubleshooting

**Frontend can't reach backend?**
- Ensure backend is running on port 8000
- Check `API_BASE_URL` in `frontend/app/index.tsx`

**Port already in use?**
- Backend: Change port in `backend/server/__main__.py`
- Frontend: Expo will prompt for alternate port

**Dependencies not installing?**
- Try clearing npm cache: `npm cache clean --force`
- Python: Ensure Python 3.8+ is installed

## Making Changes

- **Backend changes**: Restart server with Ctrl+C and rerun `python -m server.app`
- **Frontend changes**: Expo hot-reloads automatically

## Building for Production

### Backend
```bash
pip install gunicorn
gunicorn server.app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Frontend
```bash
npm run build
```

---

Happy hacking! 🚀
