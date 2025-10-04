#!/bin/bash
set -e  # Exit on any error

echo "🔍 Running Ruff (lint + format check)..."
ruff check src/ plugins/ tools/ scripts/ run_adam.py simulator_engine.py

echo "🔍 Running Pyflakes (extra safety)..."
find src plugins tools scripts -name "*.py" -exec pyflakes {} +

echo "✅ All checks passed!"
