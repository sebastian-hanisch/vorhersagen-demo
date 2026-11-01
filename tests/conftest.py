"""Gemeinsame Einrichtung: das Projektverzeichnis in den Importpfad."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
