#!/usr/bin/env python3
"""
Server startup script for Shelly Manager API.
"""

import os

import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"Starting Shelly Manager API on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"OpenAPI docs: http://{host}:{port}/docs")
    print(f"OpenAPI JSON: http://{host}:{port}/openapi.json")
    print(f"Health check: http://{host}:{port}/api/health")

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug",
    )
