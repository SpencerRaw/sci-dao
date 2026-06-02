#!/bin/bash
# Wrapper to run SciDAO pipeline with API key from .env
set -e

# Load the API key
KEY_LINE=$(grep "DEEPSEEK" "$HOME/.hermes/.env" | head -1)
if [ -z "$KEY_LINE" ]; then
    echo "ERROR: No DEEPSEEK key found in ~/.hermes/.env"
    exit 1
fi

# Export (safely)
eval "export $KEY_LINE"

DOMAIN="${1:-carbon dots for photodynamic cancer therapy}"
cd "$HOME/Desktop/dw/sci-dao"
~/.hermes/hermes-agent/venv/bin/python3 -m scidao full "$DOMAIN"
