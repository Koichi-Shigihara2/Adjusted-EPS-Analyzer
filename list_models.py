import os
from google import genai

# APIキーを読み込む
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("--- 利用可能なモデル一覧を表示します ---")
try:
    for m in client.models.list():
        # 名前の中に 'flash' が入っているものだけを表示して見やすくします
        if "flash" in m.name:
            print(f"利用可能: {m.name}")
except Exception as e:
    print(f"エラーが発生しました: {e}")