# Setup Checklist ✅

Before the hackathon starts, make sure everyone completes these steps:

## Prerequisites (Everyone)

- [ ] Download and install Node.js 18+ from [nodejs.org](https://nodejs.org)
- [ ] Download and install Python 3.8+ from [python.org](https://www.python.org)
- [ ] Clone/fork the repository to your computer
- [ ] Open a terminal in the WOO directory

## Backend Team Checklist

### One-Time Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

- [ ] Virtual environment created successfully
- [ ] All dependencies installed (pip install completed)
- [ ] FastAPI and Uvicorn installed

### Verify Backend Works
```bash
python -m server.app
```

- [ ] Server starts at `http://localhost:8000`
- [ ] Can access `/health` endpoint
- [ ] No errors in terminal

### Test API (in another terminal)
```bash
curl -X POST http://localhost:8000/transform \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world this is a test"}'
```

- [ ] API returns transformed text
- [ ] No CORS errors
- [ ] Response format is correct

## Frontend Team Checklist

### One-Time Setup
```bash
cd frontend
npm install
```

- [ ] npm install completed successfully
- [ ] node_modules folder created
- [ ] No major vulnerabilities in dependencies

### Verify Frontend Works
```bash
npm start
```

- [ ] Development server starts
- [ ] Web browser opens automatically
- [ ] Landing page displays with proper styling
- [ ] No console errors

### Test Frontend UI
- [ ] Text input field is visible
- [ ] "Transform" button is clickable
- [ ] "Clear" button is clickable
- [ ] Styling looks clean and professional
- [ ] Colors match design (blue/green theme)

### Test Frontend-Backend Integration
1. Keep backend running in Terminal 1
2. Keep frontend running in Terminal 2
3. Type text in the frontend
4. Click "Transform"

- [ ] Transformed text appears
- [ ] Original and transformed text both display
- [ ] No error messages appear
- [ ] Loading indicator shows during request

## Full Team Checklist

### Environment Setup
- [ ] Everyone can run: `make help` (shows available commands)
- [ ] Everyone cloned the same repository
- [ ] Git is configured with proper credentials

### Documentation
- [ ] Everyone read README.md
- [ ] Everyone read QUICKSTART.md
- [ ] Backend team read DEVELOPER_GUIDE.md sections on backend
- [ ] Frontend team read DEVELOPER_GUIDE.md sections on frontend

### Team Communication
- [ ] Team communication channel established (Slack/Discord)
- [ ] API contract documented and shared
- [ ] Task assignments distributed
- [ ] Deployment plan discussed

### First Integration Test
- [ ] Both backend and frontend running
- [ ] User can input text and get transformed result
- [ ] No console errors or warnings
- [ ] UI is responsive

## Troubleshooting

### Backend won't start?
```bash
# Check Python version
python --version  # Should be 3.8+

# Try different port
# Edit: backend/server/__main__.py
# Change: uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port
```

### Frontend won't start?
```bash
# Clear npm cache
npm cache clean --force

# Try again
npm install
npm start
```

### Port already in use?
```bash
# Backend: Change port in backend/server/__main__.py
# Frontend: Expo will ask if you want to use a different port
```

### API connection failed?
```bash
# 1. Ensure backend is running
# 2. Check URL in frontend/app/index.tsx
# 3. Check CORS settings in backend/server/app.py
# 4. Try health check: curl http://localhost:8000/health
```

## Next Steps After Setup

1. ✅ Both teams can start independently
2. ✅ Integrate features as they're built
3. ✅ Test regularly to catch integration issues
4. ✅ Commit changes to git frequently
5. ✅ Ask questions early - don't get stuck!

---

**Ready to go?** Let's hack! 🚀

Questions? Check the documentation files or ask your team lead!
