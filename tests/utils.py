import os
from pathlib import Path


def get_base_path() -> Path:
    return Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
