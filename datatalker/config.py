import os
from pathlib import Path

CHROMADB_DIR = os.environ.get(
    "CHROMADB_DIR",
    (Path(__file__).parents[1] / ".vectorstore").as_posix() # default
)