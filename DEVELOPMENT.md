# Development Guide

Development setup guide for Shelly Manager, covering backend (Core/API/CLI) and web development.

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **Python 3.11+** and **uv** (for local development)
- **Node.js 20+** (for web development)

### Option 1: Docker Development (Recommended)

```bash
# Clone repository
git clone https://github.com/jfmlima/shelly-manager.git
cd shelly-manager

# Start development environment
docker-compose up -d

# Access services:
# - API: http://localhost:8000
# - Web UI: http://localhost:5173
# - API Docs: http://localhost:8000/docs
```

### Option 2: Local Development

1. **Install uv:**

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # or
   pip install uv
   ```

2. **Install dependencies:**

   ```bash
   # Install all workspace packages with dev dependencies
   uv sync --extra dev
   ```

3. **Test everything works:**

   ```bash
   # Test all packages
   make test

   # Test specific packages
   make test-core
   make test-api
   make test-cli
   ```

## Backend Development (Core/API/CLI)

Shelly Manager follows Clean Architecture principles with three main backend packages:

### Package Structure

```
packages/
├── core/    # 🏛️ Business logic, domain models, use cases
├── api/     # 🌐 HTTP REST API (Litestar framework)
└── cli/     # 💻 Command-line interface (Click framework)
```

### Workspace Setup

The project uses **uv** for workspace dependencies and consistent version management:

```bash
# Install all packages with dev dependencies
uv sync --extra dev

# Install without dev dependencies (production)
uv sync --no-dev

# Install specific package only
uv sync --package shelly-manager-core
uv sync --package shelly-manager-api
uv sync --package shelly-manager-cli
```

### Running Backend Services

```bash
# CLI tool
uv run shelly-manager --help
uv run shelly-manager scan --range 192.168.1.0/24

# API server
uv run --package shelly-manager-api python -m api.main
# Visit: http://localhost:8000/docs

# Core library testing
uv run --package shelly-manager-core python -c "
from core.domain.entities.shelly_device import ShellyDevice
print('✅ Core package working!')
"
```

### Backend Development Workflow

#### Code Quality

```bash
# Format code (black, ruff)
make format

# Check linting (ruff, mypy)
make lint

# Run all quality checks
make check
```

#### Testing

```bash
# Run all backend tests
make test

# Test specific packages
make test-core
make test-api
make test-cli

# Run with coverage
make test-coverage

# Run specific test files
uv run --package shelly-manager-core pytest packages/core/tests/unit/
uv run --package shelly-manager-api pytest packages/api/tests/ -v
```

#### Architecture Principles

- **Domain-Driven Design**: Business logic in `core/domain/`
- **Clean Architecture**: Dependencies point inward to domain
- **Dependency Injection**: Use containers for external dependencies
- **Async/Await**: Async operations for network calls
- **Type Safety**: Comprehensive type hints with mypy

### Adding New Features

#### Core Package (Business Logic)

```bash
# Domain entities
packages/core/src/core/domain/entities/

# Use cases (application logic)
packages/core/src/core/use_cases/

# Gateways (external interfaces)
packages/core/src/core/gateways/
```

#### API Package (REST Endpoints)

```bash
# Controllers (HTTP handlers)
packages/api/src/api/controllers/

# DTOs (request/response models)
packages/api/src/api/presentation/dto/
```

#### CLI Package (Commands)

```bash
# Command groups
packages/cli/src/cli/commands/

# Use cases (CLI-specific logic)
packages/cli/src/cli/use_cases/
```

## Web Development

The web interface is built with React, TypeScript, and modern tooling:

### Tech Stack

- **Frontend**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Framework**: shadcn/ui + Tailwind CSS
- **State Management**: TanStack Query (React Query v5)
- **Forms**: React Hook Form + Zod validation
- **Tables**: TanStack Table

### Web Development Setup

```bash
# Navigate to web package
cd packages/web

# Install dependencies
npm install

# Start development server
npm run dev
# Visit: http://localhost:5173

# Build for production
npm run build

# Preview production build
npm run preview
```

### Web Development Workflow

#### Code Quality

```bash
cd packages/web

# Lint TypeScript/React code
npm run lint

# Check TypeScript types
npm run type-check

# Format code (Prettier)
npm run format

# Check formatting
npm run format:check
```

#### Environment Configuration

```bash
# Copy environment template
cp packages/web/env.example packages/web/.env.local

# Configure API endpoint
echo "VITE_BASE_API_URL=http://localhost:8000" > packages/web/.env.local
```

#### Adding New Features

##### Components

```bash
# UI components
packages/web/src/components/ui/

# Feature components
packages/web/src/components/dashboard/
packages/web/src/components/device-detail/

# Layout components
packages/web/src/components/layout/
```

##### Pages and Routing

```bash
# Page components
packages/web/src/pages/

# Add routes in
packages/web/src/App.tsx
```

##### API Integration

```bash
# API client and utilities
packages/web/src/lib/api.ts

# Type definitions
packages/web/src/types/api.ts
```

### Development Principles

#### React Best Practices

- **Functional Components**: Use hooks exclusively
- **Performance**: Memoize expensive operations with `useMemo`/`useCallback`
- **Error Boundaries**: Wrap components for error handling
- **Custom Hooks**: Extract reusable logic

#### State Management

- **Server State**: TanStack Query for API data
- **Component State**: React `useState`/`useReducer`
- **URL State**: React Router for navigation state
- **Local Storage**: Custom hooks for persistence

#### Type Safety

- **Strict TypeScript**: No `any` types
- **API Types**: Shared type definitions with backend
- **Form Validation**: Zod schemas for runtime validation

## Contribution Workflow

### Git Workflow

```bash
# 1. Fork and clone the repository
git clone https://github.com/your-username/shelly-manager.git
cd shelly-manager

# 2. Create a feature branch
git checkout -b feature/amazing-feature

# 3. Make your changes and commit
git add .
git commit -m "feat: add amazing feature"

# 4. Push and create a pull request
git push origin feature/amazing-feature
```

### Development Standards

#### Code Style

- **Python**: Follow PEP 8, use `black` and `ruff`
- **TypeScript**: Follow Airbnb style guide, use Prettier
- **Commits**: Use conventional commits (feat:, fix:, docs:, etc.)

#### Testing Requirements

- **Unit Tests**: Cover all new business logic
- **Integration Tests**: Test API endpoints and CLI commands
- **Type Safety**: Ensure all code passes mypy/TypeScript checks

#### Documentation

- **Code Documentation**: Use docstrings and JSDoc comments
- **README Updates**: Update relevant package READMEs
- **API Documentation**: Update OpenAPI specs for API changes

### Available Make Commands

```bash
# Quality and Testing
make lint           # Run all linting (black, ruff, mypy, eslint)
make format         # Format all code (black, prettier)
make test           # Run all tests (backend + web)
make test-coverage  # Run tests with coverage reports

# Package-specific commands
make test-core      # Test core package only
make test-api       # Test API package only
make test-cli       # Test CLI package only
make test-web       # Test web package only

# Development
make install        # Install all packages
make install-dev    # Install with dev dependencies
make clean          # Clean build artifacts
make run-api        # Start API server locally
make run-web        # Start web dev server

# Docker development
make docker-build   # Build all Docker images
make docker-up      # Start development stack
make docker-down    # Stop development stack
```

### Pre-commit Hooks

Pre-commit hooks ensure code quality before commits:

```bash
# Install pre-commit hooks (one-time setup)
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Skip hooks (not recommended)
git commit --no-verify
```

The hooks automatically:

- Format code with black/prettier
- Run linting with ruff/eslint
- Check type safety with mypy/TypeScript
- Run tests on affected packages
- Check YAML/JSON syntax

### Debugging and Troubleshooting

#### Backend Debugging

```bash
# Debug API server with breakpoints
uv run --package shelly-manager-api python -m debugpy --listen 5678 -m api.main

# Debug CLI commands
uv run --package shelly-manager-cli python -m debugpy --listen 5679 -m cli.__main__ scan --help

# Test individual components
uv run --package shelly-manager-core python -c "
import asyncio
from core.use_cases.scan_devices import ScanDevicesUseCase
# Add your debug code here
"
```

#### Web Debugging

```bash
cd packages/web

# Start with debug logging
DEBUG=true npm run dev

# Build analysis
npm run build -- --analyze

# TypeScript debugging
npx tsc --noEmit --incremental
```

#### Common Issues

1. **Docker volume permissions**: Use `:ro` (read-only) mounts for source code
2. **Port conflicts**: Check if ports 8000, 5173 are already in use
3. **uv sync issues**: Clear cache with `uv cache clean`
4. **Node modules**: Clear with `rm -rf node_modules && npm install`

## Additional Resources

- **Architecture Documentation**: See `packages/core/README.md`
- **API Documentation**: Visit `http://localhost:8000/docs` when API is running
- **CLI Documentation**: See `packages/cli/README.md`
- **Web UI Documentation**: See `packages/web/README.md`
- **Testing Documentation**: See `packages/cli/tests/README.md`

## Getting Help

- **Documentation Issues**: Check package-specific READMEs first
- **Bug Reports**: Open an issue with reproduction steps
- **Feature Ideas**: Start a discussion to validate the idea
- **Development Questions**: Check existing issues or start a discussion
