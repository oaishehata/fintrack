import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ML_SERVICE = ROOT / "ml_service"

for path in (ROOT, ML_SERVICE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
