# WOO Frontend

Modern web application built with React, TypeScript, Tailwind CSS, and shadcn/ui.

## Tech Stack

- **React 19** - UI library with hooks
- **TypeScript 5.9** - Type safety
- **Vite 7** - Build tool and dev server
- **React Router 7** - Client-side routing
- **TanStack Query 5** - Server state management
- **Zustand 5** - UI state management
- **Tailwind CSS 4** - Utility-first styling
- **shadcn/ui** - Accessible component library
- **Vitest** - Unit testing
- **Testing Library** - Component testing

## Architecture

This frontend follows a clear separation of concerns:

- **Zustand**: UI state (modals, filters, selections, local UI state)
- **TanStack Query**: Server state (API data, caching, background sync)
- **React Router**: Client-side routing
- **Tailwind + shadcn/ui**: Consistent design system

## Project Structure

```
frontend/
├── src/
│   ├── pages/              # Page components (route handlers)
│   ├── layouts/            # Layout wrappers with route guards
│   ├── components/
│   │   ├── ui/            # shadcn/ui components
│   │   └── features/      # Feature-specific components
│   ├── api/               # API client and TanStack Query config
│   ├── store/             # Zustand stores (UI state only)
│   ├── types/             # TypeScript type definitions
│   ├── hooks/             # Custom React hooks
│   ├── lib/               # Utility functions
│   └── test/              # Test setup and utilities
├── public/                # Static assets
├── components.json        # shadcn/ui configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── vite.config.ts         # Vite configuration
├── vitest.config.ts       # Vitest configuration
└── tsconfig.json          # TypeScript configuration
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd frontend
npm install
```

### Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

### Building

Build for production:

```bash
npm run build
```

Preview production build:

```bash
npm run preview
```

### Testing

Run tests in watch mode:

```bash
npm run test
```

Run tests once:

```bash
npm run test:run
```

Run tests with UI:

```bash
npm run test:ui
```

### Type Checking

```bash
npm run typecheck
```

### Linting

```bash
npm run lint
```

## Features

### Authentication

- Login page with form validation
- Session persistence using sessionStorage
- Protected routes with automatic redirection
- Logout functionality

### State Management

- **Auth Store**: Manages authentication state (login, logout, session)
- Session restoration on app load

### Routing

- `/login` - Public authentication page
- `/workspaces` - Protected workspace page (requires authentication)
- `/` - Redirects to workspaces (or login if not authenticated)

## Environment Variables

Create a `.env` file in the frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Adding Components

Add new shadcn/ui components:

```bash
npx shadcn@latest add [component-name]
```

Examples:
```bash
npx shadcn@latest add dialog
npx shadcn@latest add dropdown-menu
npx shadcn@latest add table
```

## API Integration

The API client is configured in `src/api/client.ts` with:
- Axios instance with base URL
- TanStack Query client with automatic caching
- Background refetching on window focus
- Automatic retry logic

## Testing

Tests are located in `__tests__` directories next to the code they test:
- `src/store/__tests__/` - Store tests
- `src/pages/__tests__/` - Page tests
- `src/components/__tests__/` - Component tests

Example test:
```typescript
import { describe, it, expect } from 'vitest';
import { useAuthStore } from '../auth-store';

describe('Auth Store', () => {
  it('should login successfully', () => {
    const { login } = useAuthStore.getState();
    login('testuser', 'test@example.com');
    
    const state = useAuthStore.getState();
    expect(state.isLoggedIn).toBe(true);
  });
});
```

## Code Style

- Use TypeScript strict mode
- Follow clean code guidelines
- Use named exports for components
- Keep components small and focused
- Extract repeated logic into hooks

## Development Workflow

1. Create feature branch
2. Make changes
3. Run type check: `npm run typecheck`
4. Run linter: `npm run lint`
5. Run tests: `npm run test:run`
6. Commit changes

## Known Limitations

- Mock authentication (no real backend integration yet)
- SessionStorage used for session persistence (not production-ready)
- No token-based authentication
- Basic workspace page (no actual features yet)

## Next Steps

- Integrate with backend authentication API
- Implement JWT or session cookie authentication
- Add password strength validation
- Build out workspace features
- Add document creation/editing
- Implement real-time collaboration

## License

Private project
