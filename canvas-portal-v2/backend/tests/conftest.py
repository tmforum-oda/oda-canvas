import sys
from pathlib import Path

# Make the backend packages (k8s, auth, config, ...) importable as top-level modules,
# the same way they are when the app runs from /app.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
