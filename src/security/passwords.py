import re

from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


def password_validator(password: str):
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        raise ValueError(
            "Password must contain at least one uppercase letter."
        )

    if not re.search(r"[a-z]", password):
        raise ValueError(
            "Password must contain at least one lowercase letter."
        )

    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    return password
