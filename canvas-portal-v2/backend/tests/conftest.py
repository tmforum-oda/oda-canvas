import sys
from pathlib import Path

# Make the backend modules (auth, config, ...) importable as top-level packages.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
