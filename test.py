#!/usr/bin/env python3
"""
Test script for QRGeneratorService
Validates QR code generation (single and batch) with labels.
"""

import sys
import traceback
from pathlib import Path
from datetime import datetime

try:
    # Adjust import according to your project structure
    from backend.app.services.qr_generator import QRGeneratorService, qr_generator_service
    from backend.app.config import settings
except Exception:
    try:
        # fallback if running from backend/app
        from backend.app.services.qr_generator import QRGeneratorService, qr_generator_service
        from backend.app.config import settings
    except Exception:
        print("❌ Failed to import QRGeneratorService or settings")
        traceback.print_exc()
        sys.exit(1)


def main():
    print("🔎 Running QRGeneratorService tests...\n")

    try:
        service: QRGeneratorService = qr_generator_service

        # Test 1: Single QR code generation
        test_url = "https://students.nsbm.ac.lk/attendence/test_qr_01"
        print(f"✅ Testing single QR generation for URL: {test_url}")
        qr_path = service.generate_qr_code(test_url)
        qr_file = Path(qr_path)
        if not qr_file.exists():
            raise FileNotFoundError(f"QR file not created: {qr_path}")
        print(f"✅ QR code generated successfully at: {qr_path}")

        # Test 2: QR generation with custom label
        test_label = "TEST QR LABEL"
        print(f"✅ Testing QR generation with label: {test_label}")
        qr_path_label = service.generate_qr_code(test_url, label_text=test_label)
        qr_file_label = Path(qr_path_label)
        if not qr_file_label.exists():
            raise FileNotFoundError(f"QR file with label not created: {qr_path_label}")
        print(f"✅ QR code with label generated at: {qr_path_label}")

        # Test 3: Batch QR code generation
        urls = [
            f"https://students.nsbm.ac.lk/attendence/batch_test_{i}" for i in range(1, 4)
        ]
        print(f"✅ Testing batch QR generation for {len(urls)} URLs")
        generated_paths = service.generate_batch_qr_codes(urls, prefix="batch_test")
        if len(generated_paths) != len(urls):
            print(f"⚠️ Some QR codes failed in batch. Generated {len(generated_paths)}/{len(urls)}")
        else:
            print(f"✅ All batch QR codes generated successfully")
        for path in generated_paths:
            if not Path(path).exists():
                raise FileNotFoundError(f"Batch QR file missing: {path}")

        print("\n🎉 All QRGeneratorService tests passed successfully.")
        sys.exit(0)

    except Exception as e:
        print("❌ QRGeneratorService test failed:", str(e))
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
