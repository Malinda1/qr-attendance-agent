#!/usr/bin/env python3
"""
Test script for ScrapingService
Checks URL accessibility and attendance marking automation
"""

import sys
import traceback
from pathlib import Path
from datetime import datetime

try:
    # Adjust import according to your project structure
    from backend.app.services.scraping_service import ScrapingService, scraping_service
    from backend.app.config import settings
except Exception:
    try:
        # fallback if running from backend/app
        from backend.app.services.scraping_service import ScrapingService, scraping_service
        from backend.app.config import settings
    except Exception:
        print("❌ Failed to import ScrapingService or settings")
        traceback.print_exc()
        sys.exit(1)


def main():
    print("🔎 Running ScrapingService tests...\n")

    try:
        service: ScrapingService = scraping_service

        # Step 1: Test connection to QR URL
        test_qr_url = "https://students.nsbm.ac.lk/attendence/index.php?id=52202002751_84783"
        print(f"✅ Testing URL accessibility: {test_qr_url}")
        accessible = service.test_connection(test_qr_url)
        if not accessible:
            raise Exception("❌ Test connection failed: URL not accessible")
        print(f"✅ URL accessible")

        # Step 2: Test attendance marking
        print(f"✅ Testing attendance marking for URL: {test_qr_url}")
        result = service.mark_attendance(
            qr_url=test_qr_url,
            username=None,  # Use default credentials
            password=None
        )
        print(f"✅ Attendance marking result: {result}")
        screenshot_path = result.get("screenshot_path")
        if screenshot_path:
            screenshot_file = Path(screenshot_path)
            if not screenshot_file.exists():
                raise FileNotFoundError(f"❌ Screenshot not found: {screenshot_path}")
            print(f"✅ Screenshot saved at: {screenshot_path}")
        else:
            print("⚠️ No screenshot returned")

        print("\n🎉 ScrapingService tests passed successfully.")
        sys.exit(0)

    except Exception as e:
        print("❌ ScrapingService test failed:", str(e))
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
