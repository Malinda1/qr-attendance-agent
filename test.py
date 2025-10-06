#!/usr/bin/env python3
"""
test_config.py
--------------
Simple test harness to validate backend/app/config.py (Settings).

- Prints selected settings values (masks secrets).
- Checks required environment variables exist.
- Verifies directories were created.
- Exits with code 0 on success, 1 on failure.
"""

import sys
import traceback
from pathlib import Path
from typing import Iterable

# Import settings (adjust import path if you placed test file elsewhere)
try:
    # If running from backend/app, this import will work
    from config import settings, Settings  # type: ignore
except Exception:
    # Try importing as package if run from project root
    try:
        from backend.app.config import settings, Settings  # type: ignore
    except Exception as e:
        print("❌ Failed to import settings from config.py")
        traceback.print_exc()
        sys.exit(1)


def mask_secret(s: str, keep: int = 4) -> str:
    """Mask a secret except for the last `keep` characters."""
    if not s:
        return "<empty>"
    if len(s) <= keep:
        return "*" * len(s)
    return "*" * (len(s) - keep) + s[-keep:]


def check_env_keys(keys: Iterable[str]) -> bool:
    """Ensure listed keys exist in process environment (via settings)."""
    missing = []
    for key in keys:
        val = getattr(settings, key, None)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            missing.append(key)
    if missing:
        print(f"❌ Missing required settings: {missing}")
        return False
    print("✅ All required env/settings keys are present.")
    return True


def check_directories(paths: Iterable[Path]) -> bool:
    """Confirm directories exist and are writable."""
    bad = []
    for p in paths:
        try:
            if not p.exists():
                bad.append((p, "does not exist"))
            elif not p.is_dir():
                bad.append((p, "not a directory"))
            else:
                # Try writing a tiny temporary file to test writability
                tmp = p / ".test_write"
                with open(tmp, "w") as f:
                    f.write("ok")
                tmp.unlink()
        except Exception as e:
            bad.append((p, str(e)))
    if bad:
        print("❌ Directory checks failed for:")
        for p, reason in bad:
            print(f"   - {p}: {reason}")
        return False
    print("✅ Directory checks passed (exist and writable).")
    return True


def main():
    print("🔎 Testing config.py -> settings\n")

    try:
        # Print important settings (mask secrets)
        print("Settings summary:")
        print(f"  APP_HOST: {settings.APP_HOST}")
        print(f"  APP_PORT: {settings.APP_PORT}")
        print(f"  LOG_LEVEL: {settings.LOG_LEVEL}")
        print(f"  AIRTABLE_BASE_ID: {getattr(settings, 'AIRTABLE_BASE_ID', '<not set>')}")
        # Mask secrets
        print(f"  AIRTABLE_API_KEY: {mask_secret(getattr(settings, 'AIRTABLE_API_KEY', ''))}")
        print(f"  GEMINI_API_KEY: {mask_secret(getattr(settings, 'GEMINI_API_KEY', ''))}")
        print(f"  DEFAULT_USERNAME: {getattr(settings, 'DEFAULT_USERNAME', '<not set>')}")
        # Paths
        print(f"  QR_CODE_DIR: {settings.QR_CODE_DIR}")
        print(f"  SCREENSHOT_DIR: {settings.SCREENSHOT_DIR}")
        print(f"  LOG_DIR: {settings.LOG_DIR}")
        print()

        # Required keys to validate (update list if you have more required vars)
        required_keys = [
            "GEMINI_API_KEY",
            "AIRTABLE_API_KEY",
            "AIRTABLE_BASE_ID",
            "DEFAULT_USERNAME",
            "DEFAULT_PASSWORD",
        ]

        ok_env = check_env_keys(required_keys)

        # Check directories
        dir_paths = [settings.QR_CODE_DIR, settings.SCREENSHOT_DIR, settings.LOG_DIR]
        ok_dirs = check_directories(dir_paths)

        if ok_env and ok_dirs:
            print("\n✅ config.py appears to be working correctly.")
            sys.exit(0)
        else:
            print("\n❌ config.py check failed. See messages above.")
            sys.exit(1)

    except Exception:
        print("❌ An unexpected error occurred while testing config.py")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
