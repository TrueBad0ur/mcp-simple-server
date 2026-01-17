#!/usr/bin/env python3
"""
Configuration settings for MCP server
"""

import os

# Server configuration
SERVER_NAME = "simple-utils-server"
SERVER_VERSION = "1.0.0"

# Logging configuration
LOG_FILE = "logs/requests_log.txt"

# Authentication configuration
API_KEY = os.getenv("MCP_API_KEY")
API_KEY_NAME = "X-API-Key"

# Server settings
PORT = int(os.getenv("PORT", "8000"))
HOST = "0.0.0.0"

# CORS settings
CORS_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Timeouts
COMMAND_TIMEOUT = 30  # seconds for shell commands
MAX_RANDOM_NUMBERS = 100  # maximum count for random number generation