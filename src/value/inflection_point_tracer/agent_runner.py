import os
import sys
import json
import requests
import time
from datetime import datetime
from google import genai

# ==========================================
# 1. 銘柄設定 (CIKマップ)
# ==========================================
TARGET_STOCKS = {
    "SOUN": "0001840856",
    "PLTR": "0001321655",
    "SOFI": "0001818874",
    "TSLA": "0001318605"
  
}

def send_discord_notification(message: str):
    webhook_url = "https://discord.com/api/webhooks/1488561257513488446/-OSF4wPkwd_Mf674Ln7NKsTgukuLXtVcO7hxADLy_sTKra3Dim9UjRv6Z1blyfkelwiF"
    payload = {"content": message}
    try:
        requests.post(webhook_url, json=payload, timeout=10)
    except: pass

# パス設定とモジュール読み込み
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
from sec_extractor import download_and_clean_html, fetch_latest_filing

def run_full_agent(ticker: str, cik: str, filing_type: str = "10-Q"):
    print(f"\n=== 🤖 {ticker} ({filing_type}) の分析を開始 ===")
    
    filing_info = fetch_latest_filing(ticker, cik, filing_type)
    if not filing_info: 
        print(f"⚠️ {ticker} の書類が見つかりませんでした。")
        return

    document_text = download_and_clean_html(filing_info["url"])
    if not document_text: return

    print(f"Geminiで解析中... (大容量ドキュメントのため時間がかかる場合があります)")
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # 🎯 単位ミスとCFO抽出を徹底強化したプロンプト
    prompt = f"""
    提出された{filing_type}から数値を抽出し、JSONで返してください。
    
    【重要：CFOの探し方】
    "Net cash provided by operating activities" または "Net cash provided by (used in) operating activities" 
    という項目を「CONSOLIDATED STATEMENTS OF CASH FLOWS」セクションから探してください。
    
    【ルール】
    1. 数値は「1ドル単位」に換算（In thousandsなら1000倍）。
    2. 10-Qの場合、必ず「Three Months Ended（最新3ヶ月間）」の数値を使用すること。
    
    【厳格ルール：CFOのマイナス値（赤字）の取り扱い】
    1. "Net cash provided by (used in) operating activities" を探してください。
    2. 決算書上で括弧書き `(123,456)` になっている数値、または "used in" と記載されている数値は、必ず「マイナスの数値（例: -123456000）」として出力してください。
    3. 絶対に `0` や `null` に丸めないでください。マイナスであることを正確に把握することがこの分析の命です。


    {{
      "metrics": {{
        "revenue": {{"current": 0, "prior": 0}},
        "cfo": {{"current": 0, "prior": 0}}
      }},
      "selected_cluster": "High-Margin AI/Enterprise",
      "inflection_point_comment": "分析コメント"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=[document_text, prompt],
            config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        m = data.get("metrics", {})
        
        history_path = os.path.join(base_dir, "analysis_history.json")
        new_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ticker": ticker,
            "filing_type": filing_type,
            "metrics": m,
            "predicted_lag_q": 4, 
            "cluster_name": data.get("selected_cluster", "Unknown"),
            "comment": data.get("inflection_point_comment", "")
        }
        
        history_data = []
        if os.path.exists(history_path):
            with open(history_path, "r", encoding="utf-8") as f:
                try: history_data = json.load(f)
                except: pass
        
        history_data.append(new_record)
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=4, ensure_ascii=False)

        print(f"🎉 {ticker} 分析完了・保存しました。")
        send_discord_notification(f"【Spidey Bot】{ticker} ({filing_type}) 分析完了。")
        
    except Exception as e:
        print(f"❌ {ticker} 解析エラー: {e}")

if __name__ == "__main__":
    for i, (ticker, cik) in enumerate(TARGET_STOCKS.items()):
        if i > 0:
            print(f"\n⏳ API制限回避のため60秒待機します...")
            time.sleep(60)
        run_full_agent(ticker, cik, "10-Q")