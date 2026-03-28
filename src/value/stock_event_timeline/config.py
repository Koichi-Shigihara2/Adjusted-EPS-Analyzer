import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
env_path = BASE_DIR / ".env"

# BOM対応のため utf-8-sig で読み込む
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    # 読み込んだ内容を一時ファイルに書き出して load_dotenv に渡す
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    load_dotenv(dotenv_path=tmp_path)
    os.unlink(tmp_path)
else:
    load_dotenv(dotenv_path=env_path)

XAI_API_KEY = os.getenv("XAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4.20-0309-reasoning")

print("XAI_API_KEY loaded:", XAI_API_KEY[:10] + "..." if XAI_API_KEY else "None")
