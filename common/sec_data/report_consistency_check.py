#!/usr/bin/env python3
"""
report_consistency_check.py
全銘柄 report.txt の整合性一括チェック

検出項目:
  NG  1. FCF符号矛盾          FCF_History最新年マイナス & Matrix④ Key_Metric_Y 正値
  NG  2. DCF_Reliability欠落   FCF_Base行 or FCF_Conversion_Rate行あり & DCF_Reliability行なし
                              （Policy A: FCF_Base直接方式 / Policy B: FCF_Conversion_Rate方式、DCF-RELIABILITY-1）
  NG  3. LOW丸め未発動         DCF_Reliability=LOW & Classification が WATCH/SELL/PASS 以外
  NG  4. 割引率1段             Discount_Rate_Primary 行なし（旧WACC単独形式）
  NG  7. RPO条件違反           RPO_PV>0 & whitelist外 & RPO/Revenue<0.3
  NG  8. Matrix④高FCFラベル赤字 Matrix④ Label="高FCF" & 最新FCF実績マイナス
  NG  11. Revenue桁違い        annual_JSONの隣接年Revenue比が10倍超（誤XBRLタグ検出）
  WARN 5. NetDebt旧表示        Net_Debt行あり & ST_Invest 非ゼロ（latest.json）& 報告なし
  WARN 6. 負PER数値表示        Market_PER_GAAP が負数（N/M 未変換）
  WARN 9. セグメント設定陳腐化  segment_config fiscal_yearが2年以上前
  WARN 10. PS異常値            yfinance PSが自社計算値(price×shares/rev)の2.5倍超 or 0.4倍未満
  WARN 12. Cash-STI期ズレ      latest.jsonのCashが最新四半期値なのにST_Investが年次値のまま
  NG  13. RICE負値ラベルなし   rice.available=true かつ RICE<0 なのに Matrix Label に N/A/OCF赤字 なし
  NG  14. EPS>株価50%          EPS Analyzer直近Q adj_eps が株価の50%超（単位バグ検出）
  NG  15. EPS>株価             EPS Analyzer直近Q adj_eps が株価を上回る（単位バグ確実）
  WARN 16. TTM四半期不足       EPS Analyzer TTM計算に使用した四半期数が4未満
  NG  17. EPS全値$0.0          quarterly.json の全四半期 adj_eps=0.0（BUG-EPS-ZERO-1 回帰検知）
  WARN 18. G=15%デフォルト未調整 recommended_g あり & phase1_growth_auto_adjusted=False（DCF-DEFAULT-G-1 回帰）
  NG  19. SEC株数=0            quarterly.json に diluted_shares=0 の四半期（株数取得失敗）
  WARN 20. fcf_cagr floor張り付き growth.source=fcf_cagr かつ growth.rateがgrowth_floor(15%)に
                              完全一致（recommended_gの有無を問わず検知、GROWTH-FLOOR-VERDICT-1）
  WARN 21. Revenue段差型急変    直近6年の隣接年Revenue比が2.0倍以上/0.5倍以下（QUALITY-GATES-EPIC-1
                              Phase 2b-2、common.screening.dcf_validity_checker::check_c_data_jump()を
                              統合。NG-11との役割分担・NGではなくWARNとした理由は下記CHECK-21
                              実装箇所のコメント参照）
  WARN 22. fyキー競合          本人データ(reportDate==end_date)同士で同一fyタグに複数の異なる
                              真の期間が対応する矛盾（FY52WEEK-BUCKET-MISPLACE-1根本修正で新設。
                              CRM/FCX/CAKE/HON/COHR/AVAV/FICO/NVDAで実在確認済み。parser.pyの
                              tie-breakで自動解決済みのため非ブロッキング）
  WARN 23. fyタグ裏取り不一致  本人データ(is_own_data=True)自身の年度バケツキー
                              （determine_fiscal_year()の計算結果）と採用エントリの
                              生XBRL fyタグが食い違う（ARCH-DATA-1ステージ3で新設。
                              CHECK-22とは独立した別軸で「fyタグは単一だが値の年度バケツ配置
                              自体がfyタグと異なる」CDNS型を検知する。比較年度再掲エントリ
                              〈is_own_data=False〉はfyタグがfiling側の属性でしかなく
                              正常仕様のため対象外。自動修正なし）
  WARN 24. 決算期変更境界バケツ競合 決算期変更の境界年で、生fyタグ・end_dateの両方が
                              異なる2エントリ（本人データ側と非本人データ側）が同一年度
                              バケツ（computed_year）で競合する（FYE-CHANGE-BOUNDARY-
                              COLLISION-BLIND-1で新設。CHECK-22〈同一fyタグ前提〉・
                              CHECK-23〈勝者自身のfyタグとバケツの不一致、敗者側は対象外〉
                              のいずれとも異なる軸。RCAT（決算期を2回変更）で実在確認済み、
                              ELF/MSCI/NOWはクラスタリング候補ではあるが実際の競合なしと
                              確認済み。現状は_own_override_is_safe()の汎用accnベース判定
                              の副次効果で正しい値が採用されているため実害はなく、将来の
                              実装変更等で崩れうる潜在リスクの予防的可視化が目的。
                              自動修正なし）
  WARN 25. BS項目None         最新annual_YYYY.jsonのtotal_assets/total_liabilities/
                              stockholders_equity/current_assets/current_liabilities/
                              cash_and_equivalentsのいずれかがNone
                              （FY52WEEK-BS-NULL-SILENT-1 Phase A新設。全105銘柄実測で
                              None率がほぼ0-4%のフィールドに限定——ほぼ確実にデータ異常の
                              シグナル。従来はreader.py::get_net_cash()等で`or 0`により
                              静かに$0化され検知不能だった。short_term_investments/
                              long_term_debt/short_term_debt〈真のゼロとの判別困難〉・
                              rpo〈非SaaS銘柄はNoneが正常〉はPhase B/Cとして対象外）
  WARN 26. BS項目遷移(有値→None) short_term_investments/long_term_debt/
                              short_term_debt/rpo（WARN-25対象外の4フィールド）を
                              対象に、直近2年度分のannual_*.jsonを比較し、前年に
                              値があったフィールドが当年でNoneに遷移した場合に発火
                              （BS-FIELD-NONE-TRANSITION-DETECT-1新設）。period
                              （fyラベル）の年度差が厳密に1でない場合（決算期変更
                              等でfiles[-2]が真の「1年前」を表さない可能性がある
                              場合、FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1参照）・
                              annual_*.jsonが1年分のみ（新規登録銘柄）の場合は
                              判定不能として発火させない。事前調査（[[NVDA-STI-
                              TAG-UNIDENTIFIED-1]]調査時の体制確認）でFY52WEEK-
                              BS-NULL-SILENT-1「生涯フェードアウト」既確認済み
                              8件（APP/short_term_debt・BKNG/short_term_
                              investments・CPRT/long_term_debt・DOCN/short_term_
                              investments・ENTG/short_term_debt・KULR/short_term_
                              debt・MSCI/short_term_debt・SOUN/long_term_debt）が
                              実装直後に発火することが判明済みのため、
                              warn_acknowledged.jsonへ事前登録済み
  WARN 27. 近似値残差過大      parser.py::_apply_cross_filing_tags()が付与する
                              bs_provenance[field].is_approximated=Trueのエントリで
                              residual_pctが5%を超過（NVDA-STI-TAG-UNIDENTIFIED-1・
                              ANOMALY-PATTERN-CATALOG-1型C対応。cross_filing_tags
                              機構の将来の再利用先で、想定外に大きな乖離が
                              生じていないかの安全網。NVDA自身は+0.88%のため
                              通常は発火しない）
  WARN 28. 10-KT/10-QT除外    company_facts.jsonにform=10-KT/10-QTのaccnが存在する
                              のに、そのaccnがaccn_to_reportdate（submissions.json
                              由来）に未登録（[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]
                              新設。fetcher.py::_fetch_submissions_for_cikの
                              relevant_formsに10-KT/10-QTが含まれておらず、決算期
                              変更移行期報告書の本人データがis_own_data判定の対象外
                              になる構造的欠落を直接検知する。WARN-24〈決算期変更
                              境界バケツ競合〉はこの欠落が引き起こす症状〈バケツ
                              競合〉を検知するのに対し、本WARNは根本原因〈10-KT/
                              10-QT自体の除外〉を直接検知する別軸。RCATで実在確認
                              済み。自動修正なし、検知のみ）
  WARN 29. 会計恒等式不成立    Total_Assets=Total_Liabilities+Stockholders_Equity
                              が、NCI・一時的持分（MinorityInterest・
                              TemporaryEquityCarryingAmount系・
                              RedeemableNoncontrollingInterestEquity...
                              CarryingAmount系の許可リストのみ）を加算した拡張形
                              でも成立しない（[[CHECK29-ACCOUNTING-IDENTITY-
                              DETECTION-LAYER-1]]新設。①本体一致・②拡張形一致の
                              OR条件フォールバックはparser.py側で判定済みで、
                              いずれでも解消しないケースのみ発火する。実装前
                              シミュレーションで、無条件加算はKO/WMT/VZ等の
                              既存正常ケースで二重計上を起こすと判明したため、
                              「本体不一致の場合のみ拡張形を試す」設計とした。
                              105銘柄実測で156件中133件が拡張形で解消、残る
                              23件が本WARN対象（[[CHECK29-UNRESOLVED-23-MIXED-
                              CAUSES-1]]参照）。自動修正なし、検知のみ）
  NG   31. fixed_registry不整合 fixed_registry.json登録済みのticker×年度で、
                              annual_{year}.jsonの現在のsnapshot_hashが
                              registry記録時のsnapshot_hashと不一致
                              （[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]]
                              新設。フィックス機構の二次防御〈CI検知〉。
                              一次防御〈parser.py::_apply_fixed_registry_
                              freeze()〉が正しく機能していればこのNGは
                              発生しないはずであり、不一致は「意図しない
                              書き換え」または「registry更新を伴わない
                              手動再フィックス漏れ」を意味するためNG化する
                              （WARN化すると「許容してよいWARN」として
                              放置されるリスクがあり、フィックスの
                              「以後変更されない」という保証自体が
                              骨抜きになるため）。report.txtの有無に
                              関わらず常に実行する（common/sec_data/側の
                              検証でありTANUKI VALUATION出力に依存しない）。
                              自動修正なし、検知のみ）

WARN台帳（QUALITY-GATES-EPIC-1 Phase 1・2026-07-12新設）:
  config/warn_acknowledged.json に (CHECK番号, ticker) の組み合わせを事前登録すると
  「確認済み」として通常表示される。未登録のWARNは実行時に [🆕未確認 WARN-N ...] と
  強調表示される（非ブロッキング動作は維持、NG化はしない）。
"""

import argparse
import os
import re
import json
import glob
import sys

# ─── パス設定 ────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT    = os.path.normpath(os.path.join(SCRIPT_DIR, "../.."))
DATA_DIR     = os.path.join(REPO_ROOT, "docs/value-monitor/tanuki_valuation/data")
SEC_DATA_DIR = os.path.join(REPO_ROOT, "common/sec_data/data")
EPS_DATA_DIR = os.path.join(REPO_ROOT, "docs/value-monitor/adjusted_eps_analyzer/data")
RPO_CONFIG   = os.path.join(REPO_ROOT, "config/rpo_config.json")
SEG_CONFIG   = os.path.join(REPO_ROOT, "config/segment_config.json")
WARN_LEDGER  = os.path.join(REPO_ROOT, "config/warn_acknowledged.json")

# common.screening.dcf_validity_checker（CHECK-21用）をimportするためrepo_rootを
# sys.pathに追加する（registration_validator.pyと同一パターン）
sys.path.insert(0, REPO_ROOT)
from common.screening.dcf_validity_checker import check_c_data_jump  # noqa: E402
from common.sec_data import tickers as _tickers_mod  # noqa: E402
from common.sec_data.fetcher import load_submissions  # noqa: E402
from common.sec_data.parser import _load_fixed_registry  # noqa: E402
from common.sec_data.utils import compute_snapshot_hash  # noqa: E402

_SEG_CFG_CACHE: dict = {}

def _load_seg_config() -> dict:
    global _SEG_CFG_CACHE
    if not _SEG_CFG_CACHE:
        try:
            with open(SEG_CONFIG, encoding="utf-8") as f:
                _SEG_CFG_CACHE = json.load(f)
        except Exception:
            pass
    return _SEG_CFG_CACHE


# ─── ユーティリティ ──────────────────────────────────────────

def _load_rpo_whitelist() -> set:
    try:
        with open(RPO_CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
        return set(cfg.get("whitelist", {}).keys())
    except Exception:
        return set()


_WARN_CHECK_RE = re.compile(r'\[WARN-(\d+)')


def load_warn_ledger(path: str = WARN_LEDGER) -> set[tuple[str, str]]:
    """
    確認済みWARN台帳（QUALITY-GATES-EPIC-1 Phase 1）を読み込む。

    台帳ファイルが存在しない場合は空集合を返す（全WARNが「未確認」扱いになる）。
    キーは (CHECK番号, ticker) のタプル。exact な message文字列ではなく
    check番号単位で確認済みとするため、同じ銘柄・同じCHECKのWARNが
    数値だけ変わって再発しても「確認済み」のまま扱われる（意図的な粗さ）。
    """
    if not os.path.exists(path):
        return set()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {
            (entry["check"], entry["ticker"])
            for entry in data.get("acknowledged", [])
        }
    except Exception:
        return set()


def _check_discover_config_sync() -> list[str]:
    """CHECK-32: config/discover_config.json・config/theme_config.jsonと
    docs/portfolio/data/側コピーの内容一致を検証する
    （[[DISCOVER-CONFIG-DUAL-MGMT-1]]の同期漏れ検知。書き手が複数
    存在するため`Discover_Config_Sync.yml`が自動同期する設計だが、
    同期漏れ・ワークフロー失敗をNGとして検出する。
    [[FCFCONFIG-MISSING-DETECTION-WEAK-1]]と同型のサイレント破損対策）。
    ティッカー非依存の単発チェックのため、check_ticker()内ではなく
    run_checks()から直接1回だけ呼ばれる。NGメッセージのリストを返す。
    """
    ng: list[str] = []
    pairs = [
        ("config/discover_config.json", "docs/portfolio/data/discover_config.json"),
        ("config/theme_config.json", "docs/portfolio/data/theme_config.json"),
    ]
    for src_rel, dst_rel in pairs:
        src_path = os.path.join(REPO_ROOT, src_rel)
        dst_path = os.path.join(REPO_ROOT, dst_rel)
        if not os.path.exists(src_path):
            ng.append(f"  [NG-32 discover_config同期不整合] {src_rel} が存在しない")
            continue
        if not os.path.exists(dst_path):
            ng.append(
                f"  [NG-32 discover_config同期不整合] {dst_rel} が存在しない "
                f"（{src_rel}からの同期未実施の可能性）"
            )
            continue
        try:
            with open(src_path, encoding="utf-8") as f:
                src_data = json.load(f)
            with open(dst_path, encoding="utf-8") as f:
                dst_data = json.load(f)
        except Exception as e:
            ng.append(f"  [NG-32 discover_config同期不整合] {src_rel}/{dst_rel} 読み込みエラー ({e})")
            continue
        # JSONパース後の内容で比較する（バイト単位比較はしない）。
        # Windows core.autocrlf=true環境ではgit checkout時にCRLF/LFが
        # 混在しうるが、git自体はこれを「変更なし」とみなす（コミット時に
        # 正規化される）ため、生バイト比較は改行コード差だけで誤検知
        # （false NG）を起こす（2026-08-15実測で確認済み）。
        if src_data != dst_data:
            ng.append(
                f"  [NG-32 discover_config同期不整合] {src_rel} と {dst_rel} の内容が"
                f"一致しない → Discover_Config_Sync.ymlの自動同期が未実行・失敗している"
                f"可能性（自動修正なし）"
            )
    return ng


# CHECK-34: config/設定ファイル読み込みの横断解決チェック用レジストリ
# （[[CONFIG-LOAD-SILENT-FALLBACK-1]]）。CHECK-32/33で確立した
# 「代理の検証（チェッカー独自のos.path.exists()）ではなく、本番コードの
# 解決ロジックそのものを呼び出して検証する」原則を、個別チェック関数を
# ファイル数分作るのではなく1つの汎用関数+データテーブルへ一般化した
# （CHECK-33のfcf_conversion_config.json専用実装はこのテーブルの1エントリ
# として統合済み、専用関数は廃止）。
# import_style:
#   "flat"    - sys.pathにmodule_dirを追加し、モジュール名だけでimportする
#               （src.value.tanuki_valuation配下は__init__.pyの.wacc import
#               失敗によりフルパッケージimportができないため、既存テストと
#               同じflat importパターンを使う）
#   "package" - REPO_ROOT起点のフルドット区切りパスでimportする
#               （src.value.adjusted_eps_analyzer配下は相対import
#               〈from .module import ...〉を使っているためflat importでは
#               動かず、パッケージとしてimportする必要がある）
_CONFIG_LOADER_REGISTRY = [
    {
        "label": "config/rpo_config.json",
        "import_style": "flat",
        "module_dir": os.path.join(REPO_ROOT, "src", "value", "tanuki_valuation", "calculator"),
        "module": "adjustments",
        "func": "resolve_rpo_config_path",
    },
    {
        "label": "config/beta_config.json",
        "import_style": "flat",
        "module_dir": os.path.join(REPO_ROOT, "src", "value", "tanuki_valuation"),
        "module": "data_fetcher",
        "func": "resolve_beta_config_path",
    },
    {
        "label": "config/fcf_conversion_config.json",
        "import_style": "flat",
        "module_dir": os.path.join(REPO_ROOT, "src", "value", "tanuki_valuation", "calculator"),
        "module": "adjustments",
        "func": "resolve_fcf_conversion_config_path",
    },
    {
        "label": "config/split_history.yaml",
        "import_style": "package",
        "module_dir": None,
        "module": "src.value.adjusted_eps_analyzer.pipeline",
        "func": "resolve_split_history_path",
    },
]


def _check_config_loaders_resolvable() -> list[str]:
    """CHECK-34: config/配下の設定ファイルが、各モジュールの実際の
    パス解決ロジックで解決できるかを_CONFIG_LOADER_REGISTRY駆動で
    横断検証する（[[CONFIG-LOAD-SILENT-FALLBACK-1]]）。

    ティッカー非依存の単発チェックのため、check_ticker()内ではなく
    run_checks()から直接1回だけ呼ばれる。NGメッセージのリストを返す。
    """
    import importlib

    ng: list[str] = []
    for entry in _CONFIG_LOADER_REGISTRY:
        label = entry["label"]
        try:
            if entry["import_style"] == "flat":
                if entry["module_dir"] not in sys.path:
                    sys.path.insert(0, entry["module_dir"])
                mod = importlib.import_module(entry["module"])
            else:
                mod = importlib.import_module(entry["module"])
            resolver = getattr(mod, entry["func"])
            resolved = resolver()
        except Exception as e:
            ng.append(
                f"  [NG-34 config読み込み解決失敗] {label}: "
                f"{entry['module']}.{entry['func']}()の呼び出しでエラー ({e})"
            )
            continue
        if resolved is None or not os.path.exists(resolved):
            ng.append(
                f"  [NG-34 config読み込み解決失敗] {label}: "
                f"{entry['module']}.{entry['func']}()がパスを解決できない "
                f"(resolved={resolved!r})。読み込み処理がサイレントに"
                f"フォールバック値を使用している可能性（自動修正なし）"
            )
    return ng


def _check_fixed_registry_integrity(ticker: str) -> list[str]:
    """CHECK-31: fixed_registry.json登録済みのticker×年度について、
    annual_{year}.jsonの現在のsnapshot_hashがregistry記録時のものと
    一致するかを検証する（[[SEC-DATA-REDESIGN-OPERATIONAL-POLICY-1]]の
    二次防御・CI検知）。NGメッセージのリストを返す（登録なし・全一致の
    場合は空リスト）。
    """
    registry = _load_fixed_registry().get(ticker, {})
    if not registry:
        return []

    ng: list[str] = []
    for year_str, entry in sorted(registry.items()):
        path = os.path.join(SEC_DATA_DIR, ticker, f"annual_{year_str}.json")
        expected_hash = entry.get("snapshot_hash")
        if not os.path.exists(path):
            ng.append(
                f"  [NG-31 fixed_registry不整合] {year_str}: fixed登録済みだが"
                f"annual_{year_str}.jsonが存在しない"
            )
            continue
        try:
            with open(path, encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception as e:
            ng.append(
                f"  [NG-31 fixed_registry不整合] {year_str}: annual_{year_str}.json"
                f"読み込みエラー ({e})"
            )
            continue
        current_hash = compute_snapshot_hash(current_data)
        if current_hash != expected_hash:
            ng.append(
                f"  [NG-31 fixed_registry不整合] {year_str}: snapshot_hash不一致 "
                f"(registry={str(expected_hash)[:19]}..., current={current_hash[:19]}...) "
                f"→ fixed年度の値が意図せず変更された可能性（自動修正なし）"
            )
    return ng


def annotate_warn(ticker: str, message: str, ledger: set[tuple[str, str]]) -> tuple[str, bool]:
    """
    WARNメッセージに台帳照合結果を反映する。

    Returns:
        (表示用メッセージ, is_new) — is_new=Trueは台帳未登録（未確認）WARN
    """
    m = _WARN_CHECK_RE.search(message)
    if not m:
        return message, True
    check_id = f"WARN-{m.group(1)}"
    if (check_id, ticker) in ledger:
        return message, False
    return message.replace("[WARN-", "[\U0001f195未確認 WARN-", 1), True


def _read_report(ticker: str):
    path = os.path.join(DATA_DIR, ticker, "report.txt")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


def _read_latest(ticker: str) -> dict:
    path = os.path.join(DATA_DIR, ticker, "latest.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _read_fy_collision_log(ticker: str) -> list:
    """
    parser.py が本人データ(reportDate==end_date)同士のfyキー衝突を検知した
    際に書き出す common/sec_data/data/{ticker}/fy_collision_log.json を読む。
    CRM/FCX/CAKE/HON/COHR/AVAV/FICO/NVDA等で実在確認済み（filing代行者側の
    タグ付け起因と推測。原因追及は対象外、tie-break結果の継続監視が目的）。
    """
    path = os.path.join(SEC_DATA_DIR, ticker, "fy_collision_log.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("collisions", [])
    except Exception:
        return []


def _read_fy_tag_mismatch_log(ticker: str) -> list:
    """
    ARCH-DATA-1ステージ3（fyタグ裏取り）: parser.pyが年度バケツキー
    （determine_fiscal_year()の計算結果）と採用エントリの生XBRL fyタグの
    食い違いを検知した際に書き出す
    common/sec_data/data/{ticker}/fy_tag_mismatch_log.json を読む。
    CHECK-22（同一fyタグへの複数本人end_date競合）とは独立した別軸のチェックで、
    「fyタグは単一だが値の年度バケツ配置自体がfyタグと異なる」ケース
    （CDNS型）を対象とする。
    """
    path = os.path.join(SEC_DATA_DIR, ticker, "fy_tag_mismatch_log.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("mismatches", [])
    except Exception:
        return []


def _read_fye_boundary_collision_log(ticker: str) -> list:
    """
    FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1: parser.pyが決算期変更の境界年で
    「本人データ」と生fyタグが異なる別エントリ（end_dateも異なる）が同一年度
    バケツで競合したケースを検知した際に書き出す
    common/sec_data/data/{ticker}/fye_boundary_collision_log.json を読む。
    CHECK-22（同一fyタグへの複数本人end_date競合）・CHECK-23（勝者自身の
    fyタグとバケツの不一致）のいずれとも異なる軸で、競合する2エントリの
    生fyタグ・end_dateが両方とも異なるケース（RCAT型）を対象とする。
    """
    path = os.path.join(SEC_DATA_DIR, ticker, "fye_boundary_collision_log.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("collisions", [])
    except Exception:
        return []


def _read_bs_identity_violations_log(ticker: str) -> list:
    """
    [[CHECK29-ACCOUNTING-IDENTITY-DETECTION-LAYER-1]]: parser.pyが会計恒等式
    Total_Assets = Total_Liabilities + Stockholders_Equity（+NCI+一時的
    持分）の検証結果を書き出す
    common/sec_data/data/{ticker}/bs_identity_violations_log.json を読む。
    本体一致で解消したケースはparser.py側で記録対象外済みのため、ここには
    ①拡張形（NCI・一時的持分の許可リスト加算）で解消したケースと
    ②いずれでも解消しないケースのみが含まれる。
    """
    path = os.path.join(SEC_DATA_DIR, ticker, "bs_identity_violations_log.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f).get("violations", [])
    except Exception:
        return []


# FY52WEEK-BS-NULL-SILENT-1 Phase A対象フィールド。全105銘柄実測でNone率が
# ほぼ0-4%（CASH-TAG-MISSING-1系の既知欠落を除けばほぼ確実にデータ異常の
# シグナル）のBS項目に限定する。short_term_investments/long_term_debt/
# short_term_debt（真のゼロとの判別困難）・rpo（非SaaS銘柄はNoneが正常）は
# Phase B/Cとして対象外。
_BS_NULL_CHECK_FIELDS = [
    "total_assets", "stockholders_equity", "total_liabilities",
    "cash_and_equivalents", "current_assets", "current_liabilities",
]


def _read_latest_annual_bs(ticker: str) -> tuple[dict, str]:
    """最新のannual_YYYY.jsonのbs辞書とperiod文字列を返す。存在しなければ({}, "")"""
    files = sorted(glob.glob(os.path.join(SEC_DATA_DIR, ticker, "annual_*.json")))
    if not files:
        return {}, ""
    try:
        with open(files[-1], encoding="utf-8") as f:
            d = json.load(f)
        return d.get("bs", {}) or {}, str(d.get("period", ""))
    except Exception:
        return {}, ""


def _read_eps_quarterly(ticker: str) -> list:
    path = os.path.join(EPS_DATA_DIR, ticker, "quarterly.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else d.get("quarters", [])
    except Exception:
        return []


# ─── パーサ ──────────────────────────────────────────────────

def _parse_report(text: str) -> dict:
    """report.txt から必要フィールドを抽出して dict で返す。"""
    lines = text.splitlines()

    result = {
        "classification": None,
        "dcf_reliability": None,
        "matrix_type": None,
        "key_metric_y": None,
        "label": None,
        "has_fcf_base": False,
        "has_fcf_conversion_rate": False,
        "discount_rate_primary_data": None,  # data行のみ（定義行は除外）
        "has_wacc_old": False,               # 旧 WACC: 単独行
        "has_net_debt_report": False,
        "has_st_invest_report": False,
        "per_gaap_value": None,
        "rpo_pv_value": None,
        "rpo_pv_line": None,
        "fcf_history": [],                   # [(year, neg_fcf, margin_or_None)]
        "_raw_lines": lines,                 # CHECK-9 用
    }

    in_fcf_section = False

    for line in lines:
        # FCF_History セクション
        if line.strip() == "FCF_History:":
            in_fcf_section = True
            continue
        if in_fcf_section:
            # 年次 FCF 行: "  2025: $-7.19B (FCF_Margin: -140.2%)"
            # または:      "  2023: $-0.27B"
            m = re.match(
                r'^\s{2}(\d{4}): \$([^\s(]+)'
                r'(?:\s+\(FCF_Margin:\s*([+-]?\d+\.?\d*)%\))?',
                line,
            )
            if m:
                year = int(m.group(1))
                fcf_str = m.group(2)   # e.g. "-7.19B" or "9.11B"
                neg_fcf = fcf_str.startswith("-")
                margin  = float(m.group(3)) if m.group(3) is not None else None
                result["fcf_history"].append((year, neg_fcf, margin))
                continue
            # 空行や次セクション開始でリセット
            if line.strip() == "" or (line and not line.startswith(" ")):
                in_fcf_section = False

        # Classification（最初のマッチのみ）
        if result["classification"] is None:
            m = re.match(r'^Classification:\s+(\S+)', line)
            if m:
                result["classification"] = m.group(1)

        # DCF_Reliability（データ行: "DCF_Reliability: LOW ⚠️..." or "...HIGH"）
        if result["dcf_reliability"] is None:
            m = re.match(r'^DCF_Reliability:\s+(\w+)', line)
            if m:
                result["dcf_reliability"] = m.group(1)  # "LOW" or "HIGH"

        # Matrix: （最初のマッチ）
        if result["matrix_type"] is None:
            m = re.match(r'^Matrix:\s+(.+)', line)
            if m:
                result["matrix_type"] = m.group(1).strip()

        # Key_Metric_Y: （最初のマッチ）
        if result["key_metric_y"] is None:
            m = re.match(r'^Key_Metric_Y:\s+(.+)', line)
            if m:
                result["key_metric_y"] = m.group(1).strip()

        # Label: （最初のマッチ）
        if result["label"] is None:
            m = re.match(r'^Label:\s+(.+)', line)
            if m:
                result["label"] = m.group(1).strip()

        # FCF_Base: 行の存在
        if not result["has_fcf_base"]:
            if re.match(r'^FCF_Base:', line):
                result["has_fcf_base"] = True

        # FCF_Conversion_Rate: 行の存在（DCF-RELIABILITY-1: Policy B対象銘柄の判定）
        if not result["has_fcf_conversion_rate"]:
            if re.match(r'^FCF_Conversion_Rate:', line):
                result["has_fcf_conversion_rate"] = True

        # Discount_Rate_Primary データ行（"10.00% (DCF discount rate used)"）
        # 定義行は "Discount_Rate_Primary: Actual discount rate..." → 除外
        if result["discount_rate_primary_data"] is None:
            m = re.match(r'^Discount_Rate_Primary:\s+([\d.]+)%', line)
            if m:
                result["discount_rate_primary_data"] = m.group(1)

        # 旧 WACC: 単独行（"WACC: 12.0%"）
        if not result["has_wacc_old"]:
            if re.match(r'^WACC:\s+[\d.]+%', line):
                result["has_wacc_old"] = True

        # Net_Debt 行（Financial_Health セクション内 "  Net_Debt: ..."）
        if not result["has_net_debt_report"]:
            if re.match(r'^\s+Net_Debt:\s+\$', line):
                result["has_net_debt_report"] = True

        # ST_Invest 表記（"ST_Invest:" を含む行）
        if not result["has_st_invest_report"]:
            if "ST_Invest:" in line:
                result["has_st_invest_report"] = True

        # Market_PER_GAAP（Financial_Health セクション内）
        if result["per_gaap_value"] is None:
            m = re.match(r'^\s+Market_PER_GAAP:\s+(.+)', line)
            if m:
                result["per_gaap_value"] = m.group(1).strip()

        # RPO_PV データ行（"RPO_PV: $NNN ..."）
        if result["rpo_pv_value"] is None:
            m = re.match(r'^RPO_PV:\s+\$([0-9,]+)', line)
            if m:
                try:
                    result["rpo_pv_value"] = float(m.group(1).replace(",", ""))
                    result["rpo_pv_line"]  = line.strip()
                except ValueError:
                    pass

    return result


# ─── チェック本体 ─────────────────────────────────────────────

def check_ticker(ticker: str, whitelist: set) -> tuple[list, list]:
    """
    Returns (issues_ng, issues_warn)
    各要素は表示用文字列。
    """
    ng: list[str]   = []
    warn: list[str] = []

    # CHECK-31: fixed_registry.json整合性検知。common/sec_data/側の検証
    # であり、TANUKI VALUATION出力（report.txt）の有無に依存しないため
    # report.txt存在チェックより前に実行する。
    ng.extend(_check_fixed_registry_integrity(ticker))

    text = _read_report(ticker)
    if text is None:
        return ng, warn

    latest  = _read_latest(ticker)
    parsed  = _parse_report(text)

    fcf_hist = parsed["fcf_history"]
    latest_entry = max(fcf_hist, key=lambda x: x[0]) if fcf_hist else None

    # ── CHECK 1: FCF符号矛盾 ─────────────────────────────────
    mt = parsed["matrix_type"] or ""
    kmy = parsed["key_metric_y"] or ""
    if "④" in mt and "FCF_Margin" in kmy and latest_entry:
        m = re.search(r'FCF_Margin\s*=\s*([+-]?\d+\.?\d*)%', kmy)
        if m:
            key_margin = float(m.group(1))
            _, latest_neg, latest_margin = latest_entry
            # 最新FCFがマイナスなのに Key_Metric_Y が正値
            if latest_neg and key_margin > 0:
                ng.append(
                    f"  [NG-1 FCF符号矛盾] 最新FCH({latest_entry[0]})マイナス"
                    f" & Key_Metric_Y FCF_Margin={key_margin:+.1f}%"
                )
                ng.append(f"    → {kmy}")

    # ── CHECK 2: DCF_Reliability欠落 ─────────────────────────
    if parsed["has_fcf_base"] and parsed["dcf_reliability"] is None:
        ng.append("  [NG-2 DCF_Reliability欠落] FCF_Base行あり & DCF_Reliability行なし")
    # DCF-RELIABILITY-1: FCF_Conversion_Rate方式（Policy B対象）でも同様に欠落を検出
    if parsed["has_fcf_conversion_rate"] and parsed["dcf_reliability"] is None:
        ng.append("  [NG-2 DCF_Reliability欠落] FCF_Conversion_Rate行あり & DCF_Reliability行なし")

    # ── CHECK 3: LOW丸め未発動 ───────────────────────────────
    rel = parsed["dcf_reliability"]
    cls = parsed["classification"]
    if rel == "LOW" and cls not in ("WATCH", "SELL", "PASS", None):
        ng.append(
            f"  [NG-3 LOW丸め未発動] DCF_Reliability=LOW & Classification={cls}"
        )

    # ── CHECK 4: 割引率1段 ───────────────────────────────────
    if parsed["discount_rate_primary_data"] is None:
        if parsed["has_wacc_old"]:
            ng.append("  [NG-4 割引率1段] Discount_Rate_Primary行なし・旧WACC単独形式")
        else:
            ng.append("  [NG-4 割引率1段] Discount_Rate_Primary行が存在しない")

    # ── CHECK 5: NetDebt旧表示 (警告) ────────────────────────
    if parsed["has_net_debt_report"] and not parsed["has_st_invest_report"]:
        fh = latest.get("financial_health", {}) or {}
        st_inv = fh.get("short_term_investments") or 0
        if st_inv and st_inv != 0.0:
            warn.append(
                f"  [WARN-5 NetDebt旧表示] Net_Debt行あり & ST_Invest非ゼロ({st_inv:,.0f})"
                " だが報告行なし"
            )

    # ── CHECK 6: 負PER数値表示 (警告) ───────────────────────
    pv = parsed["per_gaap_value"] or ""
    if re.match(r'^-[\d.]+', pv):
        warn.append(f"  [WARN-6 負PER数値表示] Market_PER_GAAP: {pv}  (N/M 未変換)")

    # ── CHECK 7: RPO条件違反 ─────────────────────────────────
    rpo_pv = parsed["rpo_pv_value"]
    if rpo_pv is not None and rpo_pv > 0 and ticker not in whitelist:
        comp    = latest.get("components", {}) or {}
        rpo_raw = comp.get("rpo") or 0
        rev_ttm = comp.get("latest_revenue") or 0
        if rev_ttm > 0 and rpo_raw > 0:
            ratio = rpo_raw / rev_ttm
            if ratio < 0.30:
                ng.append(
                    f"  [NG-7 RPO条件違反] RPO_PV={rpo_pv:,.0f} >0"
                    f" & whitelist外 & RPO/Rev={ratio:.2f}<0.30"
                )
                ng.append(f"    → {parsed['rpo_pv_line']}")

    # ── CHECK 8: Matrix④高FCFラベルだが実績赤字 ─────────────
    lbl = parsed["label"] or ""
    if "④" in mt and "高FCF" in lbl and latest_entry:
        _, latest_neg, _ = latest_entry
        if latest_neg:
            ng.append(
                f"  [NG-8 Matrix④高FCFラベル赤字]"
                f" Label={lbl!r} & 最新FCF({latest_entry[0]})実績マイナス"
            )

    # ── CHECK 9: セグメント設定鮮度 (警告) ──────────────────
    # segment_configのfiscal_yearが2年以上前の場合、陳腐化の可能性を警告
    seg_cfg = _load_seg_config().get(ticker, {})
    if seg_cfg.get("enabled") and seg_cfg.get("fiscal_year"):
        fy_str = seg_cfg["fiscal_year"]  # e.g. "FY2025"
        m_fy = re.match(r"FY(\d{4})", fy_str)
        if m_fy:
            fy_yr = int(m_fy.group(1))
            # report内のGenerated行から生成年を取得
            gen_yr = None
            for line in (parsed.get("_raw_lines") or []):
                mm = re.search(r"Generated: (\d{4})-", line)
                if mm:
                    gen_yr = int(mm.group(1))
                    break
            if gen_yr and (gen_yr - fy_yr) >= 2:
                warn.append(
                    f"  [WARN-9 セグメント設定陳腐化] segment_config fiscal_year={fy_str}"
                    f" (現在{gen_yr}年、{gen_yr - fy_yr}年前のデータ)"
                )

    # ── CHECK 10: PS異常値 (警告) ────────────────────────────
    # yfinance PSが自社計算値(price×shares/revenue)と大きく乖離する場合にWARN
    comp = latest.get("components", {}) or {}
    ps_yf   = comp.get("ps")
    price   = comp.get("current_price") or 0
    shares  = comp.get("diluted_shares") or 0
    rev     = comp.get("latest_revenue") or 0
    sector  = (comp.get("sector") or "").lower()
    is_fin  = "financial" in sector or "bank" in sector
    if ps_yf is not None and price and shares and rev and not is_fin:
        ps_calc = (price * shares) / rev
        if ps_calc > 0:
            ratio = ps_yf / ps_calc
            if ratio > 2.5 or ratio < 0.4:
                warn.append(
                    f"  [WARN-10 PS異常値] yfinance PS={ps_yf:.1f}x vs 自社計算={ps_calc:.1f}x"
                    f" (乖離{ratio:.1f}倍) → ステール値の可能性"
                )

    # ── CHECK 11: Revenue桁違い (NG) ──────────────────────────
    # BUG-REV-SPAC-1型の誤XBRLタグ検出。
    # 隣接年Revenue比が10倍超かつベース年 > $1M (スタートアップ微少値を除外) の場合はNG。
    # IONQ 2022: Revenuesタグが$1,235M(SPAC調達)を誤タグ → 正常年$11M との比 112倍
    sec_ticker_dir = os.path.join(SEC_DATA_DIR, ticker)
    if os.path.isdir(sec_ticker_dir):
        _annual_revs: dict[int, float] = {}
        for _fn in sorted(os.listdir(sec_ticker_dir)):
            if _fn.startswith("annual_") and _fn.endswith(".json") and _fn[7:11].isdigit():
                _yr = int(_fn[7:11])
                try:
                    with open(os.path.join(sec_ticker_dir, _fn), encoding="utf-8") as _f:
                        _d = json.load(_f)
                    _r = _d.get("pl", {}).get("revenue")
                    if _r is not None:
                        _annual_revs[_yr] = _r
                except Exception:
                    pass
        _yrs = sorted(_annual_revs.keys())
        for _i, _yr in enumerate(_yrs):
            _r = _annual_revs[_yr]
            if _r <= 1_000_000:
                continue  # スタートアップ微少値はスキップ
            # 孤立年チェック: 前後両年が存在し、どちらも当該年の5%未満 → 誤XBRLタグ疑い
            # (IONQ 2022: 前=$2.1M/後=$22M vs $1,235M → どちらも1.8%以下 → 異常)
            # (ASTS 2025: 後年データなし → 正常な高成長トレンドとして除外)
            _prev = _annual_revs.get(_yrs[_i - 1]) if _i > 0 else None
            _next = _annual_revs.get(_yrs[_i + 1]) if _i < len(_yrs) - 1 else None
            if _prev is None or _next is None:
                continue  # 両端年はスキップ（孤立か判定不能）
            if _prev <= 0 or _next <= 0:
                continue
            _threshold = _r * 0.05  # 前後が当該年の5%未満なら異常
            if _prev < _threshold and _next < _threshold:
                _ratio_prev = _r / _prev
                _ratio_next = _r / _next
                ng.append(
                    f"  [NG-11 Revenue孤立年] {_yr}=${_r/1e6:.1f}M"
                    f" (前年{_yrs[_i-1]}=${_prev/1e6:.1f}M: {_ratio_prev:.0f}x,"
                    f" 翌年{_yrs[_i+1]}=${_next/1e6:.1f}M: {_ratio_next:.0f}x)"
                    f" → XBRLタグ誤り疑い(TICKER_RESTRICTIONSで修正)"
                )

    # CHECK-21: Revenue段差型急変（QUALITY-GATES-EPIC-1 Phase 2b-2）
    # common.screening.dcf_validity_checker::check_c_data_jump()を統合。
    #
    # NG-11との役割分担（重複ではなく併存）:
    #   NG-11（孤立年検知）は「前後両年とも当該年の5%未満」の**スパイク型**
    #   （その年だけ突出し、前後は元の水準に戻る）のみを検知する。
    #   WARN-21（本チェック、段差型検知）は前後判定を要さず、隣接年比が
    #   2.0倍以上/0.5倍以下であれば検知するため、**ジャンプ後も高い水準が
    #   継続するステップ型**（FICO/CPRT/LITE型、SEC-TAG-FICO-CPRT-1参照）も
    #   捕捉できる。NG-11はこのステップ型を構造的に検知できなかった
    #   （次年が「当該年の5%未満」に該当せず孤立年条件が成立しないため）。
    #
    # 重要度はNGではなくWARNとする（2026-07-12・実装検証時の判断変更）:
    # 全105銘柄で試験実行した結果、19銘柄が新規に該当したが、うち複数
    # （NVDA: AI GPU需要による実際の売上急成長$26.9B→$130.5B、JOBY: プレ
    # コマーシャル航空機企業のほぼゼロからの売上立ち上がり等）は一次情報
    # （annual_YYYY.json）で確認した結果、タグ取得ミスではなく実際の事業
    # 成長・売上立ち上がりだった。dcf_validity_checker.pyの2.0倍/0.5倍閾値は
    # 元々「人間が目視で選別する前提のフラグ付けツール」として設計されており、
    # NG（ブロッキング）にするには誤検知率が高すぎると判断しWARNへ変更した。
    c_flag, c_jumps, _c_revs = check_c_data_jump(REPO_ROOT, ticker)
    if c_flag:
        for _jump in c_jumps:
            warn.append(
                f"  [WARN-21 Revenue段差型急変] {_jump}"
                f" → XBRLタグ誤り、または実際の急成長/急減の可能性（要確認）"
            )

    # CHECK-12: Cash-ST_Invest 期整合チェック（BUG-NETDEBT-5回帰検知）
    # Cashが最新四半期値に更新されているのにST_Investが年次のままなら期ズレ
    _ann_files_c12 = sorted(glob.glob(os.path.join(SEC_DATA_DIR, ticker, "annual_*.json")))
    _q_files_c12   = sorted(glob.glob(os.path.join(SEC_DATA_DIR, ticker, "quarterly_*.json")))
    if _ann_files_c12 and _q_files_c12:
        try:
            with open(_ann_files_c12[-1], encoding="utf-8") as _f12:
                _ann12 = json.load(_f12)
            with open(_q_files_c12[-1], encoding="utf-8") as _f12q:
                _q12   = json.load(_f12q)
            _ann_period12 = _ann12.get("period", "")
            _q_period12   = _q12.get("period", "")
            if _ann_period12 != _q_period12:
                _ann_bs12  = _ann12.get("bs", {})
                _q_bs12    = _q12.get("bs", {})
                _ann_cash12 = _ann_bs12.get("cash_and_equivalents") or 0
                _q_cash12   = _q_bs12.get("cash_and_equivalents") or 0
                _ann_sti12  = _ann_bs12.get("short_term_investments") or 0
                _q_sti12    = _q_bs12.get("short_term_investments") or 0
                # Cashが四半期値に更新済み かつ ST_Investが存在し値が変化する場合のみチェック
                if _q_cash12 != _ann_cash12 and _q_sti12 > 0 and _q_sti12 != _ann_sti12:
                    _fh12     = latest.get("financial_health", {})
                    _rep_cash = _fh12.get("cash_and_equivalents") or 0
                    _rep_sti  = _fh12.get("short_term_investments") or 0
                    # レポートCash≈四半期値 かつ レポートSTI≈年次値 かつ STI≠四半期値 → 期ズレ未修正
                    # （quarterly STI ≈ annual STI の偽陽性を除外: PLTR/QBTS など）
                    _cash_ok = abs(_rep_cash - _q_cash12) < max(1_000_000, _q_cash12 * 0.01)
                    _sti_stale = abs(_rep_sti - _ann_sti12) < max(1_000_000, _ann_sti12 * 0.01)
                    _sti_already_qtr = abs(_rep_sti - _q_sti12) < max(1_000_000, _q_sti12 * 0.01)
                    if _cash_ok and _sti_stale and not _sti_already_qtr:
                        warn.append(
                            f"  [WARN-12 Cash-STI期ズレ] Cash={_rep_cash/1e6:.0f}M({_q_period12})"
                            f" だがST_Invest={_rep_sti/1e6:.0f}M(年次{_ann_period12})のまま"
                            f" → 正={_q_sti12/1e6:.0f}M"
                        )
        except Exception:
            pass

    # CHECK-13: RICE負値ラベル確認（RICE-3 回帰検知）
    # rice.available=true かつ BASE RICE < 0 なら Matrix Label が "N/A" か "OCF赤字" を含むこと
    _rice_ld = latest.get("rice", {})
    if _rice_ld.get("available", False):
        _rice_base_val = (_rice_ld.get("base") or {}).get("rice")
        if _rice_base_val is not None and _rice_base_val < 0:
            _label_c13 = parsed.get("label", "") or ""
            if "N/A" not in _label_c13 and "OCF赤字" not in _label_c13:
                ng.append(
                    f"  [NG-13 RICE負値ラベルなし] BASE RICE={_rice_base_val:.3f} "
                    f"だが Label='{_label_c13}' に 'N/A (OCF赤字)' なし"
                )

    # CHECK-14/15: EPS異常値チェック（単位バグ・大型一時利益検出）
    # EPS Analyzer quarterly.json の直近Q adj_eps / gaap_eps を株価と比較する
    _price_c14 = None
    for _pline in parsed.get("_raw_lines", []):
        _pm = re.match(r'^Price:\s*\$([0-9,.]+)', _pline.strip())
        if _pm:
            try:
                _price_c14 = float(_pm.group(1).replace(",", ""))
            except Exception:
                pass
            break

    if _price_c14 and _price_c14 > 0:
        _eps_qs = _read_eps_quarterly(ticker)
        if _eps_qs:
            _latest_q = sorted(_eps_qs, key=lambda x: x.get("filing_date", ""))[-1]
            _latest_adj = abs(_latest_q.get("adjusted_eps", 0) or 0)
            _latest_gaap = abs(_latest_q.get("gaap_eps", 0) or 0)
            _max_eps = max(_latest_adj, _latest_gaap)
            if _max_eps > _price_c14:
                ng.append(
                    f"  [NG-15 EPS>株価] 直近Q adj_eps={_latest_adj:.2f} gaap_eps={_latest_gaap:.2f}"
                    f" > Price=${_price_c14:.2f}"
                    f" (filing:{_latest_q.get('filing_date','?')})"
                )
            elif _max_eps > _price_c14 * 0.5:
                ng.append(
                    f"  [NG-14 EPS>株価50%] 直近Q adj_eps={_latest_adj:.2f} gaap_eps={_latest_gaap:.2f}"
                    f" > Price*0.5=${_price_c14 * 0.5:.2f}"
                    f" (filing:{_latest_q.get('filing_date','?')})"
                )

            # CHECK-16: TTM計算に使われる四半期数チェック（4件未満は不完全なTTM）
            _recent = sorted(
                [q for q in _eps_qs if q.get("filing_date", "") >= "2023-01-01"],
                key=lambda x: x.get("filing_date", ""),
                reverse=True
            )
            if 0 < len(_recent) < 4:
                warn.append(
                    f"  [WARN-16 TTM四半期不足] EPS Analyzer TTM計算に{len(_recent)}四半期しかない（4必要）"
                )

    # CHECK-17: EPS全値$0.0（BUG-EPS-ZERO-1 回帰検知）
    # 直近3年の四半期で全てadj_eps=gaap_eps=0.0の場合、株式数取得失敗の可能性
    _eps_qs_c17 = _read_eps_quarterly(ticker)
    _recent_c17 = [q for q in _eps_qs_c17 if (q.get("filing_date") or "") >= "2022-01-01"]
    if len(_recent_c17) >= 2:
        _all_adj_zero = all(abs(q.get("adjusted_eps") or 0) < 1e-9 for q in _recent_c17)
        _all_gaap_zero = all(abs(q.get("gaap_eps") or 0) < 1e-9 for q in _recent_c17)
        if _all_adj_zero and _all_gaap_zero:
            ng.append(
                f"  [NG-17 EPS全値$0.0] 直近{len(_recent_c17)}四半期すべてadj_eps=gaap_eps=0.0"
                f" → 株式数取得失敗疑い(BUG-EPS-ZERO-1 回帰)"
            )

    # CHECK-18: G=15%デフォルト未調整（DCF-DEFAULT-G-1 回帰検知）
    # recommended_gがあるのにphase1_growth_auto_adjusted=Falseかつ成長率が15%のままならWARN
    _g_c18 = latest.get("growth") or {}
    _rate_c18 = _g_c18.get("rate")
    _source_c18 = _g_c18.get("source", "")
    _rec_g_c18 = latest.get("recommended_g")
    _auto_adj_c18 = latest.get("phase1_growth_auto_adjusted", False)
    if (
        _rate_c18 is not None
        and _rec_g_c18 is not None
        and not _auto_adj_c18
        and _source_c18 != "segment_weighted"  # segment_configによる意図的設定は除外
        and abs(_rate_c18 - 0.15) < 0.002      # 15%デフォルトのまま
        and abs(_rate_c18 - _rec_g_c18) > 0.05 # recommended_gと5%以上乖離
    ):
        warn.append(
            f"  [WARN-18 G=15%デフォルト未調整] growth.rate={_rate_c18:.1%}"
            f" & recommended_g={_rec_g_c18:.1%} だがauto_adjusted=False"
            f" → DCF-DEFAULT-G-1 回帰の可能性"
        )

    # CHECK-19: SEC株数=0（BUG-EPS-ZERO-1 回帰検知）
    # 直近3年の四半期でdiluted_shares=0かつnet_income非ゼロの場合はNG
    _eps_qs_c19 = _read_eps_quarterly(ticker)
    _recent_c19 = [q for q in _eps_qs_c19 if (q.get("filing_date") or "") >= "2022-01-01"]
    _zero_shares_c19 = [
        q for q in _recent_c19
        if (q.get("gaap_net_income") or 0) != 0 and (q.get("diluted_shares") or 0) == 0
    ]
    if _zero_shares_c19:
        _dates_c19 = [q.get("filing_date", "?") for q in _zero_shares_c19[:3]]
        ng.append(
            f"  [NG-19 SEC株数=0] {len(_zero_shares_c19)}四半期でdiluted_shares=0"
            f" (例: {', '.join(_dates_c19)})"
            f" → 株式数取得失敗(BUG-EPS-ZERO-1 回帰)"
        )

    # CHECK-20: fcf_cagr floor値張り付き（GROWTH-FLOOR-VERDICT-1）
    # growth.source=fcf_cagrのままgrowth.rateがgrowth_floor(15%)に完全一致している場合に検知。
    # CHECK-18はrecommended_gがNoneの場合に構造的に発火できないため、
    # recommended_gの有無を問わずgrowth_source/rateのみで判定するのが本チェックの目的
    # （MO/LOAR/XOM等、recommended_g算出不可でfloorに落ちるケースを補完的に捕捉する）
    _g_c20 = latest.get("growth") or {}
    _rate_c20 = _g_c20.get("rate")
    _source_c20 = _g_c20.get("source", "")
    if (
        _source_c20 == "fcf_cagr"
        and _rate_c20 is not None
        and abs(_rate_c20 - 0.15) < 0.002
    ):
        warn.append(
            f"  [WARN-20 fcf_cagr floor張り付き] growth.rate={_rate_c20:.1%}"
            f" (source=fcf_cagr) がgrowth_floor(15%)に完全一致"
            f" → 実績と無関係な下駄履き値の可能性(GROWTH-FLOOR-VERDICT-1)"
        )

    # CHECK-22: fyキー競合（FY52WEEK-BUCKET-MISPLACE-1根本修正で新設）
    # parser.pyが本人データ同士のfyタグ衝突を検知した場合に記録するログを監視する。
    # tie-breakで自動解決済みのため非ブロッキングWARNとする。CRM/FCX/CAKE/HON/COHR/
    # AVAV/FICO/NVDAで実在確認済み。新規銘柄で発生した場合は本チェックで検知される。
    _collisions_c22 = _read_fy_collision_log(ticker)
    if _collisions_c22:
        _fields_c22 = sorted({c.get("field", "?") for c in _collisions_c22})
        warn.append(
            f"  [WARN-22 fyキー競合] 本人データ同士で{len(_collisions_c22)}件"
            f" (対象フィールド: {', '.join(_fields_c22[:5])}{'...' if len(_fields_c22) > 5 else ''})"
            f" → tie-breakで自動解決済み。filing代行者側のタグ付け起因と推測"
            f"（原因追及は対象外）"
        )

    # CHECK-23: fyタグ裏取り不一致（ARCH-DATA-1ステージ3で新設）
    # parser.pyが年度バケツキーと採用エントリの生fyタグの食い違いを検知した場合に
    # 記録するログを監視する。CHECK-22（同一fyタグへの複数本人end_date競合）とは
    # 独立した別軸のチェック。fy_tag_mismatch_log.json自体がis_own_data=True
    # （本人データ自身のfyタグが実際に採用されてしまっているケース）のみを対象に
    # 絞り込み済み（is_own_data=Falseの比較年度再掲エントリは、fyタグが「その数値が
    # どの10-Kに載っていたか」というfiling側の属性でしかなく企業の申告ミスとは
    # 無関係な正常仕様のため、2026-07-17に検知対象から除外した。全105銘柄検証で
    # 除外前は4,434件・105銘柄というノイズになっていた）。自動修正は行わない。
    _mismatches_c23 = _read_fy_tag_mismatch_log(ticker)
    if _mismatches_c23:
        _fields_c23 = sorted({m.get("field", "?") for m in _mismatches_c23})
        warn.append(
            f"  [WARN-23 fyタグ裏取り不一致] {len(_mismatches_c23)}件"
            f" (対象フィールド: {', '.join(_fields_c23[:5])}{'...' if len(_fields_c23) > 5 else ''})"
            f" → 本人データ自身のfyタグが年度バケツと食い違う（裏取り検知、自動修正なし）"
        )

    # CHECK-24: 決算期変更境界の年度バケツ競合（FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1）
    # parser.pyが「本人データ」と生fyタグ・end_dateの両方が異なる別エントリが
    # 同一年度バケツ（computed_year）で競合したケースを検知した場合に記録する
    # ログを監視する。CHECK-22（同一fyタグ前提）・CHECK-23（勝者自身のfyタグと
    # バケツの不一致、敗者側は対象外）のいずれとも異なる軸で、「fyタグが元々
    # 異なる2エントリが同一バケツで競合する」ケース（RCAT型、決算期変更の
    # 境界年）を対象とする。現状は_own_override_is_safe()の汎用accnベース判定
    # の副次効果で正しい値が採用されているため実害はなく、将来の実装変更等で
    # 崩れうる潜在リスクの予防的可視化が目的。自動修正は行わない。
    _collisions_c24 = _read_fye_boundary_collision_log(ticker)
    if _collisions_c24:
        _fields_c24 = sorted({c.get("field", "?") for c in _collisions_c24})
        warn.append(
            f"  [WARN-24 決算期変更境界バケツ競合] {len(_collisions_c24)}件"
            f" (対象フィールド: {', '.join(_fields_c24[:5])}{'...' if len(_fields_c24) > 5 else ''})"
            f" → 決算期変更の境界年で生fyタグ・end_dateが異なる2エントリが同一"
            f"年度バケツで競合（現状は本人データ側が正しく採用済み、自動修正なし）"
        )

    # CHECK-25: BS項目None検知（FY52WEEK-BS-NULL-SILENT-1 Phase A）
    # total_assets/total_liabilities/stockholders_equity/current_assets/
    # current_liabilities/cash_and_equivalentsは全105銘柄実測でNone率が
    # ほぼ0-4%（ほぼ確実にデータ異常のシグナル）。従来はreader.py::
    # get_net_cash()等の計算経路で`or 0`により静かに$0化され検知不能
    # だった。最新年度annual_YYYY.jsonを直接参照し、対象フィールドの
    # 欠損を明示的に検知する（report.txt/latest.jsonの生成有無に依存
    # しない独立チェック）。short_term_investments/long_term_debt/
    # short_term_debt（真のゼロとの判別困難）・rpo（非SaaS銘柄はNoneが
    # 正常）はPhase B/Cとして対象外。
    _bs_c25, _period_c25 = _read_latest_annual_bs(ticker)
    if _bs_c25:
        _none_fields_c25 = [f for f in _BS_NULL_CHECK_FIELDS if _bs_c25.get(f) is None]
        if _none_fields_c25:
            warn.append(
                f"  [WARN-25 BS項目None] FY{_period_c25}: {', '.join(_none_fields_c25)}"
                f" が欠損 → 計算経路でNoneが暗黙に0化されている可能性"
                f"（FY52WEEK-BS-NULL-SILENT-1 Phase A、要確認）"
            )

    # CHECK-26: BS項目「前年値あり→当年None」遷移検知
    # （BS-FIELD-NONE-TRANSITION-DETECT-1）
    # WARN-25（ブランケット型、total_assets等6フィールド対象）とは独立した
    # 別軸のチェック。short_term_investments/long_term_debt/short_term_debt/
    # rpo（WARN-25がNone率過多〈35〜65%〉を理由に対象外とした4フィールド）は
    # 「Noneであること自体」の検知には向かないが、「前年は値があったのに
    # 当年からNoneになる」という**遷移**は正常な企業では発生しないため、
    # WARN-25とは別のブランケット型不採用理由（ノイズの多さ）が当てはまらない。
    #
    # 会計年度の連続性に関する注意（FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1関連）:
    # files[-2]/files[-1]の2ファイルを機械的に「1年前・当年」とみなさず、
    # 双方のperiod（fyラベル）の年度差が厳密に1であることを確認したうえで
    # のみ判定する。決算期変更の境界年（例: RCATは2019年・2024-2025年に
    # 決算期を変更済み、FYE-CHANGE-BOUNDARY-COLLISION-BLIND-1参照）では
    # periodラベルが連続していても、files[-2]が真の「1年前」の期間を
    # 表さない場合があり得る（スタブ期間の混入等）。年度差が1でない場合は
    # 判定不能として発火させない（誤判定より見逃しを優先する設計）。
    # 新規登録銘柄（annual_*.jsonが1年分のみ）も同様に対象外。
    #
    # 事前調査（NVDA-STI-TAG-UNIDENTIFIED-1調査時の体制確認、BS-FIELD-NONE-
    # TRANSITION-DETECT-1）で、FY52WEEK-BS-NULL-SILENT-1「生涯フェードアウト」
    # 25件のうち8件（APP/BKNG/CPRT/DOCN/ENTG/KULR/MSCI/SOUN）が実装直後の
    # 直近2年度比較で発火することが判明済み。いずれも一次情報（10-K原本）で
    # 真の無借金/無投資継続と確認済みのため、warn_acknowledged.jsonへ事前
    # 登録し初回実行時のアラート疲れを回避する。
    _TRANSITION_CHECK_FIELDS = ["short_term_investments", "long_term_debt", "short_term_debt", "rpo"]
    _ann_files_c26 = sorted(glob.glob(os.path.join(SEC_DATA_DIR, ticker, "annual_*.json")))
    if len(_ann_files_c26) >= 2:
        try:
            with open(_ann_files_c26[-1], encoding="utf-8") as _f26_latest:
                _ann_latest26 = json.load(_f26_latest)
            with open(_ann_files_c26[-2], encoding="utf-8") as _f26_prior:
                _ann_prior26 = json.load(_f26_prior)
            _latest_period26 = _ann_latest26.get("period")
            _prior_period26 = _ann_prior26.get("period")
            try:
                _year_diff26 = int(_latest_period26) - int(_prior_period26)
            except (TypeError, ValueError):
                _year_diff26 = None
            if _year_diff26 == 1:
                _latest_bs26 = _ann_latest26.get("bs", {}) or {}
                _prior_bs26 = _ann_prior26.get("bs", {}) or {}
                _transitioned26 = [
                    f for f in _TRANSITION_CHECK_FIELDS
                    if _prior_bs26.get(f) is not None and _latest_bs26.get(f) is None
                ]
                if _transitioned26:
                    warn.append(
                        f"  [WARN-26 BS項目遷移(有値→None)] FY{_prior_period26}→FY{_latest_period26}: "
                        f"{', '.join(_transitioned26)} が前年値あり→当年Noneに遷移"
                        f"（タグ申告停止の可能性。生涯フェードアウト〈真のゼロ継続〉の"
                        f"場合はwarn_acknowledged.jsonへ登録すること）"
                    )
        except Exception:
            pass

    # CHECK-27: cross_filing_tags近似値の残差率閾値超過検知
    # （NVDA-STI-TAG-UNIDENTIFIED-1・ANOMALY-PATTERN-CATALOG-1型C対応）
    # parser.py::_apply_cross_filing_tags()が付与するbs_provenance[field].
    # is_approximated=Trueのエントリを対象に、residual_pctが閾値（5%）を
    # 超える場合のみ発火する。NVDA（+0.88%）等の既知の合算近似値は許容範囲内
    # のため通常は発火しない。将来同型（型C）を別銘柄に適用した際、想定外に
    # 大きな乖離が生じていないかの安全網。
    _RESIDUAL_PCT_THRESHOLD = 0.05
    _ann_files_c27 = sorted(glob.glob(os.path.join(SEC_DATA_DIR, ticker, "annual_*.json")))
    if _ann_files_c27:
        try:
            with open(_ann_files_c27[-1], encoding="utf-8") as _f27:
                _ann27 = json.load(_f27)
            _prov27 = _ann27.get("bs_provenance", {}) or {}
            _period27 = _ann27.get("period", "")
            for _field27, _fp27 in _prov27.items():
                if not isinstance(_fp27, dict) or not _fp27.get("is_approximated"):
                    continue
                _residual27 = _fp27.get("residual_pct")
                if _residual27 is not None and abs(_residual27) > _RESIDUAL_PCT_THRESHOLD:
                    warn.append(
                        f"  [WARN-27 近似値残差過大] FY{_period27} {_field27}: "
                        f"cross_filing_tags合算値の残差{_residual27*100:+.1f}%が"
                        f"閾値({_RESIDUAL_PCT_THRESHOLD*100:.0f}%)を超過 → 合算元タグ"
                        f"（{', '.join(_fp27.get('combined_tags', []))}）の妥当性を要確認"
                    )
        except Exception:
            pass

    # CHECK-28: 10-KT/10-QT除外検知（[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]）
    # fetcher.py::_fetch_submissions_for_cik()のrelevant_formsに10-KT・
    # 10-QT（決算期変更移行期報告書）が含まれておらず、該当formのaccnが
    # accn_to_reportdateに登録されないため、is_own_data判定が恒常的に
    # Falseになり本人データが年次バケツ争いで採用されない構造的欠落を
    # 直接検知する。WARN-24〈決算期変更境界バケツ競合〉はこの欠落が
    # 引き起こす症状〈バケツ競合〉を検知するのに対し、本WARNは根本原因
    # 〈10-KT/10-QT自体の除外〉を直接検知する別軸。自動修正なし、検知のみ。
    _cf_path_c28 = os.path.join(SEC_DATA_DIR, ticker, "company_facts.json")
    if os.path.exists(_cf_path_c28):
        try:
            with open(_cf_path_c28, encoding="utf-8") as _f28:
                _cf28 = json.load(_f28)
            _facts28 = _cf28.get("facts", {}).get("us-gaap", {})
            _transition_forms28 = {"10-KT", "10-QT"}
            _transition_accns28: dict = {}
            for _tagdata28 in _facts28.values():
                for _entries28 in _tagdata28.get("units", {}).values():
                    for _e28 in _entries28:
                        _accn28 = _e28.get("accn")
                        _form28 = _e28.get("form")
                        if _accn28 and _form28 in _transition_forms28:
                            _transition_accns28.setdefault(_accn28, (_form28, _e28.get("end")))
            if _transition_accns28:
                _accn_reportdate28 = load_submissions(ticker, data_dir=SEC_DATA_DIR)
                for _accn28, (_form28, _end28) in sorted(_transition_accns28.items()):
                    if _accn28 not in _accn_reportdate28:
                        warn.append(
                            f"  [WARN-28 10-KT/10-QT除外] accn={_accn28} form={_form28} "
                            f"end={_end28} → accn_to_reportdateに未登録のため本人データ"
                            f"判定の対象外（fetcher.py relevant_forms除外、"
                            f"[[FETCHER-10KT-10QT-FORM-EXCLUSION-1]]、自動修正なし）"
                        )
        except Exception:
            pass

    # CHECK-29: 会計恒等式Total_Assets=Total_Liabilities+Stockholders_
    # Equity（+NCI+一時的持分）検知（[[CHECK29-ACCOUNTING-IDENTITY-
    # DETECTION-LAYER-1]]）。parser.pyが①本体一致・②NCI/一時的持分を加算
    # した拡張形一致（許可リスト方式、OR条件フォールバック）のいずれでも
    # 解消しなかったケースを検知した際に書き出すログを監視する。①で解消
    # したケース・②拡張形で解消したケースはparser.py側で記録対象外済み
    # （ノイズ削減）のため、ここで発火するのはいずれでも未解消のケースのみ。
    # 自動修正は行わない。
    _violations_c29 = _read_bs_identity_violations_log(ticker)
    _unresolved_c29 = [v for v in _violations_c29 if not v.get("resolved_by_extension")]
    if _unresolved_c29:
        _periods_c29 = sorted({str(v.get("period", "?")) for v in _unresolved_c29})
        warn.append(
            f"  [WARN-29 会計恒等式不成立] {len(_unresolved_c29)}件"
            f" (対象年度: {', '.join(_periods_c29[:5])}{'...' if len(_periods_c29) > 5 else ''})"
            f" → Total_Assets=Total_Liabilities+Stockholders_Equity"
            f"（NCI・一時的持分の許可リスト加算を含む拡張形でも）が成立しない"
            f"（自動修正なし、[[CHECK29-UNRESOLVED-23-MIXED-CAUSES-1]]参照）"
        )

    return ng, warn


# ─── CLI ─────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="TANUKI VALUATION report.txt 整合性チェック"
    )
    parser.add_argument(
        "--fail-on-ng",
        action="store_true",
        help="NG件数 > 0 のとき sys.exit(1) で終了する（省略時は常にexit(0)）",
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default=None,
        help="チェック対象銘柄（カンマ区切り可。例: NVDA または NVDA,AAPL）",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="PASS行を表示しない（NGとWARNのみ出力）",
    )
    return parser.parse_args()


# ─── メイン ──────────────────────────────────────────────────

def run_checks(args=None) -> tuple[int, int]:
    """整合性チェックを実行し (ng_count, warn_count) を返す。"""
    whitelist = _load_rpo_whitelist()
    warn_ledger = load_warn_ledger()
    quiet = getattr(args, "quiet", False)
    ticker_filter = None
    if args and args.ticker:
        ticker_filter = {t.strip().upper() for t in args.ticker.split(",")}

    # FLAG-CONSUMER-AUDIT-2: 以前はos.listdir(DATA_DIR)でtanukiフラグを見ず
    # ディレクトリ実在＋report.txt存在だけでスキャン対象を決めており、
    # tanuki=false化済みだがreport.txtが残存する銘柄（ZS・RKLB等）が
    # スキャン対象に混入していた（ZS-TICKERS-LEAK-1参照）。
    # tickers.get_tanuki_tickers()との積集合に限定する。
    all_tickers = sorted([
        t for t in _tickers_mod.get_tanuki_tickers()
        if os.path.exists(os.path.join(DATA_DIR, t, "report.txt"))
    ])

    if ticker_filter:
        tickers = [t for t in all_tickers if t in ticker_filter]
    else:
        tickers = all_tickers

    if not quiet:
        print(f"=== TANUKI VALUATION report.txt 整合性チェック ({len(tickers)} 銘柄) ===\n")

    total_ng        = 0
    total_warn      = 0
    total_warn_new  = 0
    flagged: list[tuple[str, list, list]] = []

    for ticker in tickers:
        ng, warn = check_ticker(ticker, whitelist)
        annotated_warn = []
        for w in warn:
            msg, is_new = annotate_warn(ticker, w, warn_ledger)
            annotated_warn.append(msg)
            if is_new:
                total_warn_new += 1
        if ng or annotated_warn:
            flagged.append((ticker, ng, annotated_warn))
            total_ng   += len(ng)
            total_warn += len(annotated_warn)

    # CHECK-32: ティッカー非依存の単発チェック（discover_config/theme_config同期）。
    # --tickerフィルタの有無に関わらず常時実行する（ticker単位のデータとは
    # 無関係な、config/とdocs/の同期状態そのものを検証するため）。
    discover_sync_ng = _check_discover_config_sync()
    if discover_sync_ng:
        flagged.append(("[GLOBAL]", discover_sync_ng, []))
        total_ng += len(discover_sync_ng)

    # CHECK-34: ティッカー非依存の単発チェック（config/設定ファイル読み込み
    # の横断解決チェック、_CONFIG_LOADER_REGISTRY駆動）。
    # CHECK-32と同様、--tickerフィルタの有無に関わらず常時実行する。
    config_loader_ng = _check_config_loaders_resolvable()
    if config_loader_ng:
        flagged.append(("[GLOBAL]", config_loader_ng, []))
        total_ng += len(config_loader_ng)

    if not flagged:
        if not quiet:
            print("✅ 全銘柄整合 — NG=0 / 警告=0\n")
    else:
        for ticker, ng, warn in flagged:
            icon = "❌" if ng else "⚠️"
            print(f"{icon} {ticker}")
            for item in ng:
                print(item)
            for item in warn:
                print(item)
            print()

    if not quiet:
        print("─" * 50)
        total_warn_ack = total_warn - total_warn_new
        print(
            f"合計: NG={total_ng} 件 / 警告={total_warn} 件"
            f"（確認済み{total_warn_ack} / \U0001f195未確認{total_warn_new}）"
            f"  (対象 {len(tickers)} 銘柄)"
        )
        if total_ng == 0:
            print("✅ NG=0 全銘柄整合")
        if total_warn_new > 0:
            print(f"⚠️  未確認WARNが{total_warn_new}件あります。台帳（{WARN_LEDGER}）で確認要否を判断してください。")

    return total_ng, total_warn


if __name__ == "__main__":
    args = parse_args()
    ng_count, warn_count = run_checks(args)

    print(f"\n{'='*50}")
    print(f"結果: NG={ng_count}件 / WARN={warn_count}件")

    if args.fail_on_ng and ng_count > 0:
        print("❌ ゲート失敗: NGが存在するためexit(1)で終了します")
        sys.exit(1)
    else:
        print("✅ ゲート通過")
        sys.exit(0)
