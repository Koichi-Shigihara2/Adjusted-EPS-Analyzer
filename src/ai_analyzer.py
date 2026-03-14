import os
import google.generativeai as genai
from openai import OpenAI

def analyze_with_gemini_v3(ticker, data, adjustments):
    """最新の Gemini 3 Flash を使用した解析"""
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    # ドキュメントに基づき、推奨モデル 'gemini-3-flash' を指定
    model = genai.GenerativeModel('gemini-3-flash')
    
    prompt = f"""
    米国株財務分析官として、{ticker}の非GAAP調整を評価してください。
    【データ】
    GAAP利益: {data['net_income']} / 調整後利益: {data['adjusted_net_income']}
    調整項目: {adjustments}
    
    【出力要件】
    1. 健全性（Healthy/Caution/Warning/Critical）を判定。
    2. SBC（株式報酬）や買収関連費用の妥当性を日本語で200文字解説。
    """
    
    response = model.generate_content(prompt)
    return response.text

def analyze_with_xai(ticker, data, adjustments, press_snippet):
    """特に重要な判断が必要な場合、xAI (Grok) を使用"""
    client = OpenAI(
        api_key=os.environ.get("XAI_API_KEY"),
        base_url="https://api.x.ai/v1",
    )
    # ... (xAI用のプロンプト実装)
    
    prompt = f"""
    【投資分析ミッション】
    銘柄: {ticker}
    調整項目: {adjs}
    プレスリリース内容: {press_release}
    
    上記に基づき、この調整が「実態を表す前向きなもの」か「利益を飾る不健全なもの」か厳しく評価せよ。
    """
    # 課金キーのため、特に重要なフラグが立った時のみ呼び出すロジックにします
