# Shelly Manager Core

The core business logic package for Shelly Manager. This package contains:

- **Domain entities**: Core business objects representing devices and operations
- **Value objects**: Immutable objects for data transfer and requests
- **Domain services**: Business logic services for device operations
- **Use cases**: Application business logic orchestration
- **Gateways**: Abstract interfaces for external dependencies
- **Shared utilities**: Configuration, logging, exceptions

## Architecture

This package follows Clean Architecture principles:

```
core/
├── domain/
│   ├── entities/         # Core business entities
│   ├── value_objects/    # Immutable value objects
│   ├── services/         # Domain business logic
│   └── enums/           # Domain enumerations
├── use_cases/           # Application business logic
├── gateways/            # Abstract interfaces
└── shared/              # Cross-cutting concerns
```

## Installation

Install the core package as a foundation for other packages.

## Development Setup

Set up development environment with testing capabilities.

## Usage

Import and use domain entities, services, and use cases for business logic operations.
```

## Dependencies

- `pydantic`: Data validation and serialization
- `structlog`: Structured logging
- `httpx`: HTTP client for device communication
- `requests`: HTTP requests library

## Development

See the main project README for development setup instructions.
