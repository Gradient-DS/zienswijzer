# Project Index 📑

Quick reference to all files and documentation in this project.

## 📍 Start Here

1. **[README.md](README.md)** - Complete project overview and features
2. **[QUICKSTART.md](QUICKSTART.md)** - Get up and running in 5 minutes
3. **[SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)** - Before the hackathon checklist

## 📚 Documentation

### For Everyone
- **[README.md](README.md)** - Overview, features, tech stack
- **[QUICKSTART.md](QUICKSTART.md)** - Fast setup instructions
- **[SETUP_CHECKLIST.md](SETUP_CHECKLIST.md)** - Verification checklist
- **[Makefile](Makefile)** - Convenient make commands
- **[PROJECT_SUMMARY.txt](PROJECT_SUMMARY.txt)** - Quick reference

### For Developers
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Detailed dev guide
  - Project architecture
  - API contract
  - How to add features
  - Debugging tips
  - Git workflow

## 🏗️ Backend Files

```
backend/
├── server/
│   ├── __init__.py         Package initialization
│   ├── __main__.py         Entry point (python -m server.app)
│   ├── app.py              FastAPI app with endpoints
│   └── utils/
│       ├── __init__.py
│       └── text_processor.py   Text transformation logic
├── requirements.txt         Python dependencies
└── .gitignore               Git ignore rules
```

**Key Files:**
- `backend/server/app.py` - Add new endpoints here
- `backend/server/utils/text_processor.py` - Modify text transformation logic
- `backend/requirements.txt` - Update when adding Python packages

## 🎨 Frontend Files

```
frontend/
├── app/
│   ├── _layout.tsx         Root layout with routing
│   └── index.tsx           Landing page
├── app.json                Expo configuration
├── package.json            Node dependencies
├── tailwind.config.js      Tailwind configuration
├── nativewind.config.js    React Native styling config
├── global.css              Global styles
├── index.js                Entry point
├── metro.config.js         Bundler config
└── .gitignore              Git ignore rules
```

**Key Files:**
- `frontend/app/index.tsx` - Modify landing page UI
- `frontend/app/_layout.tsx` - Add new routes here
- `frontend/tailwind.config.js` - Customize colors/themes

## ⚙️ Configuration Files

- `.env.example` - Environment variables template
- `.gitignore` - Git ignore rules
- `Makefile` - Development commands

## 🚀 Quick Commands

```bash
# Setup
make install-backend
make install-frontend

# Run
make run-backend         # Terminal 1
make run-frontend        # Terminal 2

# Cleanup
make clean

# Help
make help
```

## 📱 API Endpoints

### Current Endpoints

- `GET /health` - Health check
- `POST /transform` - Transform text with random words

See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for adding new endpoints.

## 🎯 File Purposes

| File | Purpose |
|------|---------|
| README.md | Project overview |
| QUICKSTART.md | Setup instructions |
| SETUP_CHECKLIST.md | Pre-hackathon checklist |
| DEVELOPER_GUIDE.md | Detailed development guide |
| Makefile | Convenient commands |
| .gitignore | Git ignore rules |
| backend/server/app.py | Backend API endpoints |
| backend/server/utils/ | Backend utilities |
| frontend/app/ | Frontend pages/routes |

## 🔍 Finding Things

### I want to...

**Add a new API endpoint**
→ Edit `backend/server/app.py`
→ See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#adding-new-endpoints-backend)

**Add a new page/screen**
→ Create file in `frontend/app/`
→ See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#adding-new-pages-frontend)

**Change styling**
→ Edit `frontend/tailwind.config.js` or component classes
→ See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#styling-with-tailwind)

**Add Python package**
→ `pip install package` then `pip freeze > requirements.txt`
→ See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#adding-a-python-dependency)

**Add Node.js package**
→ `npm install package`
→ See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#adding-a-nodejs-dependency)

**Debug backend**
→ See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#debugging) Backend section

**Debug frontend**
→ See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#debugging) Frontend section

## 📊 Project Stats

- **Backend Files**: 5 Python files
- **Frontend Files**: 10 TypeScript/JavaScript files
- **Configuration Files**: 8 config files
- **Documentation**: 5 markdown files
- **Total Files**: 24 files

## 🆘 Troubleshooting

See [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md#troubleshooting) for common issues.

## 📞 Quick Reference

- Backend runs at: `http://localhost:8000`
- Frontend runs at: `http://localhost:8081`
- FastAPI docs at: `http://localhost:8000/docs`
- Health check: `curl http://localhost:8000/health`

---

**Last Updated**: October 28, 2025
**Team**: WOO Hackathon 2025 🚀
