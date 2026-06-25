import sys
from pathlib import Path

# Add src/ to sys.path so tests can import config and alpata_localizer
# without installing them as a package.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
