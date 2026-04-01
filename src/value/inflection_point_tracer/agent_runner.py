import os
import sys
import json
import requests
from google import genai

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
# 2. SECデータ取得機能
# ==========================================
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from sec_extractor import download_and_clean_html, fetch_latest_filing
except ImportError:
    print("❌ sec_extractor.py が見つかりません。")
    sys.exit(1)

# ==========================================
# 3. 過去イベント＆ラグのデータベース
# ==========================================
LAG_DATABASE = {
    "High-Margin AI/Enterprise": {
        "example_ticker": "PLTR",
        "lag_to_profit_q": 4,
        "description": "高粗利なソフトウェア・AI型。シグナル点灯後、約1年（4Q）で本格黒字化の傾向。"
    },
    "Hardware/Software Hybrid": {
        "example_ticker": "TSLA",
        "lag_to_profit_q": 6,
        "description": "莫大な設備投資が必要な製造業ハイブリッド。黒字化までのラグは長めの傾向（6Q）。"
    },
    "Fintech/Platform": {
        "example_ticker": "SOFI",
        "lag_to_profit_q": 3,
        "description": "顧客獲得コストが下がると一気に利益が出る。比較的ラグは短い（3Q）。"
    }
}

# ==========================================
# 4. 変曲点シグナル判定ロジック (Step 2)
# ==========================================
def evaluate_signals(m):
    signals = []
    rev_c = m['revenue']['current'] or 0
    rev_p = m['revenue']['prior'] or 0
    if rev_p > 0:
        rev_growth = ((rev_c - rev_p) / rev_p) * 100
        if rev_growth >= 20.0:
            signals.append(f"✅ 売上急成長: 前期比 +{rev_growth:.1f}% (基準: >20%)")

    cfo_c = m['cfo']['current'] or 0
    cfo_p = m['cfo']['prior'] or 0
    if rev_c > 0 and rev_p > 0:
        cfo_margin_c = (cfo_c / rev_c) * 100
        cfo_margin_p = (cfo_p / rev_p) * 100
        margin_diff = cfo_margin_c - cfo_margin_p
        if margin_diff >= 5.0:
            signals.append(f"✅ CFOマージン急改善: {cfo_margin_p:.1f}% ➔ {cfo_margin_c:.1f}% (+{margin_diff:.1f}pt改善)")
            
    opex_c = m['opex']['current'] or 0
    opex_p = m['opex']['prior'] or 0
    if rev_p > 0 and opex_p > 0:
        opex_growth = ((opex_c - opex_p) / opex_p) * 100
        if rev_growth > opex_growth:
            signals.append(f"✅ 営業レバレッジ効力: 売上成長(+{rev_growth:.1f}%) > 販管費増加(+{opex_growth:.1f}%)")

    return signals

# ==========================================
# 5. Burn Rate（余命）算出ロジック (Step 3)
# ==========================================
def calculate_burn_rate(m):
    cash = m['cash']['current'] or 0
    cfo = m['cfo']['current'] or 0
    fcf = m['fcf']['current'] or 0
    
    if fcf >= 0 and cfo >= 0:
        return ["💚 資金余力: 営業CF・FCFともに黒字です。滑走路は無限です。"]
        
    results = []
    if cfo < 0:
        monthly_ope_burn = abs(cfo) / 12
        ope_runway = cash / monthly_ope_burn if monthly_ope_burn > 0 else 0
        results.append(f"🔴 Operating Burn（健全性）: あと {ope_runway:.1f} ヶ月 で現預金が底をつきます。")
        
    return results

# ==========================================
# 6. 統合エージェント本体
# ==========================================
def run_full_agent(ticker: str, filing_type: str = "10-K"):
    print(f"\n=== 🤖 {ticker} の第2期：パイプライン統合を開始します ===")

    # 1. SECから探索
    cik = "0001321655" 
    print(f"1. SECから {ticker} の {filing_type} を探索中...")
    filing_info = fetch_latest_filing(ticker, cik, filing_type)
    if not filing_info: return

    # 2. テキスト抽出
    print("2. テキストを抽出中...")
    document_text = download_and_clean_html(filing_info["url"])
    if not document_text: return

    # 3. Gemini による構造化分析 ＆ 動的類似度判定
    print("3. Geminiで数値抽出とクラスタリング判定中...")
    api_key = os.getenv("GEMINI_API_KEY")
    
    prompt = f"""
    提出された{filing_type}から、以下の財務数値を抽出し、指定のJSON形式で出力してください。
    数値は「百万ドル(Millions of USD)」単位で数値のみを抽出してください。不明な場合は null にしてください。
    
    さらに、この会社のビジネスモデルや財務構造を分析し、以下の3つのクラスタのうち「どれに最も近いか」を1つだけ選んでください。
    1. "High-Margin AI/Enterprise" (高粗利なソフトウェア・AI型。例: PLTR)
    2. "Hardware/Software Hybrid" (設備投資が必要な製造業ハイブリッド。例: TSLA)
    3. "Fintech/Platform" (金融・プラットフォーム型。例: SOFI)

    【出力形式】
    {{
      "metrics": {{
        "revenue": {{"current": 0, "prior": 0}},
        "cfo": {{"current": 0, "prior": 0}},
        "fcf": {{"current": 0, "prior": 0}},
        "opex": {{"current": 0, "prior": 0}},
        "cogs": {{"current": 0, "prior": 0}},
        "capex": {{"current": 0, "prior": 0}},
        "cash": {{"current": 0, "prior": 0}}
      }},
      "selected_cluster": "上記3つのうち選んだクラスタ名をそのまま記述",
      "cluster_reason": "なぜそのクラスタに近いと判断したかの短い理由（日本語）",
      "inflection_point_comment": "数値から見える変曲点についての短い分析（日本語）"
    }}
    """

    try:
        client = genai.Client(api_key=api_key)
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

    # 4. 各種計算ロジックの実行
    print("4. 各種判定ロジックを計算中...")
    signals = evaluate_signals(m)
    burn_rates = calculate_burn_rate(m)

    # 5. 動的類似度からラグを算出
    print("5. 動的類似度からラグを算出中...")
    cluster_name = data.get("selected_cluster", "High-Margin AI/Enterprise")
    lag_q = 0
    if cluster_name in LAG_DATABASE:
        lag_q = LAG_DATABASE[cluster_name]["lag_to_profit_q"]

    # ==========================================
    # 🔥 【Step 6 新機能】Pipeline統合（JSON保存）
    # ==========================================
    print("6. グラフ化に向けたJSONファイルを保存中...")
    
    output_data = {
        "ticker": ticker,
        "filing_date": filing_info["filing_date"],
        "metrics": m,
        "signals": signals,
        "burn_rates": burn_rates,
        "predicted_lag_q": lag_q,
        "cluster_name": cluster_name,
        "ai_analysis": data.get("inflection_point_comment", "")
    }
    
    # 成果物としてファイルに書き出す
    with open("analysis_result.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)

    # 7. Discordへの通知
    print("7. Discordへ結果を送信中...")
    table_msg = (
        f"📊 **{ticker} 財務数値 (単位:百万ドル)**\n"
        f"```\n"
        f"項目      | 最新期    | 前期\n"
        f"----------|-----------|-----------\n"
        f"売上高    | {m['revenue']['current']:>9} | {m['revenue']['prior']:>9}\n"
        f"営業CF    | {m['cfo']['current']:>9} | {m['cfo']['prior']:>9}\n"
        f"自由CF    | {m['fcf']['current']:>9} | {m['fcf']['prior']:>9}\n"
        f"現預金    | {m['cash']['current']:>9} | {m['cash']['prior']:>9}\n"
        f"```\n"
    )

    signal_text = "\n".join(signals) if signals else "⚠️ 明確なシグナル条件を満たしませんでした。"
    burn_text = "\n".join(burn_rates)

    discord_message = (
        f"【🤖 第2期完成：Pipeline統合エンジン】\n"
        f"📅 書類提出日: {filing_info['filing_date']}\n"
        f"{table_msg}"
        f"🎯 **【Step 2: 変曲点シグナル】**\n"
        f"{signal_text}\n\n"
        f"⏳ **【Step 3: Burn Rate（余命）】**\n"
        f"{burn_text}\n\n"
        f"📈 **【Step 5: ラグ予測】**\n"
        f"判定クラスタ: {cluster_name} (Xデーまで約 {lag_q} Q)\n\n"
        f"💡 **AI定性分析:**\n{data['inflection_point_comment']}\n\n"
        f"💾 *第3期（可視化）に向けたJSONファイルを保存しました。*"
    )

    if send_discord_notification(discord_message):
        print(f"\n🎉 データの保存とDiscordへの通知が完了しました！")

if __name__ == "__main__":
    run_full_agent("PLTR", "10-K")