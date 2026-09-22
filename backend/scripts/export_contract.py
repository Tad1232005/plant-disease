"""Export/verify the exact OpenAPI snapshot delivered to frontend."""
import argparse
import json
from pathlib import Path
from app.main import app
from app.core.config import BASE_DIR

DEFAULT_OUTPUT = BASE_DIR / "docs" / "week7" / "openapi.json"


def contract_text() -> str:
    return json.dumps(app.openapi(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Read-only comparison with committed contract")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    generated = contract_text()
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != generated:
            raise SystemExit("OpenAPI differs: review the change, regenerate contract and notify frontend.")
        print("OpenAPI contract matches application")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(generated, encoding="utf-8")
        print(f"Exported {args.output}")


if __name__ == "__main__":
    main()
