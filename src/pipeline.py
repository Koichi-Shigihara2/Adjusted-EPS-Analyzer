"""
pipeline.py - メインパイプライン
SEC EDGAR からデータ取得 → 調整検知 → EPS 計算 → AI 分析 → JSON 保存
"""
import sys
import os
# src/ ディレクトリを Python パスに追加（GitHub Actions から呼び出された場合も動作）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
import json
from datetime import datetime

from extract_key_facts import extract_all_filings_for_ticker
from adjustment_detector import detect_adjustments
from tax_adjuster import apply_tax_adjustments
from eps_calculator import calculate_eps
from ai_analyzer import analyze_adjustments


# ─── ユーティリティ ───────────────────────────────────────────────

def load_config(path: str):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def ttm_calc(filings_list: list) -> dict | None:
    """
    直近4四半期分(10-Q×3 + 最新期から年次換算)の TTM EPS を計算。
    最新 10-K がある場合は FY を使用する簡易実装。
    """
    quarters = [f for f in filings_list if f.get("period_type") == "Q"]
    if len(quarters) < 4:
        return None
    quarters = sorted(quarters, key=lambda x: x.get("period_of_report", ""), reverse=True)[:4]

    ttm_net_income = sum(q.get("adjusted_net_income", 0) for q in quarters)
    ttm_gaap_ni    = sum(q.get("gaap_net_income", 0)    for q in quarters)

    # 希薄化後株式数は最新四半期を使用
    diluted_shares = quarters[0].get("diluted_shares_used", 0) or 1
    return {
        "period_type":          "TTM",
        "period_of_report":     quarters[0].get("period_of_report"),
        "gaap_net_income":      ttm_gaap_ni,
        "adjusted_net_income":  ttm_net_income,
        "adjusted_eps":         ttm_net_income / diluted_shares,
        "gaap_eps":             ttm_gaap_ni    / diluted_shares,
        "diluted_shares_used":  diluted_shares,
    }


def yoy_growth(current: float | None, previous: float | None) -> float | None:
    """前年同期比成長率(%)"""
    if not current or not previous or previous == 0:
        return None
    return round((current - previous) / abs(previous) * 100, 2)


def build_history_summary(filings_list: list) -> list:
    """
    全 filing の軽量サマリーリストを返す（UI テーブル・グラフ用）
    """
    result = []
    for f in sorted(filings_list,
                    key=lambda x: x.get("period_of_report", ""),
                    reverse=True):
        result.append({
            "accession_no":      f.get("accession_no"),
            "period_of_report":  f.get("period_of_report"),
            "fiscal_year":       f.get("fiscal_year"),
            "fiscal_quarter":    f.get("fiscal_quarter"),
            "period_type":       f.get("period_type"),
            "gaap_eps":          f.get("gaap_eps"),
            "adjusted_eps":      f.get("adjusted_eps"),
            "gaap_net_income":   f.get("gaap_net_income"),
            "adjusted_net_income": f.get("adjusted_net_income"),
            "diluted_shares_used": f.get("diluted_shares_used"),
            "health":            f.get("ai_analysis", {}).get("health"),
            "ai_comment":        f.get("ai_analysis", {}).get("comment"),
        })
    return result


# ─── メイン ───────────────────────────────────────────────────────

def run():
    repo_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

    # 監視銘柄読み込み
    tickers_path = os.path.join(repo_root, "config", "monitor_tickers.yaml")
    with open(tickers_path, encoding="utf-8") as f:
        tickers = yaml.safe_load(f).get("tickers", [])

    # 調整項目設定
    adj_config_path = os.path.join(repo_root, "config", "adjustment_items.json")
    adj_config = load_config(adj_config_path)

    # 全銘柄サマリー（data/index.json 用）
    index_entries = []

    for ticker in tickers:
        print(f"\n{'='*50}")
        print(f"Processing {ticker} ...")

        try:
            # ① 全 filing のキーファクト取得（edgartools）
            filings_data = extract_all_filings_for_ticker(ticker)
            if not filings_data:
                print(f"  [SKIP] {ticker}: データなし")
                continue

            processed_filings = []

            for filing_facts in filings_data:
                accession_no = filing_facts.get("accession_no", "unknown")
                period       = filing_facts.get("period_of_report", "")
                print(f"  → {period} ({filing_facts.get('period_type','?')}) {accession_no}")

                # 既存ファイルがあればスキップ（GitHub Actions の増分更新）
                out_path = os.path.join(repo_root, "data", ticker, f"{accession_no}.json")
                if os.path.exists(out_path):
                    try:
                        with open(out_path, encoding="utf-8") as f:
                            existing = json.load(f)
                        # AI 分析済みならスキップ
                        if existing.get("ai_analysis", {}).get("health") not in (None, "Error"):
                            processed_filings.append(existing)
                            continue
                    except Exception:
                        pass

                # ② 調整検知
                raw_facts   = filing_facts.get("raw_facts", {})
                adjustments = detect_adjustments(raw_facts, adj_config)

                # ③ 税後調整額計算
                net_adj, detailed_adj = apply_tax_adjustments(adjustments, filing_facts)

                # ④ EPS 計算
                result = calculate_eps(filing_facts, net_adj, detailed_adj)

                # ⑤ AI 分析（エラー時はスキップして後で再試行）
                try:
                    ai_raw = analyze_adjustments(ticker, result, detailed_adj)
                    try:
                        # JSON コードブロック除去
                        clean = ai_raw.strip()
                        if clean.startswith("```"):
                            clean = "\n".join(clean.split("\n")[1:])
                            clean = clean.rstrip("`").strip()
                        ai_parsed = json.loads(clean)
                    except Exception:
                        ai_parsed = {"health": "Unknown", "comment": ai_raw[:500]}
                    result["ai_analysis"] = ai_parsed
                except Exception as e:
                    print(f"    [WARN] AI 分析失敗: {e}")
                    result["ai_analysis"] = {"health": "Error", "comment": str(e)[:200]}

                result["processed_at"] = datetime.now().isoformat()

                # 個別ファイル保存
                save_json(out_path, result)
                print(f"    Saved: {out_path}")
                processed_filings.append(result)

            if not processed_filings:
                print(f"  [SKIP] {ticker}: 処理済み filing なし")
                continue

            # 最新 filing = latest.json
            latest = sorted(processed_filings,
                            key=lambda x: x.get("period_of_report", ""),
                            reverse=True)[0]
            save_json(os.path.join(repo_root, "data", ticker, "latest.json"), latest)

            # history.json（全件サマリー）
            history = build_history_summary(processed_filings)
            save_json(os.path.join(repo_root, "data", ticker, "history.json"),
                      {"ticker": ticker, "updated_at": datetime.now().isoformat(),
                       "filings": history})

            # TTM
            ttm = ttm_calc(processed_filings)
            if ttm:
                save_json(os.path.join(repo_root, "data", ticker, "ttm.json"),
                          {**ttm, "ticker": ticker,
                           "updated_at": datetime.now().isoformat()})

            # index エントリ
            # YoY: 最新四半期 vs 1年前の同四半期
            quarters = sorted(
                [f for f in processed_filings if f.get("period_type") == "Q"],
                key=lambda x: x.get("period_of_report", ""), reverse=True)
            yoy = None
            if len(quarters) >= 5:
                yoy = yoy_growth(
                    quarters[0].get("adjusted_eps"),
                    quarters[4].get("adjusted_eps"))

            index_entries.append({
                "ticker":           ticker,
                "latest_period":    latest.get("period_of_report"),
                "period_type":      latest.get("period_type"),
                "adjusted_eps":     latest.get("adjusted_eps"),
                "gaap_eps":         latest.get("gaap_eps"),
                "health":           latest.get("ai_analysis", {}).get("health"),
                "yoy_growth_pct":   yoy,
                "ttm_adjusted_eps": ttm.get("adjusted_eps") if ttm else None,
            })

        except Exception as e:
            import traceback
            print(f"  [ERROR] {ticker}: {e}")
            traceback.print_exc()

    # data/index.json 更新
    save_json(
        os.path.join(repo_root, "data", "index.json"),
        {"updated_at": datetime.now().isoformat(), "tickers": index_entries}
    )
    print("\nDone. data/index.json updated.")


if __name__ == "__main__":
    run()
