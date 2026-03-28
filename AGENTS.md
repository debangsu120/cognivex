# Agent Guidelines for CogniVex AI Interview Platform

## Project Overview

This is a monorepo containing:
- **Frontend**: React Native/Expo mobile app in `ai-interviewer/`
- **Backend**: FastAPI Python API in `backend/`

## Build, Lint, and Test Commands

### Backend (Python/FastAPI)

```bash
# Install dependencies
cd backend && pip install -r requirements.txt
pip install pytest pytest-asyncio httpx ruff mypy

# Run linter (ruff)
ruff check app/ --output-format=github

# Run type checker (mypy)
mypy app/ --ignore-missing-imports

# Run all tests
pytest tests/ -v

# Run single test file
pytest tests/test_placeholder.py -v

# Run single test function
pytest tests/test_placeholder.py::test_function_name -v

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=xml

# Start development server
cd backend && uvicorn app.main:app --reload --port 8000
```

### Frontend (React Native/Expo)

```bash
# Install dependencies
cd ai-interviewer && npm install

# Start development server
npm start
npx expo start

# Run on web
npx expo start --web

# Run on Android
npx expo run:android

# Run on iOS
npx expo run:ios
```

## Code Style Guidelines

### Python (Backend)

**Imports**
- Group imports: standard library, third-party, local application
- Sort within groups alphabetically
- Use absolute imports: `from app.routers import auth`
- Avoid wildcard imports: `from app import *`

**Formatting**
- Line length: 100 characters (ruff default)
- Use 4 spaces for indentation
- Use Black formatting (integrated in ruff)
- Add trailing commas in multi-line structures

**Types**
- Use type hints for all function parameters and return values
- Prefer `Optional[X]` over `X | None`
- Use Pydantic models for request/response validation
- Run mypy before committing: `mypy app/ --ignore-missing-imports`

**Naming**
- Classes: `PascalCase` (e.g., `UserService`)
- Functions/methods: `snake_case` (e.g., `get_current_user`)
- Constants: `UPPER_SNAKE_CASE`
- Variables: `snake_case`
- Async functions: prefix with `async_` or use `await` properly

**Error Handling**
- Use custom exceptions from `app/exceptions.py`
- Raise `HTTPException` for API errors
- Use try/except only when necessary, prefer early returns
- Log errors with context using the logger
- Never expose internal error details in production

**API Design**
- All routes go under `/api/v1/` prefix
- Use proper HTTP methods: GET (read), POST (create), PUT/PATCH (update), DELETE (delete)
- Return appropriate status codes: 200, 201, 204, 400, 401, 403, 404, 500
- Use Pydantic models for request body validation
- Document endpoints with docstrings

### TypeScript/React Native (Frontend)

**Imports**
- Use absolute imports from project root (configured in tsconfig)
- Order: React/hooks, third-party, local components/hooks/utils, styles
- Example: `import { useState } from 'react'` then `import { useAuth } from '@/contexts/AuthContext'`

**Formatting**
- Use 2 spaces for indentation
- Maximum line length: 100 characters
- Use Prettier for formatting (default in Expo)
- Use single quotes for strings

**Types**
- Enable strict TypeScript mode (already configured)
- Define interfaces for props and data structures
- Avoid `any` - use `unknown` or proper types
- Use TypeScript's built-in utility types (`Partial`, `Required`, etc.)

**Naming**
- Components: `PascalCase` (e.g., `HomeScreen`)
- Hooks: `camelCase` starting with `use` (e.g., `useCandidateDashboard`)
- Functions: `camelCase`
- Constants: `UPPER_SNAKE_CASE` in dedicated files
- Files: `kebab-case.ts` for utilities, `PascalCase.tsx` for components

**Component Structure**
- Use functional components with hooks
- Keep components focused (single responsibility)
- Extract reusable UI into `components/` directory
- Extract business logic into `hooks/` directory
- Use composition over inheritance

**Styling**
- Use NativeWind/Tailwind utility classes
- Define shared constants in `constants/theme.ts`
- Avoid inline styles except for dynamic values
- Use `StyleSheet.create` for complex styles

**State Management**
- Use React Context for global state (e.g., AuthContext)
- Use local useState for component-specific state
- Use custom hooks for reusable stateful logic
- Avoid prop drilling - use context or pass data via navigation params

**Error Handling**
- Handle loading and error states in UI
- Show user-friendly error messages
- Use try/catch for async operations
- Implement proper TypeScript error types

## Project Structure

### Backend
```
backend/
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Settings configuration
│   ├── deps.py           # Dependency injection
│   ├── exceptions.py     # Custom exceptions
│   ├── routers/         # API route handlers
│   ├── services/         # Business logic
│   ├── models/           # Pydantic models
│   └── middleware/       # Custom middleware
├── tests/                # Test files
├── requirements.txt      # Python dependencies
└── pytest.ini           # Pytest configuration
```

### Frontend
```
ai-interviewer/
├── app/                  # Expo Router screens
├── components/          # Reusable UI components
├── constants/           # Theme, configuration
├── contexts/            # React Context providers
├── hooks/               # Custom React hooks
├── services/            # API clients
├── types/               # TypeScript types
└── package.json         # NPM dependencies
```

## Testing Guidelines

- Write tests for all new features and bug fixes
- Use descriptive test names: `test_should_return_401_for_invalid_token`
- Mock external dependencies (Supabase, external APIs)
- Use `@pytest.mark.asyncio` for async test functions
- Keep tests in `tests/` directory with `test_*.py` naming
- Target 80% code coverage for critical paths

## Git Conventions

- Use meaningful commit messages: "add user authentication endpoint"
- Create feature branches: `feature/add-job-search`
- Fix branches: `fix/auth-token-expiry`
- Run lint and tests before pushing
- Use conventional commits format if possible