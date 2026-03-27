"""
pytest konfigürasyonu — proje kökünü Python path'ine ekler.
Bu sayede tests/ altındaki testler config, modules, app gibi
üst dizin modüllerini import edebilir.
"""

import sys
from pathlib import Path

# Proje kökü: bu dosyanın bulunduğu dizin
sys.path.insert(0, str(Path(__file__).parent))
