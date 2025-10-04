#!/usr/bin/env python3
import sys
import os

# Get the directory where run_adam.py is located (project root)
project_root = os.path.dirname(os.path.abspath(__file__))

# Add 'src' to Python path so 'from adam.core import main' works
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import and run main from src/adam/core.py
from adam.core import main

if __name__ == "__main__":
    main()
