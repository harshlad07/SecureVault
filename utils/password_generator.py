"""Utilities to generate strong random passwords."""

import secrets
import string


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    """Generate a strong password using the requested character sets."""
    character_sets = []
    if use_lower:
        character_sets.append(string.ascii_lowercase)
    if use_upper:
        character_sets.append(string.ascii_uppercase)
    if use_digits:
        character_sets.append(string.digits)
    if use_symbols:
        character_sets.append("!@#$%^&*()-_=+[]{};:,.<>?/~")

    if not character_sets:
        raise ValueError("At least one character type must be selected")

    password_chars = [secrets.choice(charset) for charset in character_sets]
    remaining_length = max(length - len(password_chars), 0)
    all_characters = "".join(character_sets)
    password_chars += [secrets.choice(all_characters) for _ in range(remaining_length)]
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)
