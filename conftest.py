"""
conftest.py  (repo root)
------------------------
Ensure the python/ directory is on sys.path so tests can import
descriptive_qc without installing the package.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "python"))
