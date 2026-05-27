"""
TANUKI VALUATION - Pipeline v2.1
全ティッカーを処理し、latest.jsonを生成

使用方法:
    python pipeline.py
    python pipeline.py TSLA PLTR  # 特定ティッカーのみ

v2.1変更点:
    - AI検証機能（validator.py）を統合
    - latest.jsonに"validation"フィールドを追加

v2.2変更点:
    - cik_lookup.csv の tanuki 列対応（false の銘柄をスキップ）
"""

import csv
import json
import os
import sys
from datetime import datetime
from typing import List, Optional

# 同一ディレクトリからのインポート
from data_fetcher import TanukiDataFetcher
from core_calculator import KoichiValuationCalculator
from validator import validate_calculation


class TanukiValuationPipeline:
    """TANUKI VALUATION パイプライン"""

    def __init__(self, output_dir: str = None, use_ai_validation: bool = True):
        self.fetcher = TanukiDataFetcher()
        self.use_ai_validation = use_ai_validation

        if output_dir:
            self.output_dir = output_dir
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(output_dir)))
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
            self.output_dir = os.path.join(repo_root, "docs", "value-monitor", "tanuki_valuation", "data")

        self.repo_root = repo_root

        eps_data_dir = os.path.join(
            repo_root, "docs", "value-monitor", "adjusted_eps_analyzer", "data"
        )
        sec_data_dir = os.path.join(repo_root, "common", "sec_data", "data")
        self.calculator = KoichiValuationCalculator(
            eps_data_dir=eps_data_dir,
            sec_data_dir=sec_data_dir,
        )
        
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"   出力先: {self.output_dir}")

    def run(self, tickers: Optional[List[str]] = None) -> dict:
        print("=" * 60)
        print("TANUKI VALUATION Phase 4 実行開始")
        print(f"  Koichi式 v{KoichiValuationCalculator.VERSION}（動的WACC + 3段階DCF + FCFベース自動判定 + AI検証）")
        print("=" * 60)
        
        if tickers is None:
            tickers = self._load_tickers_from_csv()

        results = {}
        success_count = 0
        error_count = 0
        validation_stats = {"pass": 0, "warn": 0, "fail": 0, "error": 0}

        for ticker in tickers:
            print(f"\n{'─' * 40}")
            print(f"🔄 処理中: {ticker}")
            print(f"{'─' * 40}")
            
            try:
                financials = self.fetcher.get_financials(ticker)
                
                if "error" in financials:
                    print(f"❌ {ticker} スキップ: {financials['error']}")
                    error_count += 1
                    continue
                
                if financials.get("diluted_shares", 0) <= 100_000:
                    print(f"❌ {ticker} スキップ: diluted_shares不足")
                    error_count += 1
                    continue

                valuation = self.calculator.calculate_pt(financials)
                
                if "error" in valuation:
                    print(f"❌ {ticker} 計算エラー: {valuation['error']}")
                    error_count += 1
                    continue

                try:
                    validation = validate_calculation(
                        ticker, 
                        valuation, 
                        use_ai=self.use_ai_validation
                    )
                    valuation["validation"] = validation
                    
                    overall = validation.get("overall", "ERROR")
                    if overall == "PASS":
                        print(f"   ✅ 検証パス")
                        validation_stats["pass"] += 1
                    elif overall == "WARN":
                        print(f"   ⚠️  検証警告: {self._get_warn_details(validation)}")
                        validation_stats["warn"] += 1
                    else:
                        print(f"   ❌ 検証失敗: {self._get_warn_details(validation)}")
                        validation_stats["fail"] += 1
                        
                except Exception as e:
                    print(f"   ⚠️  検証エラー: {e}")
                    valuation["validation"] = {
                        "validated_at": datetime.now().strftime("%Y-%m-%d"),
                        "model": "error",
                        "checks": {},
                        "overall": "ERROR",
                        "ai_comment": str(e)
                    }
                    validation_stats["error"] += 1

                self._save_result(ticker, valuation)
                results[ticker] = valuation
                success_count += 1
                
                per_share = valuation.get("intrinsic_value_per_share", 0)
                current = financials.get("current_price", 0)
                upside = valuation.get("upside_percent", 0)
                
                print(f"✅ {ticker} 完了:")
                print(f"   理論株価: ${per_share:,.2f}")
                print(f"   現在株価: ${current:,.2f}")
                print(f"   乖離率: {upside:+.1f}%")

            except Exception as e:
                print(f"❌ {ticker} 例外発生: {e}")
                error_count += 1
                import traceback
                traceback.print_exc()

        print("\n" + "=" * 60)
        print("🎉 TANUKI VALUATION 実行完了")
        print(f"   成功: {success_count} / 失敗: {error_count}")
        print(f"   検証結果: PASS={validation_stats['pass']} WARN={validation_stats['warn']} FAIL={validation_stats['fail']} ERROR={validation_stats['error']}")
        print(f"   出力先: {self.output_dir}")
        print("=" * 60)

        if results:
            self._save_tickers_index(list(results.keys()))

        return results

    def _load_tickers_from_csv(self) -> List[str]:
        """
        cik_lookup.csv から TANUKI 対象銘柄を取得

        tanuki 列が "false" の銘柄はスキップ（列が存在しない場合は全件対象・後方互換）
        """
        csv_path = os.path.join(self.repo_root, "config", "cik_lookup.csv")
        if not os.path.exists(csv_path):
            print(f"❌ エラー: {csv_path} が見つかりません")
            sys.exit(1)
        tickers = []
        skipped = []
        with open(csv_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tanuki = row.get("tanuki", "true").strip().lower()
                if tanuki == "false":
                    skipped.append(row["ticker"])
                else:
                    tickers.append(row["ticker"])
        if skipped:
            print(f"   ℹ️  TANUKIスキップ銘柄: {', '.join(skipped)}")
        return tickers

    def _get_warn_details(self, validation: dict) -> str:
        checks = validation.get("checks", {})
        failed = [k for k, v in checks.items() if not v.get("pass", True)]
        return ", ".join(failed) if failed else "unknown"

    def _load_eps_map(self) -> dict:
        if hasattr(self, "_eps_summary_cache"):
            return self._eps_summary_cache
        eps_path = os.path.join(
            self.repo_root, "docs", "value-monitor", "adjusted_eps_analyzer", "data", "summary.json"
        )
        result = {}
        if os.path.exists(eps_path):
            try:
                with open(eps_path, encoding="utf-8") as f:
                    data = json.load(f)
                result = {t["ticker"]: t for t in data.get("tickers", [])}
            except Exception:
                pass
        self._eps_summary_cache = result
        return result

    def _compute_tanuki_score(self, ticker: str, valuation: dict) -> dict:
        """TANUKI SCOREをパイプライン時に計算（JS classify/calcFundaのPython移植）"""
        upside   = valuation.get("upside_percent")
        fcf_base = valuation.get("fcf_base", {}).get("base_fcf")

        rev_yoy = rule40 = stage = None
        poc_path = os.path.join(
            self.repo_root, "docs", "value-monitor", "hypecore", "data", f"{ticker}_poc.json"
        )
        if os.path.exists(poc_path):
            try:
                with open(poc_path, encoding="utf-8") as f:
                    poc = json.load(f)
                monthly = poc.get("monthly") or []
                last = monthly[-1] if monthly else {}
                rev_yoy = last.get("rev_yoy")
                rule40  = last.get("rule40")
                stage   = last.get("stage")
            except Exception:
                pass

        eps_yoy = None
        eps_entry = self._load_eps_map().get(ticker, {})
        yoy_dec = eps_entry.get("yoy_growth")
        if yoy_dec is not None:
            eps_yoy = yoy_dec * 100

        # calcFunda (JS移植)
        funda = 0
        funda += 25 if rev_yoy is not None and rev_yoy > 20 else 15 if rev_yoy is not None and rev_yoy >= 0 else 0
        funda += 25 if rule40  is not None and rule40  > 40 else 15 if rule40  is not None and rule40  >= 20 else 0
        funda += 25 if eps_yoy is not None and eps_yoy > 20 else 15 if eps_yoy is not None and eps_yoy >= 0 else 0
        funda += 25 if fcf_base is not None and fcf_base > 0 else 0

        # classify (JS移植: FG=50固定でtiming省略し upside直接判定)
        fcf_est = valuation.get("fcf_estimation", {}).get("estimated_fcf")
        sell_funda = (
            rev_yoy is not None and rev_yoy < 0
            and rule40 is not None and rule40 < 20
            and (fcf_base is not None and fcf_base < 0
                 or (fcf_est is not None and fcf_base is not None and fcf_est < fcf_base * 0.8))
        )
        if funda < 25:
            score = "PASS"
        elif sell_funda:
            score = "SELL"
        elif funda >= 50:
            if upside is not None and upside < -30 and stage is not None and stage >= 3:
                score = "TRIM"
            elif upside is not None and upside > 20:
                score = "BUY"
            elif upside is not None and upside > 0:
                score = "WATCH"
            else:
                score = "HOLD"
        else:
            score = "HOLD"

        comment = self._generate_score_comment(score, upside, rev_yoy, rule40, fcf_base, funda)
        return {"score": score, "funda_score": funda, "score_comment": comment}

    def _generate_score_comment(self, score, upside, rev_yoy, rule40, fcf_base, funda) -> str:
        """スコアに基づくルールベースコメント（30字程度の日本語）"""
        parts = []
        if upside is not None:
            if   upside >  30: parts.append(f"割安圏({upside:.0f}%)で買い余地大")
            elif upside >  10: parts.append(f"割安({upside:.0f}%)傾向")
            elif upside >   0: parts.append(f"若干割安({upside:.0f}%)")
            elif upside > -20: parts.append("フェアバリュー近辺")
            else:              parts.append(f"割高({upside:.0f}%超)")
        if fcf_base is not None:
            parts.append("FCF黒字" if fcf_base > 0 else "FCF赤字注意")
        if rev_yoy is not None:
            if   rev_yoy > 20: parts.append("売上成長加速")
            elif rev_yoy > 0:  parts.append("売上安定成長")
            else:              parts.append("売上成長停滞")
        return "、".join(parts[:3]) if parts else f"{score}（データ不足）"

    def _save_result(self, ticker: str, valuation: dict) -> None:
        ticker_dir = os.path.join(self.output_dir, ticker)
        history_dir = os.path.join(ticker_dir, "history")
        os.makedirs(history_dir, exist_ok=True)

        latest_data = {k: v for k, v in valuation.items() if k != "calculation_steps"}
        latest_path = os.path.join(ticker_dir, "latest.json")
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(latest_data, f, ensure_ascii=False, indent=2)

        date_str = valuation.get("calculation_date", datetime.now().strftime("%Y-%m-%d"))
        filename_safe = date_str.replace(":", "-")
        history_path = os.path.join(history_dir, f"{filename_safe}.json")
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(valuation, f, ensure_ascii=False, indent=2)

        # history.json（時系列チャート用・軽量サマリ）に追記
        history_summary_path = os.path.join(ticker_dir, "history.json")
        history_summary = []
        if os.path.exists(history_summary_path):
            try:
                with open(history_summary_path, encoding="utf-8") as f:
                    history_summary = json.load(f)
            except Exception:
                history_summary = []

        score_data = self._compute_tanuki_score(ticker, valuation)

        entry = {
            "date": date_str,
            "intrinsic_value_per_share": valuation.get("intrinsic_value_per_share"),
            "intrinsic_value_beta": valuation.get("intrinsic_value_beta"),
            "current_price": valuation.get("components", {}).get("current_price"),
            "ma200": valuation.get("components", {}).get("ma200"),
            "upside_percent": valuation.get("upside_percent"),
            "growth_rate": valuation.get("growth_scenarios", {}).get("primary", {}).get("rate"),
            "scenario_bear": valuation.get("scenario_valuations", {}).get("bear", {}).get("intrinsic_value_per_share"),
            "scenario_bull": valuation.get("scenario_valuations", {}).get("bull", {}).get("intrinsic_value_per_share"),
            "tanuki_score":  score_data.get("score"),
            "funda_score":   score_data.get("funda_score"),
            "score_comment": score_data.get("score_comment"),
        }
        # 同日エントリを上書き
        history_summary = [e for e in history_summary if e.get("date") != date_str]
        history_summary.append(entry)
        history_summary.sort(key=lambda e: e.get("date", ""))

        with open(history_summary_path, "w", encoding="utf-8") as f:
            json.dump(history_summary, f, ensure_ascii=False, indent=2)

        print(f"   💾 保存: {latest_path}")

    def _save_tickers_index(self, success_tickers: List[str]) -> None:
        index_path = os.path.join(self.output_dir, "tickers.json")

        existing_tickers = []
        if os.path.exists(index_path):
            try:
                with open(index_path, encoding="utf-8") as f:
                    existing_tickers = json.load(f).get("tickers", [])
            except Exception:
                pass

        merged = sorted(set(existing_tickers) | set(success_tickers))
        valid = [
            t for t in merged
            if os.path.exists(os.path.join(self.output_dir, t, "latest.json"))
        ]

        index_data = {
            "tickers": valid,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(valid)
        }

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"   📋 tickers.json 更新: {valid}")

    def run_single(self, ticker: str) -> dict:
        return self.run([ticker]).get(ticker, {})


def main():
    tickers = sys.argv[1:] if len(sys.argv) > 1 else None
    use_ai = False
    pipeline = TanukiValuationPipeline(use_ai_validation=use_ai)
    results = pipeline.run(tickers)
    sys.exit(0 if results else 1)


if __name__ == "__main__":
    main()
