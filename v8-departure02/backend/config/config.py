from pathlib import Path
from dotenv import load_dotenv
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
env = os.getenv("ENV", "development")
load_dotenv(PROJECT_ROOT / f"backend/.env.{env}")
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))
GRAPHS_DIR = DATA_DIR / "maps"
SOLUTIONS_DIR = DATA_DIR / "solutions"
FRONTEND_URL = os.getenv("FRONTEND_URL")