#!/usr/bin/env python3
"""CLI management script for Mattequiz."""
import os
import sys
from database import init_db, create_invite_token, get_user_login_token

def cmd_generate_token():
    init_db()
    token = create_invite_token()
    base_url = os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/")
    print(f"{base_url}/register/{token}")

def cmd_get_login_link():
    if len(sys.argv) < 3:
        print("Bruk: python manage.py get-login-link <navn>")
        sys.exit(1)
    name = sys.argv[2]
    init_db()
    token = get_user_login_token(name)
    if not token:
        print(f"Fant ingen bruker med navn '{name}'.")
        sys.exit(1)
    base_url = os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/")
    print(f"{base_url}/enter/{token}")

COMMANDS = {
    "generate-token": cmd_generate_token,
    "get-login-link": cmd_get_login_link,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Bruk: python manage.py [{' | '.join(COMMANDS)}]")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
