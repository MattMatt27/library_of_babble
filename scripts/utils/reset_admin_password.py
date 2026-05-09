#!/usr/bin/env python3
"""Reset an admin user's password in the local database.

Usage:
    .venv/bin/python scripts/utils/reset_admin_password.py [username]

Prompts for the new password twice (hidden). Username defaults to 'matt'.
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from werkzeug.security import generate_password_hash

from app import create_app
from app.auth.models import User
from app.extensions import db


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else 'matt'

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found.")
            sys.exit(1)

        print(f"Resetting password for '{username}' (role: {user.role}).")
        pw1 = getpass.getpass("New password: ")
        pw2 = getpass.getpass("Confirm password: ")

        if pw1 != pw2:
            print("Passwords do not match. No changes made.")
            sys.exit(1)
        if len(pw1) < 6:
            print("Password must be at least 6 characters. No changes made.")
            sys.exit(1)

        user.password = generate_password_hash(pw1)
        db.session.commit()
        print(f"Password updated for '{username}'.")


if __name__ == '__main__':
    main()
