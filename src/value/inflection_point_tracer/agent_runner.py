import os
import sys
import json
import requests
from datetime import datetime
from google import genai  # ✅ 最新のSDKを使用

# ==========================================
# 1. Discord通知機能
# ==========================================
def send_discord_notification(message: str):
    webhook_url = "https://discord.com/api/webhooks/1488561257513488446/-OSF4wPkwd_Mf674Ln7NKsTgukuLXtVcO7hxADLy_sTKra3Dim9UjRv6Z1blyfkelwiF"
    payload = {"content": message}
    try:
        response = requests.post(webhook_url, json=payload)
        return response.status_code in [200, 204]
    except:
        return False

# ==========================================
# 2. パス設定とモジュール読み込み
# ==========================================
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
try:
    from sec_extractor import download_and_clean_html, fetch_latest_filing
except ImportError:
    print("❌ sec_extractor.py が見つかりません。")
    sys.exit(1)

# ==========================================
# 3. 判定・計算ロジック
# ==========================================
LAG_DATABASE = {
    "High-Margin AI/Enterprise": {"lag_to_profit_q": 4},
    "Hardware/Software Hybrid": {"lag_to_profit_q": 6},
    "Fintech/Platform": {"lag_to_profit_q": 3}
}

def evaluate_signals(m):
    signals = []
    rev_c, rev_p = m['revenue']['current'] or 0, m['revenue']['prior'] or 0
    if rev_p > 0 and ((rev_c - rev_p) / rev_p) * 100 >= 20.0:
        signals.append(f"✅ 売上急成長")
    return signals

# ==========================================
# 4. 統合エージェント本体
# ==========================================
def run_full_agent(ticker: str, filing_type: str = "10-K"):
    print(f"\n=== 🤖 {ticker} の分析を開始します ===")

    # SECからデータ取得
    cik = "0001321655" 
    filing_info = fetch_latest_filing(ticker, cik, filing_type)
    if not filing_info: return

    document_text = download_and_clean_html(filing_info["url"])
    if not document_text: return

    # Gemini 分析 (最新 SDK 方式)
    print("3. Geminiで分析中...")
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = f"提出された{filing_type}から数値を抽出しJSONで返してください。metrics, selected_cluster, inflection_point_commentを含めてください。"

    try:
        # ✅ 修正：一覧で確認できた「gemini-2.5-flash」を指定
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=[document_text, prompt],
            config={"response_mime_type": "application/json"}
        )
        data = json.loads(response.text)
        m = data["metrics"]
        
    except Exception as e:
        print(f"❌ 解析エラー: {e}")
        return

    # 計算と保存
    signals = evaluate_signals(m)
    cluster_name = data.get("selected_cluster", "High-Margin AI/Enterprise")
    lag_q = LAG_DATABASE.get(cluster_name, {"lag_to_profit_q": 4})["lag_to_profit_q"]

    # 履歴の蓄積
    history_path = os.path.join(base_dir, "analysis_history.json")
    new_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker,
        "metrics": m,
        "predicted_lag_q": lag_q,
        "cluster_name": cluster_name
    }
    
    history_data = []
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            try: history_data = json.load(f)
            except: pass
    
    history_data.append(new_record)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=4, ensure_ascii=False)

    print(f"🎉 履歴を保存しました (累計: {len(history_data)}件)")
    send_discord_notification(f"【Spidey Bot】{ticker} 分析完了。予測ラグ: {lag_q}Q")

if __name__ == "__main__":
    run_full_agent("PLTR", "10-K")