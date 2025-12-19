#!/bin/bash
# Run all FSB examples
# Can be run from project root: ./examples/run_examples.sh

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== FSB Examples ==="
echo

for example in 01_create_bundle.py 02_figure_with_children.py 03_validate_bundle.py 04_data_and_stats.py; do
    echo "--- Running $example ---"
    python "$SCRIPT_DIR/$example"
    echo
done

echo "=== All examples completed ==="
