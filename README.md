# Zienswijzer

A full-stack application for managing cases and documents with PDF viewing capabilities. Built with FastAPI backend and React frontend for the WOO (Wet Open Overheid) project.

## Features

- **Case Management**: Create and manage cases with multiple documents
- **PDF Viewing**: View PDF documents directly in the browser
- **Document Upload**: Drag-and-drop PDF upload functionality
- **Authentication**: User login and session management
- **Document Organization**: List and organize documents by case
- **Dummy Data**: Pre-configured sample data for demonstration

## Project Structure

```
WOO/
├── backend/
│   ├── server/
│   │   ├── __init__.py
│   │   ├── __main__.py          (Module entry point)
│   │   ├── app.py               (FastAPI application)
│   │   ├── data/                (PDF files storage)
│   │   │   ├── document.pdf
│   │   │   └── email.pdf
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── text_processor.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                 (API hooks with TanStack Query)
│   │   ├── components/
│   │   │   ├── features/        (Feature components)
│   │   │   └── ui/              (shadcn/ui components)
│   │   ├── layouts/             (Layout components)
│   │   ├── pages/               (Page components)
│   │   ├── store/               (Zustand stores)
│   │   └── types/               (TypeScript types)
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
└── README.md
```

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (for backend)
- **Node.js 18+** (for frontend)
- **npm** (comes with Node.js)

### Installing Node.js

#### macOS

**Option 1: Using Homebrew (Recommended)**
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Node.js
brew install node
```

**Option 2: Official Installer**
1. Visit [nodejs.org](https://nodejs.org/)
2. Download the macOS installer (.pkg file)
3. Run the installer and follow the instructions
4. Verify installation:
```bash
node --version
npm --version
```

#### Windows

**Option 1: Official Installer (Recommended)**
1. Visit [nodejs.org](https://nodejs.org/)
2. Download the Windows installer (.msi file)
3. Run the installer and follow the instructions
4. Verify installation:
```cmd
node --version
npm --version
```

**Option 2: Using Chocolatey**
```cmd
# Install Chocolatey if you don't have it (run as Administrator)
# Visit: https://chocolatey.org/install

# Install Node.js
choco install nodejs
```

**Option 3: Using winget**
```cmd
winget install OpenJS.NodeJS
```

### Installing Python

#### macOS

Python 3 is usually pre-installed. Check your version:
```bash
python3 --version
```

If you need to install or update Python:
```bash
# Using Homebrew
brew install python3
```

#### Windows

1. Visit [python.org](https://www.python.org/downloads/)
2. Download the Windows installer
3. Run the installer and **check "Add Python to PATH"**
4. Verify installation:
```cmd
python --version
```

## Setup Instructions

### Backend Setup

1. **Navigate to the backend directory:**

   **macOS/Linux:**
   ```bash
   cd backend
   ```

   **Windows:**
   ```cmd
   cd backend
   ```

2. **Create a virtual environment:**

   **macOS/Linux:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   **Windows:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**

   **macOS/Linux/Windows:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the backend server:**

   **macOS/Linux:**
   ```bash
   python -m server.app
   ```

   **Windows:**
   ```cmd
   python -m server.app
   ```

   Or using uvicorn directly:
   ```bash
   # macOS/Linux/Windows
   uvicorn server.app:app --reload
   ```

The backend will start at `http://localhost:8000`

**Available API endpoints:**
- `GET /health` - Health check
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user
- `GET /cases` - List all cases
- `GET /cases/{id}` - Get case details with documents
- `POST /cases` - Create a new case
- `GET /documents` - List all documents
- `GET /documents/{id}` - Get document details
- `GET /documents/{id}/pdf` - Serve PDF file
- `POST /documents/upload` - Upload a PDF document

### Frontend Setup

1. **Navigate to the frontend directory:**

   **macOS/Linux:**
   ```bash
   cd frontend
   ```

   **Windows:**
   ```cmd
   cd frontend
   ```

2. **Install dependencies:**

   **macOS/Linux/Windows:**
   ```bash
   npm install
   ```

3. **Start the development server:**

   **macOS/Linux/Windows:**
   ```bash
   npm run dev
   ```

The frontend will open at `http://localhost:3000` (or another available port)

**Available scripts:**
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run typecheck` - Type check TypeScript
- `npm test` - Run tests
- `npm run test:run` - Run tests once

## API Usage Examples

### Authentication

**Login:**
```bash
# macOS/Linux
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "johndoe", "email": "john@example.com"}'

# Windows (PowerShell)
curl.exe -X POST http://localhost:8000/auth/login `
  -H "Content-Type: application/json" `
  -d '{\"username\": \"johndoe\", \"email\": \"john@example.com\"}'
```

**Response:**
```json
{
  "user": {
    "id": "user_1",
    "username": "johndoe",
    "email": "john@example.com",
    "avatar": "..."
  },
  "token": "dummy_token_..."
}
```

### Cases

**Get all cases:**
```bash
# macOS/Linux/Windows
curl http://localhost:8000/cases
```

**Get case details:**
```bash
# macOS/Linux/Windows
curl http://localhost:8000/cases/case_1
```

### Documents

**Upload a PDF:**
```bash
# macOS/Linux
curl -X POST "http://localhost:8000/documents/upload?case_id=case_1" \
  -F "file=@/path/to/document.pdf"

# Windows (PowerShell)
curl.exe -X POST "http://localhost:8000/documents/upload?case_id=case_1" `
  -F "file=@C:\path\to\document.pdf"
```

**Get PDF file:**
```bash
# macOS/Linux/Windows
curl http://localhost:8000/documents/doc_1/pdf --output document.pdf
```

## Frontend Features

- **Modern UI**: Built with Tailwind CSS and shadcn/ui components
- **State Management**: 
  - TanStack Query for server state
  - Zustand for UI state
- **PDF Viewer**: In-browser PDF viewing with iframe
- **Document Upload**: Drag-and-drop file upload with progress
- **Type Safety**: Full TypeScript support
- **Responsive Design**: Works on desktop and mobile browsers
- **Error Handling**: Comprehensive error handling and user feedback
- **Loading States**: Proper loading indicators throughout

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **Python 3.8+**: Python runtime

### Frontend
- **React 19**: UI library
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **React Router**: Client-side routing
- **TanStack Query**: Server state management
- **Zustand**: UI state management
- **Tailwind CSS**: Utility-first CSS framework
- **shadcn/ui**: UI component library
- **Axios**: HTTP client
- **Vitest**: Testing framework

## Development Notes

- **Backend CORS**: CORS middleware is configured to allow requests from the frontend
- **API Base URL**: Defaults to `http://localhost:8000`. Can be configured via `VITE_API_BASE_URL` environment variable
- **Dummy Data**: The backend includes pre-configured dummy data for development and demos
- **PDF Storage**: Uploaded PDFs are stored in `backend/server/data/`
- **Hot Reload**: Both frontend (Vite) and backend (uvicorn --reload) support hot reload

## Environment Variables

### Frontend

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### Backend

No environment variables required for basic setup. See `.env.example` if available.

## Testing

### Backend Tests
```bash
# macOS/Linux/Windows
# (Tests to be added)
```

### Frontend Tests
```bash
# macOS/Linux/Windows
cd frontend
npm test
```

## Troubleshooting

### Port Already in Use

**Backend (port 8000):**
```bash
# macOS/Linux
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Frontend (port 3000):**
```bash
# macOS/Linux
lsof -ti:3000 | xargs kill -9

# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Python Virtual Environment Issues

**macOS/Linux:**
```bash
# Deactivate and recreate
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```cmd
# Deactivate and recreate
deactivate
rmdir /s venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Node Modules Issues

```bash
# macOS/Linux/Windows
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Windows (alternative):**
```cmd
cd frontend
rmdir /s node_modules
del package-lock.json
npm install
```

## Team Collaboration

- **Backend team**: Work in the `backend/` directory
- **Frontend team**: Work in the `frontend/` directory
- **API Contract**: Documented in backend routes and frontend TypeScript types
- **Git Workflow**: Use feature branches and pull requests
- **Testing**: Run tests before committing changes

## Project Status

✅ **Completed:**
- Authentication system
- Case management
- Document listing and viewing
- PDF upload functionality
- PDF viewer component
- Dummy data setup

🚧 **In Progress:**
- Document processing pipeline
- Stakeholder identification
- Issue tracking

📋 **Planned:**
- Database integration
- Real user authentication
- Document annotation
- Advanced PDF features

---

Built for WOO (Wet Open Overheid) Project 🚀
