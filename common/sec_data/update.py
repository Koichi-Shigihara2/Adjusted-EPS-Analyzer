"""
SEC データ一括更新スクリプト
GitHub Actions から実行される
使用方法:
    python common/sec_data/update.py              # 全ティッカー
    python common/sec_data/update.py TSLA PLTR    # 特定ティッカーのみ
"""
import sys
import os

# common/sec_data/ から実行される前提でパス設定
script_dir = os.path.dirname(os.path.abspath(__file__))
common_dir = os.path.dirname(script_dir)
repo_root = os.path.dirname(common_dir)
sys.path.insert(0, repo_root)

from common.sec_data.config import get_all
from common.sec_data.fetcher import SECFetcher, load_company_facts
from common.sec_data.parser import SECParser
from common.sec_data.quarterly import build_raw_table, save_raw_table, check_revenue_quality
from common.sec_data.normalizer import normalize, save_normalized
from common.sec_data.layer3_builder import build_ticker_store
from common.sec_data.ttm_calculator import calc_ttm_series, save_ttm_series
from common.sec_data.revenue_tag_conflict_check import check_revenue_tag_conflict, _format_conflict


def main():
    tickers = sys.argv[1:] if len(sys.argv) > 1 else get_all()

    # データ保存先をcommon/sec_data/data/に設定
    data_dir = os.path.join(script_dir, "data")
    fetcher = SECFetcher(data_dir=data_dir)
    parser = SECParser(data_dir=data_dir)

    print("=" * 60)
    print("SEC EDGAR データ更新")
    print(f"対象: {len(tickers)} 銘柄")
    print(f"保存先: {data_dir}")
    print("=" * 60)

    success = 0
    failed = []

    for ticker in tickers:
        print(f"\n--- {ticker} ---")

        # 1. company_facts 取得
        raw = fetcher.fetch_company_facts(ticker)
        if not raw:
            failed.append(ticker)
            continue

        # 1b. submissions取得（本人データ判定用のreportDate。取得失敗しても
        #     determine_fiscal_year()フォールバックで継続できるためnon-blocking）
        try:
            fetcher.fetch_submissions(ticker)
        except Exception as e:
            print(f"   [WARN] submissions取得エラー: {e} → フォールバック判定のみで継続")

        # 2. 従来パース＆保存（annual等）
        parsed = parser.parse_and_save(ticker)
        if parsed:
            annual_years = list(parsed.get("annual", {}).keys())[:3]
            print(f"   年次: {annual_years}")
        else:
            failed.append(ticker)
            continue

        # 3. 四半期Raw Table生成
        try:
            company_facts = load_company_facts(ticker, data_dir=data_dir)
            if company_facts is None:
                print(f"   [WARN] company_facts 読み込み失敗 → TTMスキップ")
                success += 1
                continue

            raw_table = build_raw_table(ticker, company_facts)
            save_raw_table(ticker, raw_table)
            print(f"   Raw Table: {len(raw_table.get('fields', {}))} fields")
        except Exception as e:
            print(f"   [WARN] Raw Table生成エラー: {e} → TTMスキップ")
            success += 1
            continue

        # 4. 正規化（YTD→Q差分変換）
        try:
            normalized = normalize(ticker, raw_table)
            save_normalized(ticker, normalized)
            print(f"   Normalized: OK")
        except Exception as e:
            print(f"   [WARN] Normalize エラー: {e} → TTMスキップ")
            success += 1
            continue

        # 4b. Revenue品質チェック
        try:
            rq = check_revenue_quality(ticker, normalized)
            status = rq["status"]
            yoy = f"{rq['latest_rev_yoy']:+.1f}%" if rq["latest_rev_yoy"] is not None else "N/A"
            if status == "ISSUE":
                print(f"   [Revenue ❌ ISSUE] yoy={yoy}")
                for iss in rq["issues"]:
                    print(f"     ❌ {iss}")
            elif status == "WARN":
                print(f"   [Revenue ⚠️  WARN] yoy={yoy}")
                for w in rq["warnings"]:
                    print(f"     ⚠️  {w}")
            else:
                print(f"   Revenue: OK  yoy={yoy}")
            # GitHub Actions Step Summary に書き込み
            summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
            if summary_path and status in ("ISSUE", "WARN"):
                with open(summary_path, "a", encoding="utf-8") as sf:
                    icon = "🔴" if status == "ISSUE" else "🟡"
                    sf.write(f"| {ticker} | {icon} {status} | {yoy} | "
                             f"{'; '.join(rq['issues'] + rq['warnings'])[:120]} |\n")
        except Exception as e:
            print(f"   [WARN] Revenue品質チェックエラー: {e}")

        # 4c. Revenue系タグ競合チェック（ARCH-DATA-1残課題③）
        # SEC-REV-FINTECH-1/BUG-REV-SPAC-1型の「複数候補タグが同一年度で
        # 大きく食い違う」ケースを検知する。自動修正は行わずWARN表示のみ。
        try:
            tc = check_revenue_tag_conflict(ticker, data_dir=data_dir)
            if tc["status"] == "WARN":
                print(f"   [TagConflict ⚠️  WARN] {len(tc['conflicts'])}件")
                for c in tc["conflicts"]:
                    print(f"    {_format_conflict(c)}")
        except Exception as e:
            print(f"   [WARN] タグ競合チェックエラー: {e}")

        # 5. TTMシリーズ生成（フェーズC対応: 入力元をnormalize()の戻り値
        #    からbuild_ticker_store()の戻り値〈Layer3、インメモリ〉に切替）
        try:
            store = build_ticker_store(ticker)
            if store is None:
                print(f"   [WARN] Layer3ストア構築失敗 → TTMスキップ")
            else:
                ttm_series = calc_ttm_series(ticker, store)
                save_ttm_series(ticker, ttm_series)
                n = len(ttm_series)
                fields_sample = list(ttm_series[0].get("flow", {}).keys()) if ttm_series else []
                print(f"   TTM: {n} periods → {fields_sample[:5]}...")
        except Exception as e:
            print(f"   [WARN] TTM計算エラー: {e}")

        success += 1

    # サマリー
    print("\n" + "=" * 60)
    print(f"完了: {success}/{len(tickers)}")
    if failed:
        print(f"失敗: {', '.join(failed)}")
    print("=" * 60)

    # GitHub Actions Step Summary にRevenue品質チェック結果のヘッダーを追記
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        # ヘッダーが未出力の場合のみ追記（先頭に書く）
        header = "\n## Revenue品質チェック（WARN/ISSUE銘柄のみ）\n\n| Ticker | Status | YoY | 内容 |\n|:---|:---|---:|:---|\n"
        try:
            with open(summary_path, "r", encoding="utf-8") as sf:
                existing = sf.read()
        except FileNotFoundError:
            existing = ""
        if "Revenue品質チェック" not in existing:
            with open(summary_path, "a", encoding="utf-8") as sf:
                sf.write(header)

    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
