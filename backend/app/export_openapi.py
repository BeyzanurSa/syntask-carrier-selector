"""Write the OpenAPI schema to a file so the frontend can generate types without a running server.

Usage: python -m app.export_openapi ../frontend/openapi.json
"""

import json
import sys

from app.main import create_app


def main() -> None:
    target = sys.argv[1] if len(sys.argv) > 1 else "openapi.json"
    with open(target, "w", encoding="utf-8") as f:
        json.dump(create_app().openapi(), f, indent=2, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
