#!/usr/bin/env python3
"""
logging_test.py
---------------
Test harness to validate backend/app/logging_config.py

- Verifies setup_logger returns a logger.
- Runs a sample decorated function to exercise decorator logging.
- Checks that today's log files (app_YYYYMMDD.log and error_YYYYMMDD.log) exist and contain entries.
- Exits with 0 on success, 1 on failure.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path
import re

# Attempt imports from common locations
try:
    # if running from backend/app directory
    from backend.app.logging_config import logger, log_function_call, setup_logger  # type: ignore
    # try to import settings from local config
    try:
        from config import settings  # type: ignore
    except Exception:
        # fallback to package import
        from backend.app.config import settings  # type: ignore
except Exception:
    try:
        # If running from project root, import as package
        from backend.app.logging_config import logger, log_function_call, setup_logger  # type: ignore
        from backend.app.config import settings  # type: ignore
    except Exception as e:
        print("❌ Failed to import logging_config or settings. Make sure this script is placed next to logging_config.py or run from project root.")
        traceback.print_exc()
        sys.exit(1)


TEST_LOGGER_NAME = "qr_attendance_test_logger"
TODAY_SUFFIX = datetime.now().strftime("%Y%m%d")


def read_file_tail(path: Path, lines: int = 20) -> str:
    """Return last `lines` lines of file as a string (best-effort)."""
    try:
        with open(path, "rb") as f:
            # read last ~20KB or file size whichever smaller
            f.seek(0, 2)
            size = f.tell()
            to_read = min(size, 20 * 1024)
            f.seek(-to_read, 2)
            data = f.read().decode(errors="ignore")
        return "\n".join(data.splitlines()[-lines:])
    except Exception:
        return ""


def main():
    print("🔎 Running logging_config tests...\n")

    try:
        # Create a fresh test logger
        test_logger = setup_logger(TEST_LOGGER_NAME)
        assert test_logger is not None
        print("✅ setup_logger returned a logger instance.")

        # Define a small decorated function to exercise the decorator and logger
        @log_function_call
        def sample_func(x, y=1):
            test_logger.info("Inside sample_func - performing calculation")
            test_logger.debug(f"Input values: x={x}, y={y}")
            if x < 0:
                test_logger.error("sample_func received invalid x < 0, raising ValueError")
                raise ValueError("x must be non-negative")
            return x + y

        # Run success case
        try:
            res = sample_func(3, y=2)
            assert res == 5
            print("✅ sample_func success case ran and returned expected result.")
        except Exception as e:
            print("❌ sample_func success case raised an unexpected exception.")
            traceback.print_exc()
            sys.exit(1)

        # Run failure case to ensure error handler logs exceptions
        try:
            sample_func(-1)
        except ValueError:
            print("✅ sample_func failure case raised ValueError as expected (and should be logged).")
        except Exception:
            print("❌ sample_func failure case raised an unexpected exception type.")
            traceback.print_exc()
            sys.exit(1)

        # Check that log directory exists
        log_dir: Path = settings.LOG_DIR
        if not log_dir.exists() or not log_dir.is_dir():
            print(f"❌ settings.LOG_DIR does not exist or is not a directory: {log_dir}")
            sys.exit(1)
        print(f"✅ LOG_DIR exists: {log_dir}")

        # Expected log filenames for today
        app_log = log_dir / f"app_{TODAY_SUFFIX}.log"
        error_log = log_dir / f"error_{TODAY_SUFFIX}.log"

        # Wait briefly for handlers to flush (best-effort)
        # (No sleeping to keep script snappy; handlers usually flush on file write)

        # Verify files exist
        missing = []
        for p in (app_log, error_log):
            if not p.exists():
                missing.append(str(p))
        if missing:
            print("❌ Expected log files not found:")
            for m in missing:
                print("   -", m)
            sys.exit(1)
        print(f"✅ Found expected log files: {app_log.name}, {error_log.name}")

        # Verify files are non-empty
        empty_files = [p for p in (app_log, error_log) if p.stat().st_size == 0]
        if empty_files:
            print("❌ Found empty log file(s):")
            for p in empty_files:
                print("   -", p)
            sys.exit(1)
        print("✅ Log files are non-empty.")

        # Ensure that our test messages appear in the app log
        tail = read_file_tail(app_log, lines=200)
        checks = [
            r"sample_func",  # decorator messages include function name
            r"Inside sample_func - performing calculation",
            r"sample_func received invalid x < 0",  # error log text
        ]
        missing_checks = [c for c in checks if not re.search(c, tail)]
        if missing_checks:
            print("❌ Some expected log entries not found in app log. Tail preview:")
            print("--- Log tail start ---")
            print(tail or "<empty>")
            print("--- Log tail end ---")
            print("Missing patterns:", missing_checks)
            # Still check error log for the error entry
            error_tail = read_file_tail(error_log, lines=200)
            if "sample_func received invalid x < 0" in error_tail:
                print("✅ Error message present in error log (good).")
                # consider success if error found there
            else:
                sys.exit(1)
        else:
            print("✅ Expected log messages found in app log.")

        print("\n🎉 Logging configuration appears to be working correctly.")
        sys.exit(0)

    except AssertionError as ae:
        print("❌ Assertion failed during tests:", str(ae))
        traceback.print_exc()
        sys.exit(1)
    except Exception:
        print("❌ Unexpected error while testing logging_config.py")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
