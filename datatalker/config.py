import os
from pathlib import Path
from agents.extensions.models.litellm_model import LitellmModel

CHROMADB_DIR = os.environ.get(
    "CHROMADB_DIR",
    (Path(__file__).parents[1] / ".vectorstore").as_posix() # default
)


MODEL = LitellmModel("ollama/gemma3", "http://localhost:11434")