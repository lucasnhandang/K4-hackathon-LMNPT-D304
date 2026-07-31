from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .registry import build_default_registry


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run one student-assistant tool.")
    parser.add_argument("tool", nargs="?", help="Tool name. Omit to list definitions.")
    parser.add_argument(
        "--arguments",
        default="{}",
        help='JSON object, for example: \'{"query":"deadline RAG"}\'',
    )
    parser.add_argument(
        "--arguments-file",
        help="Read arguments from a UTF-8 JSON file (recommended on Windows).",
    )
    args = parser.parse_args()

    registry = build_default_registry()
    if not args.tool:
        print(json.dumps(registry.definitions(), ensure_ascii=False, indent=2))
        return

    raw_arguments = (
        Path(args.arguments_file).read_text(encoding="utf-8")
        if args.arguments_file
        else args.arguments
    )
    arguments = json.loads(raw_arguments)
    if not isinstance(arguments, dict):
        parser.error("--arguments must be a JSON object")
    result = registry.execute(args.tool, arguments)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
