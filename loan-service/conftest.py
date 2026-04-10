# conftest.py – pytest-Konfiguration für loan-service
# Diese Datei sorgt dafür dass IntelliJ IDEA pytest korrekt erkennt
# und src/ als Importpfad verwendet.
import sys
from pathlib import Path

# src/ zum Python-Pfad hinzufügen damit 'loan.*' importierbar ist
sys.path.insert(0, str(Path(__file__).parent / "src"))

