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

        # TANUKIスコアを先に計算してlatest.jsonとhistory.json両方に保存
        score_data = self._compute_tanuki_score(ticker, valuation)

        latest_data = {k: v for k, v in valuation.items() if k != "calculation_steps"}
        latest_data["tanuki_score"]  = score_data.get("score")
        latest_data["funda_score"]   = score_data.get("funda_score")
        latest_data["score_comment"] = score_data.get("score_comment")
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

        report_text = self._generate_report(ticker, valuation, score_data)
        self._save_report(ticker, report_text)

        print(f"   💾 保存: {latest_path}")

    def _generate_report(self, ticker: str, valuation: dict, score_data: dict) -> str:
        """銘柄別統合レポートをプレーンテキストで生成"""
        now = valuation.get("calculation_date", datetime.now().strftime("%Y-%m-%d"))
        comps = valuation.get("components", {})
        rice = valuation.get("rice", {})
        scenarios = valuation.get("scenario_valuations", {})
        fcf_est = valuation.get("fcf_estimation", {})
        wacc_data = valuation.get("wacc", {})

        current_price = comps.get("current_price", 0) or 0
        upside = valuation.get("upside_percent")
        base_iv_top = valuation.get("intrinsic_value_per_share")
        wacc_val = wacc_data.get("value", 0) if isinstance(wacc_data, dict) else 0
        beta = comps.get("beta", "N/A")
        rpo_pv = comps.get("rpo_pv", 0) or 0
        sector = comps.get("sector", "")
        industry = comps.get("industry", "")
        roe = comps.get("roe_10yr_avg")

        score = score_data.get("score", "N/A")
        funda_score = score_data.get("funda_score", "N/A")
        score_comment = score_data.get("score_comment", "N/A")

        # --- Matrix position ---
        rice_available = rice.get("available", False)
        rice_note = rice.get("note", "")
        rice_base_data = rice.get("base", {})
        rice_base_val = rice_base_data.get("rice")

        if rice_available:
            matrix = "①投資効率系"
            key_metric_y = f"RICE = {rice_base_val:.3f}" if rice_base_val is not None else "RICE = N/A"
            qx = upside is not None and upside >= 0
            qy = rice_base_val is not None and rice_base_val >= 2
            yH, yL = "高効率", "低効率"
        elif "セクター除外" in rice_note:
            matrix = "②収益性系"
            roe_pct = roe * 100 if roe is not None else None
            key_metric_y = f"ROE_10yr_avg = {roe_pct:.1f}%" if roe_pct is not None else "ROE = N/A"
            qx = upside is not None and upside >= 0
            qy = roe_pct is not None and roe_pct >= 15
            yH, yL = "高ROE", "低ROE"
        elif "Q異常値" in rice_note:
            matrix = "③成長性系"
            key_metric_y = "Revenue_Growth (see HYPECORE)"
            qx = False
            qy = False
            yH, yL = "高成長", "低成長"
        else:
            matrix = "④キャッシュ創出力系"
            fcf_margin = fcf_est.get("fcf_margin")
            if fcf_margin is None:
                fcb = comps.get("fcf_base_used")
                rev = comps.get("latest_revenue")
                if fcb and rev:
                    fcf_margin = fcb / rev * 100
            key_metric_y = f"FCF_Margin = {fcf_margin:.1f}%" if fcf_margin is not None else "FCF_Margin = N/A"
            qx = upside is not None and upside >= 0
            qy = fcf_margin is not None and fcf_margin >= 15
            yH, yL = "高FCF", "低FCF"

        xL = "割安" if qx else "割高"
        yL_label = yH if qy else yL
        quadrant = ("右上" if qy else "右下") if qx else ("左上" if qy else "左下")
        label = f"{xL}×{yL_label}"

        # --- Scenario valuations ---
        bear_sc = scenarios.get("bear", {})
        base_sc = scenarios.get("base", {})
        bull_sc = scenarios.get("bull", {})
        bear_g = (bear_sc.get("growth_rate") or 0) * 100
        base_g = (base_sc.get("growth_rate") or 0) * 100
        bull_g = (bull_sc.get("growth_rate") or 0) * 100
        bear_iv = bear_sc.get("intrinsic_value_per_share") or 0
        base_iv = base_sc.get("intrinsic_value_per_share") or base_iv_top or 0
        bull_iv = bull_sc.get("intrinsic_value_per_share") or 0

        def dev(iv):
            if iv and current_price:
                return (iv - current_price) / current_price * 100
            return 0.0

        fcf_conv = fcf_est.get("conversion_rate", "N/A")
        fcf_industry = fcf_est.get("sector", "") or industry

        # --- RICE components ---
        rice_q = rice.get("q", "N/A")
        rice_cf = rice.get("cf_conversion", "N/A")
        rice_wacc = rice.get("wacc", "N/A")
        rice_bear_d = rice.get("bear", {})
        rice_bull_d = rice.get("bull", {})
        sbc_adjusted = "SBC補正済み" in rice_note
        excl_reason = rice_note if not rice_available else "N/A"

        # --- EPS data ---
        eps_summary_entry = self._load_eps_map().get(ticker, {})
        adj_eps = eps_summary_entry.get("adjusted_eps")
        gaap_eps_val = eps_summary_entry.get("gaap_eps")
        eps_diff = eps_summary_entry.get("eps_diff")
        yoy_growth = eps_summary_entry.get("yoy_growth")
        yoy_pct = f"{yoy_growth * 100:.1f}" if yoy_growth is not None else "N/A"

        adj_items_str = "N/A"
        recent_quarters = []
        q_path = os.path.join(
            self.repo_root, "docs", "value-monitor", "adjusted_eps_analyzer", "data", ticker, "quarterly.json"
        )
        if os.path.exists(q_path):
            try:
                with open(q_path, encoding="utf-8") as f:
                    q_data = json.load(f)
                # quarters[0] = 最新、降順で格納
                quarters = q_data.get("quarters", [])
                if quarters:
                    items = [a.get("item_id", "") for a in quarters[0].get("adjustments", [])]
                    adj_items_str = "/".join(items) if items else "N/A"
                    for q in quarters[:4]:
                        fy = q.get("fiscal_year", "?")
                        qt = q.get("quarter", "?")
                        q_label = f"{fy} Q{qt}" if isinstance(qt, int) else f"{fy} {qt}"
                        recent_quarters.append({
                            "label": q_label,
                            "actual": q.get("adjusted_eps"),
                        })
            except Exception:
                pass

        # --- HypeCore data ---
        poc_path = os.path.join(
            self.repo_root, "docs", "value-monitor", "hypecore", "data", f"{ticker}_poc.json"
        )
        hype_phase = "N/A"
        hype_alpha = valuation.get("alpha", "N/A")
        hype_signal = "N/A"
        phase_history = []
        short_int = "N/A"
        rev_yoy_hype = None
        rec_mean = None
        if os.path.exists(poc_path):
            try:
                with open(poc_path, encoding="utf-8") as f:
                    poc = json.load(f)
                monthly = poc.get("monthly", [])
                if monthly:
                    last = monthly[-1]
                    stage = last.get("stage")
                    stage_label = last.get("stage_label", f"Phase{stage}")
                    hype_phase = f"Phase{stage} ({stage_label})" if stage else "N/A"
                    substage = last.get("substage_label", "")
                    substage_watch = last.get("substage_watch", "")
                    hype_signal = f"{substage} — {substage_watch}" if substage else "N/A"
                    phase_history = [(m.get("month", "?"), m.get("stage"), m.get("stage_label", "")) for m in monthly[-6:]]
                    si = last.get("short_pct_float")
                    if si is not None:
                        short_int = f"{si * 100:.1f}"
                    rev_yoy_hype = last.get("rev_yoy")
                    rec_mean = last.get("recommendation_mean")
            except Exception:
                pass

        # --- STONKS SILO data ---
        stonks_path = os.path.join(
            self.repo_root, "docs", "value-monitor", "stonks-silo", "data", "results.json"
        )
        stonks_data = {}
        if os.path.exists(stonks_path):
            try:
                with open(stonks_path, encoding="utf-8") as f:
                    stonks_data = json.load(f).get("tickers", {}).get(ticker, {})
            except Exception:
                pass

        short_target = "yes" if stonks_data else "no"

        runway_raw = stonks_data.get("runway", {}).get("runway_months") if stonks_data else None
        if isinstance(runway_raw, (int, float)):
            runway_m = f"{runway_raw:.1f}"
        elif runway_raw is not None:
            runway_m = str(runway_raw)
        else:
            runway_m = "N/A"

        rev_growth_raw = stonks_data.get("deficit_quality", {}).get("revenue_growth_pct") if stonks_data else None
        if isinstance(rev_growth_raw, dict):
            valid = {k: v for k, v in rev_growth_raw.items() if v is not None}
            latest_key = max(valid.keys()) if valid else None
            rev_growth_val = valid.get(latest_key) if latest_key else None
        elif isinstance(rev_growth_raw, (int, float)):
            rev_growth_val = rev_growth_raw
        else:
            rev_growth_val = None

        if rev_growth_val is not None:
            rev_growth_str = f"{rev_growth_val:.1f}"
        elif rev_yoy_hype is not None:
            rev_growth_str = f"{rev_yoy_hype:.1f}"
        else:
            rev_growth_str = "N/A"

        # --- Build report lines ---
        L = []
        L.append(f"{ticker} INTEGRATED INVESTMENT REPORT")
        L.append(f"Generated: {now}")
        L.append(f"Price: ${current_price:,.2f}" if current_price else "Price: N/A")
        L.append("")
        # --- Timing score components ---
        ma200 = comps.get("ma200")
        ma200_dev = None
        if ma200 and current_price:
            ma200_dev = (current_price / ma200 - 1) * 100
        rec_label = "N/A"
        if rec_mean is not None:
            if rec_mean <= 1.5:
                rec_label = f"{rec_mean:.2f} (Strong Buy)"
            elif rec_mean <= 2.5:
                rec_label = f"{rec_mean:.2f} (Buy)"
            elif rec_mean <= 3.5:
                rec_label = f"{rec_mean:.2f} (Hold)"
            elif rec_mean <= 4.5:
                rec_label = f"{rec_mean:.2f} (Sell)"
            else:
                rec_label = f"{rec_mean:.2f} (Strong Sell)"
        timing_lines = [
            f"  Deviation_Rate: {upside:+.1f}%" if upside is not None else "  Deviation_Rate: N/A",
            f"  MA200_Deviation: {ma200_dev:+.1f}%" if ma200_dev is not None else "  MA200_Deviation: N/A",
            f"  HypeCore_Phase: {hype_phase}",
            f"  Analyst_Consensus: {rec_label}",
        ]

        L.append("[1. TANUKI SCORE]")
        L.append(f"Classification: {score}")
        L.append(f"Funda_Score: {funda_score}/100")
        L.append("Timing_Score (components):")
        L.extend(timing_lines)
        L.append(f"Comment: {score_comment}")
        L.append("Definition:")
        L.append("")
        L.append("Funda_Score: Composite score of financial health,")
        L.append("growth, and profitability (0-100)")
        L.append("Timing_Score: Reference indicators — deviation from IV,")
        L.append("MA200 momentum, hype phase, analyst consensus")
        L.append("(composite score requires FG index, shown as components)")
        L.append("BUY: Funda>=50 AND upside>10% AND Timing>=50")
        L.append("WATCH: Funda>=50 AND upside 0-20%")
        L.append("HOLD: Funda good, within tolerance range")
        L.append("TRIM: Funda good, overvalued(>-30%), post-euphoria")
        L.append("SELL: Funda deteriorating or long-term downtrend")
        L.append("PASS: Funda<25, excluded from consideration")
        L.append("")
        L.append("")
        L.append("[2. MATRIX POSITION]")
        L.append(f"Matrix: {matrix}")
        L.append(f"Quadrant: {quadrant}")
        L.append(f"Label: {label}")
        L.append(f"Key_Metric_Y: {key_metric_y}")
        L.append(f"Deviation_Rate: {upside:+.1f}%" if upside is not None else "Deviation_Rate: N/A")
        L.append("Thresholds:")
        L.append("  RICE_Threshold: 2.0 (above=high efficiency)")
        L.append("  ROE_Threshold: 15% (above=high profitability)")
        L.append("  FCFMargin_Threshold: 15% (above=high cash generation)")
        L.append("  Deviation_Threshold: 0% (positive=undervalued)")
        L.append("Definition:")
        L.append("")
        L.append("Matrix①(投資効率系): Y=RICE, X=Deviation Rate")
        L.append("RICE = (G x Q x CF) / WACC")
        L.append("Applied to: RICE-calculable tickers")
        L.append("Matrix②(収益性系): Y=ROE_10yr_avg, X=Deviation Rate")
        L.append("Applied to: Sector-excluded tickers")
        L.append("(Consumer/Financial/Utilities/RealEstate/Insurance)")
        L.append("Matrix③(成長性系): Y=Revenue_Growth%, X=Runway(years)")
        L.append("Applied to: Q-anomaly tickers (deep deficit)")
        L.append("Matrix④(キャッシュ創出力系): Y=FCF_Margin%, X=Deviation Rate")
        L.append("Applied to: All tickers with FCF data")
        L.append("Deviation_Rate = (Intrinsic_Value - Current_Price)")
        L.append("/ Current_Price x 100")
        L.append("Positive deviation = undervalued (intrinsic > current)")
        L.append("")
        L.append("")
        L.append("[3. TANUKI VALUATION]")
        L.append(f"Current_Price: ${current_price:,.2f}" if current_price else "Current_Price: N/A")
        L.append(f"Intrinsic_Value_BASE: ${base_iv:,.2f}" if base_iv else "Intrinsic_Value_BASE: N/A")
        L.append(f"Deviation_BASE: {dev(base_iv):+.1f}%")
        L.append("Scenarios:")
        L.append(f"BEAR: Growth={bear_g:.1f}%, IV=${bear_iv:,.2f}, Deviation={dev(bear_iv):+.1f}%")
        L.append(f"BASE: Growth={base_g:.1f}%, IV=${base_iv:,.2f}, Deviation={dev(base_iv):+.1f}%")
        L.append(f"BULL: Growth={bull_g:.1f}%, IV=${bull_iv:,.2f}, Deviation={dev(bull_iv):+.1f}%")
        wacc_pct = wacc_val * 100 if isinstance(wacc_val, (int, float)) else None
        L.append(f"WACC: {wacc_pct:.2f}%" if wacc_pct is not None else "WACC: N/A")
        L.append(f"Beta: {beta}")
        L.append(f"FCF_Conversion_Rate: {fcf_conv} (Industry: {fcf_industry})")
        L.append(f"RPO_PV: ${rpo_pv:,.0f} (Remaining Performance Obligation premium)")
        L.append("Definition:")
        L.append("")
        L.append("Intrinsic Value: Calculated via FCF-based DCF model")
        L.append("Formula: IV = sum(FCF_t / (1+WACC)^t) + Terminal_Value")
        L.append("Terminal_Value = FCF_final x (1+g) / (WACC - g)")
        L.append("WACC = Rf + Beta x (Rm - Rf)")
        L.append("Rm=10% (market return basis, Beta=0 gives Rf+risk_premium)")
        L.append("FCF_Conversion_Rate: Industry-standard ratio to estimate")
        L.append("FCF from OCF (accounts for capex intensity by sector)")
        L.append("RPO: Remaining Performance Obligation, booked future")
        L.append("revenue not yet recognized; added as DCF premium")
        L.append("")
        L.append("")
        L.append("[4. RICE METRICS]")
        L.append(f"Available: {str(rice_available).lower()}")
        L.append(f"Exclusion_Reason: {excl_reason}")
        if rice_available:
            L.append(f"BEAR: RICE={rice_bear_d.get('rice', 'N/A')}")
            L.append(f"BASE: RICE={rice_base_data.get('rice', 'N/A')}")
            L.append(f"BULL: RICE={rice_bull_d.get('rice', 'N/A')}")
        else:
            L.append("BEAR: RICE=N/A")
            L.append("BASE: RICE=N/A")
            L.append("BULL: RICE=N/A")
        L.append("Components (BASE scenario):")
        g_val = rice_base_data.get("growth_rate")
        L.append(f"G  = {g_val*100:.1f}%  [TANUKI forward growth rate]" if g_val is not None else "G  = N/A")
        L.append(f"Q  = {rice_q}   [OCF / (NetIncome + SBC), 3yr avg]")
        if rice_cf != "N/A":
            L.append(f"CF = {rice_cf}  [RevGrowth / InvestmentIntensity, 1yr lag, 3yr avg]")
        else:
            L.append("CF = N/A")
        L.append(f"WACC = {rice_wacc * 100:.1f}%" if isinstance(rice_wacc, (int, float)) else f"WACC = {rice_wacc}")
        L.append(f"SBC_Adjusted: {str(sbc_adjusted).lower()}")
        L.append("Definition:")
        L.append("")
        L.append("RICE measures reinvestment efficiency and compounding power")
        L.append("G: Scenario-specific forward revenue growth rate")
        L.append("Q: Cash conversion quality")
        L.append("Q = OCF / max(NetIncome + SBC, 1), 3-year average")
        L.append("SBC added back to denominator to normalize")
        L.append("for stock-based compensation distortion")
        L.append("CF: Capital efficiency of growth investment")
        L.append("CF = RevGrowthRate / InvestmentIntensity (1yr lag)")
        L.append("InvestmentIntensity = (R&D + CapEx) / Revenue, 3yr avg")
        L.append("WACC: Weighted Average Cost of Capital")
        L.append("Primary basis: Rm=10% (Beta=0 scenario)")
        L.append("Reference: Beta-adjusted WACC also calculated")
        L.append("Interpretation: RICE>2.0 = high reinvestment efficiency")
        L.append("")
        L.append("")
        L.append("[5. EPS ANALYZER]")
        L.append(f"Latest_Adjusted_EPS: ${adj_eps:.4f}" if isinstance(adj_eps, (int, float)) else "Latest_Adjusted_EPS: N/A")
        L.append(f"Latest_GAAP_EPS: ${gaap_eps_val:.4f}" if isinstance(gaap_eps_val, (int, float)) else "Latest_GAAP_EPS: N/A")
        L.append(f"Adjustment_Delta: ${eps_diff:.4f} ({adj_items_str})" if isinstance(eps_diff, (int, float)) else "Adjustment_Delta: N/A")
        L.append(f"YoY_Growth: {yoy_pct}%")
        L.append("Recent Surprises (Adjusted EPS):")
        if recent_quarters:
            for q in recent_quarters:
                act = q.get("actual")
                act_str = f"${act:.4f}" if isinstance(act, (int, float)) else "N/A"
                L.append(f"  {q['label']}: Actual={act_str} vs Est=N/A -> N/A%")
        else:
            L.append("  N/A")
        L.append("Definition:")
        L.append("")
        L.append("Adjusted EPS: GAAP EPS excluding SBC, one-time charges,")
        L.append("M&A costs, and other non-recurring items")
        L.append("Adjustment items classified as:")
        L.append("SBC / Restructuring / Amortization / LegalSettlement /")
        L.append("AcquisitionCost / Other")
        L.append("Surprise Rate = (Actual - Estimate) / |Estimate| x 100")
        L.append("Positive surprise historically correlates with")
        L.append("short-term price appreciation (PEAD effect)")
        L.append("")
        L.append("")
        L.append("[6. HYPECORE]")
        L.append(f"Current_Phase: {hype_phase}")
        L.append(f"Alpha_Premium: {hype_alpha}" if hype_alpha != "N/A" else "Alpha_Premium: N/A")
        L.append(f"HYPE_Signal: {hype_signal}")
        L.append("Phase_History (recent 6 months):")
        if phase_history:
            for m_str, st, sl in phase_history:
                L.append(f"{m_str}: Phase{st} ({sl})")
        else:
            L.append("N/A")
        L.append("Definition:")
        L.append("")
        L.append("HypeCore measures market sentiment and hype lifecycle stage")
        L.append("Phase1 (黎明期/Dawn): Early awareness, pre-euphoria,")
        L.append("price below MA200, low momentum")
        L.append("Phase2 (期待拡大期/Expansion): Rising expectations,")
        L.append("price approaching or above MA200, momentum building")
        L.append("Phase3 (陶酔期/Euphoria): Peak sentiment, price well above")
        L.append("MA200, high RSI, strong volume surge")
        L.append("Phase4 (期待剥落期/Deflation): Sentiment reversal,")
        L.append("price falling from peak, expectation reset")
        L.append("Alpha: Growth expectation premium added to IV")
        L.append("Higher alpha in Phase1-2, lower in Phase3-4")
        L.append("HYPE_Signal: Combined judgment of Matrix quadrant")
        L.append("and HypeCore phase")
        L.append("")
        L.append("")
        L.append("[7. STONKS SILO]")
        L.append(f"Short_Report_Target: {short_target}")
        L.append(f"Short_Interest: {short_int}%")
        L.append("Institutional_Ownership: N/A (not in data source)")
        L.append(f"Analyst_Consensus: {rec_label}")
        L.append(f"Runway_Months: {runway_m}" if stonks_data and runway_m != "N/A" else "Runway_Months: N/A (profitable or not in STONKS)")
        L.append(f"Revenue_Growth_YoY: {rev_growth_str}%")
        L.append("Definition:")
        L.append("")
        L.append("Short_Interest: % of float sold short")
        L.append("High short interest -> squeeze risk if positive catalyst")
        L.append("Institutional_Ownership: % held by institutions")
        L.append("High ownership -> stable shareholder base")
        L.append("Runway: Cash / Annual_FCF_Burn_Rate (years)")
        L.append("Critical for pre-profit companies; <1yr = distress risk")
        L.append("Revenue_Growth_YoY: TTM vs prior TTM")
        L.append("Primary growth metric for RICE-excluded tickers")
        L.append("")
        L.append("==============================================")
        L.append("DISCLAIMER: This report is generated automatically")
        L.append("from financial data for reference purposes only.")
        L.append("Not investment advice.")

        return "\n".join(L)

    def _save_report(self, ticker: str, report_text: str) -> None:
        ticker_dir = os.path.join(self.output_dir, ticker)
        report_path = os.path.join(ticker_dir, "report.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        print(f"   📄 レポート: {report_path}")

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
