from openai import OpenAI
import os

def analyze_adjustments(ticker, data, adjustments):
    client = OpenAI(
        api_key=os.environ.get("XAI_API_KEY"),
        base_url="https://api.x.ai/v1",
    )

    # 調整内訳を文字列化（snippet付きで）
    adj_text = []
    for adj in adjustments:
        snippet = adj.get("context_snippet", "N/A")
        adj_text.append(f"- {adj['item_name']}: {adj['net_amount']:,} USD (理由: {adj['reason']}) Snippet: {snippet}")

    prompt = f"""
あなたは米国株のNon-GAAP調整専門のシニアアナリストです。
銘柄: {ticker}
GAAP純利益: {data['gaap_net_income']:,} USD
調整後純利益: {data['adjusted_net_income']:,} USD
調整項目詳細:
{'\n'.join(adj_text)}

以下の4段階で健全性を評価してください：
- Excellent: 調整が極めて合理的で本質的成長を示唆
- Good: 標準的な調整、問題なし
- Caution: 一部調整が恣意的or連続発生
- Warning: 調整が利益水増しに見える、または連続Caution

評価理由を日本語で150-250文字。**各調整項目に引用した原文snippetを必ず明記**。
連続Cautionが複数四半期なら強調。
出力はJSON形式で:
{{
  "health": "Excellent|Good|Caution|Warning",
  "comment": "詳細解説...",
  "sources": [{{"item": "リストラ費用", "snippet": "..."}}, ...]
}}
"""

    response = client.chat.completions.create(
        model="grok-beta",  # または grok-4-0709 など最新モデル（APIで確認）
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=800
    )

    try:
        return response.choices[0].message.content.strip()  # JSON文字列として返す
    except:
        return '{"health": "Error", "comment": "AI解析失敗"}'
