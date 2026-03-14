"""
ai_analyzer.py - Grok (xAI) による調整品質の AI 分析
config/prompts.yaml からプロンプトテンプレートを読み込み、
4 段階の健全性評価と日本語コメントを JSON で返す。
"""
import os
import json
import yaml
from openai import OpenAI

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROMPTS_PATH = os.path.join(_SCRIPT_DIR, "..", "config", "prompts.yaml")

# プロンプト設定キャッシュ
_prompts_cache = None


def _load_prompts():
    global _prompts_cache
    if _prompts_cache is None:
        try:
            with open(_PROMPTS_PATH, encoding="utf-8") as f:
                _prompts_cache = yaml.safe_load(f)
        except Exception:
            _prompts_cache = {}
    return _prompts_cache


def analyze_adjustments(ticker: str, data: dict, adjustments: list) -> str:
    """
    Parameters
    ----------
    ticker      : ティッカーシンボル
    data        : calculate_eps() の出力 dict
    adjustments : detailed_adjustments リスト

    Returns
    -------
    JSON 文字列:
    {
      "health": "Excellent|Good|Caution|Warning",
      "comment": "...",
      "sources": [{"item": "...", "snippet": "..."}, ...]
    }
    """
    prompts = _load_prompts()

    # モデル設定（prompts.yaml で上書き可能）
    model = prompts.get("model", "grok-3-mini")

    # 調整内訳テキスト（各項目のスニペット付き）
    adj_lines = []
    for adj in adjustments:
        snippet = adj.get("context_snippet") or "N/A"
        conf    = adj.get("ai_confidence",  "unknown")
        adj_lines.append(
            f"- [{adj.get('category','')}] {adj['item_name']}: "
            f"{adj.get('net_amount', 0):,.0f} USD "
            f"(税後, 方向: {adj.get('direction','')}, "
            f"理由: {adj.get('reason','')}, "
            f"信頼度: {conf}) "
            f"Snippet: {snippet}"
        )
    adj_text = "\n".join(adj_lines) if adj_lines else "調整項目なし"

    # カスタムプロンプト（prompts.yaml の analysis_prompt キーを使用）
    custom_instruction = prompts.get(
        "analysis_prompt",
        prompts.get("health_evaluation", "")
    )

    prompt = f"""あなたは米国株のNon-GAAP調整専門のシニアアナリストです。
以下のデータを分析し、調整品質を評価してください。

銘柄: {ticker}
期間: {data.get('period_of_report','N/A')} ({data.get('period_type','')})
GAAP純利益: {data.get('gaap_net_income', 0):,.0f} USD
調整後純利益: {data.get('adjusted_net_income', 0):,.0f} USD
GAAP EPS: {data.get('gaap_eps', 0):.4f}
調整後EPS: {data.get('adjusted_eps', 0):.4f}
希薄化後株式数(加重平均): {data.get('diluted_shares_used', 0):,.0f}

調整項目詳細:
{adj_text}

{custom_instruction}

以下の4段階で健全性を評価してください：
- Excellent: 調整が極めて合理的で本質的成長を示唆（非現金・一過性のみ）
- Good: 標準的な調整、問題なし
- Caution: 一部調整が恣意的または連続発生
- Warning: 調整が利益水増しに見える、または連続Cautionが複数四半期継続

評価理由を日本語で150〜250文字で記述。
各調整項目に対して引用した原文スニペットを必ず明記すること。
連続Cautionが複数四半期の場合は必ず強調すること。

出力は必ず以下のJSON形式のみで返す（コードブロック不要）:
{{
  "health": "Excellent|Good|Caution|Warning",
  "comment": "詳細解説（150-250文字）",
  "sources": [
    {{"item": "調整項目名", "snippet": "原文スニペット"}}
  ]
}}"""

    client = OpenAI(
        api_key=os.environ.get("XAI_API_KEY"),
        base_url="https://api.x.ai/v1",
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return json.dumps({
            "health": "Error",
            "comment": f"AI分析エラー: {str(e)[:200]}",
            "sources": []
        }, ensure_ascii=False)
