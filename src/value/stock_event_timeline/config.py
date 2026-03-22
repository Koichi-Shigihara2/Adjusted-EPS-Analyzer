import os
from pathlib import Path

# DB 繝代せ・医Μ繝昴ず繝医Μ逶ｴ荳・data/stocks.db・・
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "stocks.db"

# API Keys・・itHub Secrets 縺九ｉ豕ｨ蜈･・・
XAI_API_KEY = os.getenv("XAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# xAI 繧ｨ繝ｳ繝峨・繧､繝ｳ繝茨ｼ・penAI 莠呈鋤諠ｳ螳夲ｼ・
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4")
