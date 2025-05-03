#!/usr/bin/env python3

import sys
print("Python Path:")
for path in sys.path:
    print(f"  - {path}")

print("\nTesting imports:")
try:
    import pydantic
    print("✓ pydantic imported successfully")
except ImportError as e:
    print(f"✗ Error importing pydantic: {e}")

try:
    import loguru
    print("✓ loguru imported successfully")
except ImportError as e:
    print(f"✗ Error importing loguru: {e}")

try:
    import requests
    print("✓ requests imported successfully")
except ImportError as e:
    print(f"✗ Error importing requests: {e}")

try:
    import yaml
    print("✓ yaml imported successfully")
except ImportError as e:
    print(f"✗ Error importing yaml: {e}") 