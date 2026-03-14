#!/usr/bin/env python3
"""CLI management script for Mattequiz."""
import os
import sys
from database import init_db, create_invite_token

def cmd_generate_token():
    init_db()
    token = create_invite_token()
    base_url = os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/")
    print(f"{base_url}/register/{token}")

COMMANDS = {
    "generate-token": cmd_generate_token,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Bruk: python manage.py [{' | '.join(COMMANDS)}]")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
