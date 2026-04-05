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
    print(f"🎬 {ticker} の分析エージェントを開始します。")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY が設定されていません。")
        return
        
    client = genai.Client(api_key=api_key)
    
    # 1. 最新の書類メタデータをSECから取得
    filing_info = fetch_latest_filing(ticker, cik, filing_type)
    if not filing_info:
        print(f"❌ {ticker} の {filing_type} が見つかりませんでした。")
        return
        
    print(f"📄 最新書類を発見: {filing_info['filing_date']}")
    
    # 2. HTMLのダウンロードとテキスト化
    document_text = download_and_clean_html(filing_info["url"])
    if not document_text:
        print("❌ テキストの抽出に失敗しました。")
        return
        
    print(f"🚀 Geminiにデータを送信中... (文字数: {len(document_text)})")
    
    # ==========================================
    # 改善されたプロンプト (類推・逆算の許可とラベリング)
    # ==========================================
    prompt = """
    あなたは米国のプロの機関投資家専属のデータアナリストです。
    提出された決算書（10-Kまたは10-Q）を厳密に分析し、指定されたフォーマットのJSONのみを返してください。

    【最重要ルール：データの欠落（null）と類推（CALCULATED）の扱い】
    SEC書類（特に四半期報告書10-Q）では、キャッシュフロー計算書（CFO等）が「年初からの累計（Year-to-Date）」でしか記載されていないケースが多々あります。
    投資家は「当期単独（3ヶ月間）の数値」を必要としています。

    1. 書類内に「当期単独（3ヶ月間）」の数値が明記されている場合は、それを抽出し status を "CONFIRMED" としてください。
    2. 単独の数値が明記されておらず、年初からの累計額しか載っていない場合：
       - 書類内の文脈、あるいは注記（Notes）等から、当期単独の数値を「逆算（例：Q3累計からQ2累計を引く）」または「合理的に類推」できる場合は、その計算結果を数値として格納し、status を "CALCULATED" としてください。
       - その際、必ず「derivation_logic」に、どのような計算や類似科目の参照を行ってその数値を導き出したのか、日本語でプロセスを厳密に記録してください。
    3. どうしても数値が見当たらず、類推も不可能な場合のみ数値を null とし、status を "NULL" としてください。

    【返却するJSONフォーマット】
    ```json
    {
      "selected_cluster": "企業のビジネスモデルに応じたクラスター名（例: High-Margin AI/Enterprise など）",
      "inflection_point_comment": "業績の反転や変化の兆候、抽出の過程で気づいたことに関する日本語のコメント",
      "metrics": {
        "revenue": {
          "current": 当期の数値(数値、不明ならnull),
          "prior": 前年同期の数値(数値、不明ならnull),
          "status": "CONFIRMED" | "CALCULATED" | "NULL",
          "derivation_logic": "抽出または計算のロジック（CONFIRMEDの場合は空文字で可）"
        },
        "cfo": {
          "current": 当期の数値(数値、不明ならnull),
          "prior": 前年同期の数値(数値、不明ならnull),
          "status": "CONFIRMED" | "CALCULATED" | "NULL",
          "derivation_logic": "抽出または計算のロジック（CONFIRMEDの場合は空文字で可）"
        }
      }
    }
    ```
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
            "filing_date": filing_info["filing_date"],
            "metrics": m,
            "predicted_lag_q": 4, 
            "cluster_name": data.get("selected_cluster", "Unknown"),
            "comment": data.get("inflection_point_comment", "")
        }
        
        history_data = []
        if os.path.exists(history_path):
            with open(history_path, "r", encoding="utf-8") as f:
                try: 
                    history_data = json.load(f)
                except: 
                    pass
        
        history_data.append(new_record)
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=4, ensure_ascii=False)

        print(f"🎉 {ticker} 分析完了・保存しました。")
        send_discord_notification(f"【Spidey Bot】{ticker} ({filing_type}) 分析完了。")
        
    except Exception as e:
        print(f"❌ 処理中にエラーが発生しました: {e}")

if __name__ == "__main__":
    # テスト実行
    for ticker, cik in TARGET_STOCKS.items():
        run_full_agent(ticker, cik, "10-Q")
        time.sleep(1)