import os
import time
from google import genai


def analyze_filing_with_gemini(file_path: str):
    """【今回の塊】保存されたテキストをGeminiに読ませて分析する"""
    # 以前の画像にあった環境変数 GEMINI_API_KEY を使用します
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("⚠️ GEMINI_API_KEY が環境変数に設定されていません。")
        # テスト用に直接キーを入れる場合は、下のクォートの中に貼り付けてください
        # api_key = "AIzaSy..."
        return None

    if not os.path.exists(file_path):
        print(f"❌ ファイルが見つかりません: {file_path}")
        return None

    print(f"📄 ファイルを読み込み中: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        document_text = f.read()

    print(f"🚀 Geminiにデータを送信中... (文字数: {len(document_text)})")

    try:
        # 最新の Google GenAI SDK の記法
        client = genai.Client(api_key=api_key)

        # 56万文字の巨大なテキストを扱うため、賢くコンテキストの広い 1.5 Pro を使用
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                document_text,
                "\n\n上記の10-K（決算書）を分析し、以下の3点について日本語で簡潔にまとめてください。\n"
                "1. この企業のビジネスにおける最大の強み\n"
                "2. 前年と比較して、業績や契約、戦略において「大きな変化（変曲点）」が起きている部分\n"
                "3. 今後の成長を阻害する可能性がある最大のリスク",
            ],
        )

        return response.text

    except Exception as e:
        print(f"❌ Gemini API 呼び出し中に例外発生: {e}")
        return None


if __name__ == "__main__":
    print("=== Gemini 解析テストを開始します ===")

    # 先ほど 10-K の取得で保存されたはずの Palantir のファイルを指定
    # パスがズレないよう、実行場所から見た相対パスで指定します
    target_file = "../../../data/extracted_filings/PLTR/PLTR_10-K_2026-02-17.txt"

    start_time = time.time()
    analysis_result = analyze_filing_with_gemini(target_file)
    end_time = time.time()

    if analysis_result:
        print("\n" + "=" * 40)
        print("🎉 Gemini による解析が完了しました！")
        print(f"（所要時間: {end_time - start_time:.1f} 秒）")
        print("=" * 40)
        print("\n【分析結果】")
        print(analysis_result)
    else:
        print("\n❌ 解析に失敗しました。")