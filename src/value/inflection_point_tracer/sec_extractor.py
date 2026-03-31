import csv
import os
import re
import time
import requests
from bs4 import BeautifulSoup


def fetch_latest_filing(ticker: str, cik: str, filing_type: str = "10-K"):
    """【完成版】指定企業の最新書類メタデータを取得する"""
    gmail_user = os.getenv("GMAIL_USER")
    if not gmail_user:
        gmail_user = "your-email@example.com"

    headers = {"User-Agent": f"InvestmentAnalysisBot/1.0 ({gmail_user})"}

    cik_padded = cik.zfill(10)
    url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"

    try:
        response = requests.get(url, headers=headers)
        time.sleep(0.15)  # レートリミット安全弁

        if response.status_code != 200:
            print(f"[{ticker}] 取得失敗 (Status: {response.status_code})")
            return None

        data = response.json()
        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])

        for i, form in enumerate(forms):
            if form == filing_type:
                accession_number = filings["accessionNumber"][i].replace(
                    "-", ""
                )
                primary_doc = filings["primaryDocument"][i]
                report_date = filings["reportDate"][i]
                filing_date = filings["filingDate"][i]

                filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_number}/{primary_doc}"

                return {
                    "ticker": ticker,
                    "filing_type": filing_type,
                    "report_date": report_date,
                    "filing_date": filing_date,
                    "url": filing_url,
                }
        return None

    except Exception as e:
        print(f"[{ticker}] 例外発生: {e}")
        return None


def download_and_clean_html(url: str):
    """【完成版】URLからHTMLを取得し、プレーンテキストに変換する"""
    gmail_user = os.getenv("GMAIL_USER")
    if not gmail_user:
        gmail_user = "your-email@example.com"

    headers = {"User-Agent": f"InvestmentAnalysisBot/1.0 ({gmail_user})"}

    try:
        response = requests.get(url, headers=headers)
        time.sleep(0.15)

        if response.status_code != 200:
            return None

        html_content = response.text
        soup = BeautifulSoup(html_content, "html.parser")

        for element in soup(["script", "style", "noscript", "header", "footer"]):
            element.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        clean_text = "\n".join([line for line in lines if line])

        return clean_text

    except Exception as e:
        print(f"解析中に例外発生: {e}")
        return None


def save_extracted_text(ticker: str, filing_type: str, date: str, text: str):
    """【新規追加】抽出したテキストをdataフォルダに保存する"""
    # 実行場所から見て3つ上のプロジェクトルートにあるdataフォルダを指す
    base_dir = "../../../data"
    output_dir = os.path.join(base_dir, "extracted_filings", ticker)

    # フォルダがなければ作成
    os.makedirs(output_dir, exist_ok=True)

    # ファイル名: PLTR_10-K_2026-02-17.txt
    file_name = f"{ticker}_{filing_type}_{date}.txt"
    file_path = os.path.join(output_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"  -> 保存完了: {file_path}")
    return file_path


def run_process_for_type(filing_type: str):
    """指定された書類タイプでCSV全社を巡回する"""
    print(f"\n=== {filing_type} の一括取得・解析処理を開始します ===")
    csv_path = "../../../config/cik_lookup.csv"

    if not os.path.exists(csv_path):
        print(f"エラー: {csv_path} が見つかりません。")
        return

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            ticker = row["ticker"]
            cik = row["cik"]

            if ticker == "FIG" and cik == "0001716310":
                cik = "0001579878"

            print(f"Checking {ticker} for {filing_type}...")
            result = fetch_latest_filing(ticker, cik, filing_type)

            if result:
                print(
                    f"  -> 最新書類を発見! 提出日: {result['filing_date']}"
                )

                # HTMLをダウンロードしてテキスト化
                clean_text = download_and_clean_html(result["url"])

                if clean_text:
                    # データを保存
                    save_extracted_text(
                        ticker,
                        filing_type,
                        result["filing_date"],
                        clean_text,
                    )
                else:
                    print(f"  -> テキストの抽出に失敗しました。")
            else:
                print(f"  -> {filing_type} が見つかりませんでした。")

            time.sleep(1)


# --- 実戦用のエントリーポイント ---
if __name__ == "__main__":
    # 1. まずは 10-K を全社分集める
    run_process_for_type("10-K")

    # 2. 続いて 10-Q を全社分集める
    run_process_for_type("10-Q")

    print("\n🎉 全ての処理が完了しました！")