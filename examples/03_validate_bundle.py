#!/usr/bin/env python3
"""
Example 03: Validate bundle against FSB schemas.

Demonstrates:
- Schema validation
- Error reporting
"""

from pathlib import Path

import fsb

OUT_DIR = Path(__file__).parent / f"{Path(__file__).stem}_out"
OUT_DIR.mkdir(exist_ok=True)


def main():
    # Create a bundle first
    bundle = fsb.Bundle(
        OUT_DIR / "validated",
        create=True,
        node_type="plot",
        name="Validated Plot",
    )
    bundle.save()

    # Validate the bundle
    print(f"Validating: {bundle.path}")
    print("-" * 50)

    results = bundle.validate(raise_on_error=False)

    for file_name, (is_valid, error) in results.items():
        if is_valid is None:
            status = "⚠️  MISSING"
        elif is_valid:
            status = "✓  VALID"
        else:
            status = f"✗  INVALID: {error}"
        print(f"  {file_name}: {status}")

    # Demonstrate schema loading
    print("\nAvailable schemas:")
    for name in fsb.SCHEMA_NAMES:
        schema = fsb.load_schema(name)
        print(f"  {name}: {schema.get('title', 'No title')}")


if __name__ == "__main__":
    main()
