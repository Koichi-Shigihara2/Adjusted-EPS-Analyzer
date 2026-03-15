"""
ai_analyzer.py
AI分析モジュール（Grok API利用）
- 調整項目リストを分析し、健全性・コメント・引用ソースを返す
- 調整項目がない場合は早期に「調整なし」レスポンスを返す
- 戻り値はJSON文字列（pipeline.py が json.loads する想定）
"""
import json
import os
import requests
from typing import List, Dict, Any, Optional

# デフォルトプロンプトテンプレート
PROMPT_TEMPLATE = """
あなたは財務分析のエキスパートです。以下の調整項目リストを分析し、健全性とコメントを返してください。
ティッカー: {ticker}
期: {fiscal_period}
GAAP EPS: {gaap_eps}
Adjusted EPS: {adjusted_eps}
調整項目: {adjustments_json}

以下のJSON形式で返してください：
{{
  "health": "Excellent/Good/Caution/Warning/Error",
  "comment": "分析コメント（日本語）",
  "sources": [
    {{"item": "項目名", "snippet": "引用テキスト"}}
  ]
}}
"""

# 環境変数からAPIキーを取得
GROK_API_KEY = os.environ.get("GROK_API_KEY")
GROK_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROK_MODEL = "llama3-70b-8192"  # または "mixtral-8x7b-32768"

def analyze_adjustments(ticker: str, fiscal_period_data: Dict[str, Any], adjustments: List[Dict[str, Any]]) -> str:
    """
    調整項目を分析し、JSON文字列を返す
    Args:
        ticker: 銘柄ティッカー
        fiscal_period_data: 当該期のデータ（filing_date, gaap_eps, adjusted_eps などを含む）
        adjustments: 税効果適用後の調整項目リスト（各項目に item_name, amount, net_amount, category 等を含む）
    Returns:
        str: JSON文字列。例：
        {
            "health": "Good",
            "comment": "コメント",
            "sources": [...]
        }
    """
    # --- ガード節：調整項目なし ---
    if not adjustments:
        return json.dumps({
            "health": "Good",
            "comment": "調整項目はありません。GAAP EPSがそのまま実質EPSと見なせます。",
            "sources": []
        }, ensure_ascii=False)

    # APIキーチェック
    if not GROK_API_KEY:
        return json.dumps({
            "health": "Caution",
            "comment": "AI分析にはGROK_API_KEY環境変数が必要です。",
            "sources": []
        }, ensure_ascii=False)

    # プロンプト作成
    fiscal_period = fiscal_period_data.get('filing_date', 'unknown')
    gaap_eps = fiscal_period_data.get('gaap_eps', 0)
    adjusted_eps = fiscal_period_data.get('adjusted_eps', 0)

    prompt = PROMPT_TEMPLATE.format(
        ticker=ticker,
        fiscal_period=fiscal_period,
        gaap_eps=gaap_eps,
        adjusted_eps=adjusted_eps,
        adjustments_json=json.dumps(adjustments, ensure_ascii=False, indent=2)
    )

    # APIリクエスト
    try:
        response = requests.post(
            GROK_API_URL,
            headers={
                "Authorization": f"Bearer {GROK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        content = result['choices'][0]['message']['content']
        # レスポンスがJSON文字列であることを確認（念のためパースして戻す）
        parsed = json.loads(content)
        return json.dumps(parsed, ensure_ascii=False)
    except Exception as e:
        # エラーレスポンス
        error_msg = str(e)
        return json.dumps({
            "health": "Error",
            "comment": f"AI分析中にエラーが発生しました: {error_msg}",
            "sources": []
        }, ensure_ascii=False)

# テスト用
if __name__ == "__main__":
    # ダミーデータ
    sample_ticker = "PLTR"
    sample_period = {
        "filing_date": "2025-03-31",
        "gaap_eps": 0.0838,
        "adjusted_eps": 0.1319
    }
    sample_adjustments = [
        {
            "item_name": "株式報酬費用",
            "amount": 155339000,
            "net_amount": 122717810,
            "category": "株式報酬 (SBC)",
            "reason": "非現金費用",
            "extracted_from": "us-gaap:ShareBasedCompensation"
        }
    ]
    result = analyze_adjustments(sample_ticker, sample_period, sample_adjustments)
    print(result)
    # 空調整のテスト
    empty_result = analyze_adjustments(sample_ticker, sample_period, [])
    print(empty_result)
