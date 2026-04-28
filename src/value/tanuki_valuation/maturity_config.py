"""
TANUKI VALUATION - Maturity Profile Configuration v8.0
銘柄別成熟曲線パラメータ設定

v8.0 変更点:
  - 設定値を config/maturity_config.json から読み込む
  - ハードコードの MATURITY_PROFILES を廃止
  - 後方互換: get_maturity_profile() / is_three_stage() / get_terminal_growth() のAPIは変更なし
  - フォールバック: JSONが存在しない場合は two_stage をデフォルトとして返す

成熟タイプ:
  "three_stage" : Phase1（高成長）→ Phase2（移行）→ ターミナル
  "two_stage"   : 既存モデルと同一（デフォルト）

phase1.growth = null の場合は segment_config の加重平均成長率を流用する。

設定変更方法:
  - admin.html（docs/value-monitor/admin.html）からフォーム入力
  - GitHub API経由で config/maturity_config.json を更新
  - ローカル直接編集は非推奨（admin.htmlを使用すること）
"""

import json
import os
from typing import Dict, Any


# ============================================================
# JSON設定ファイルの読み込み
# ============================================================

def _find_config_dir() -> str:
    """config/ ディレクトリを探す"""
    workspace = os.environ.get("GITHUB_WORKSPACE", "")
    if workspace:
        path = os.path.join(workspace, "config")
        if os.path.isdir(path):
            return path

    current = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(current)))
    path = os.path.join(repo_root, "config")
    if os.path.isdir(path):
        return path

    raise FileNotFoundError(
        "config/ ディレクトリが見つかりません。"
        "migrate_config_to_json.py を実行してください。"
    )


_DEFAULT_PROFILE: Dict[str, Any] = {
    "type": "two_stage",
    "terminal_growth": 0.03
}

_MATURITY_CONFIG: Dict[str, Any] = {}


def _ensure_loaded() -> None:
    """設定が未ロードなら読み込む（遅延初期化）"""
    global _MATURITY_CONFIG
    if not _MATURITY_CONFIG:
        try:
            config_dir = _find_config_dir()
            path = os.path.join(config_dir, "maturity_config.json")
            with open(path, encoding="utf-8") as f:
                _MATURITY_CONFIG = json.load(f)
        except FileNotFoundError as e:
            print(f"[ERROR] maturity_config.json が見つかりません: {e}")
            _MATURITY_CONFIG = {"_default": _DEFAULT_PROFILE.copy()}
        except json.JSONDecodeError as e:
            print(f"[ERROR] maturity_config.json のJSON解析エラー: {e}")
            _MATURITY_CONFIG = {"_default": _DEFAULT_PROFILE.copy()}


def reload_config() -> None:
    """設定を強制再読み込み（テスト・デバッグ用）"""
    global _MATURITY_CONFIG
    _MATURITY_CONFIG = {}
    _ensure_loaded()


# ============================================================
# 公開API（既存コードとの後方互換を維持）
# ============================================================

def get_maturity_profile(ticker: str) -> Dict[str, Any]:
    """
    銘柄の成熟プロファイルを取得

    Args:
        ticker: 銘柄コード

    Returns:
        成熟プロファイルのdict（未定義の場合は _default を返す）
    """
    _ensure_loaded()
    profile = _MATURITY_CONFIG.get(ticker)
    if profile is None or ticker.startswith("_"):
        default = _MATURITY_CONFIG.get("_default", _DEFAULT_PROFILE)
        return default.copy()
    return profile.copy()


def is_three_stage(ticker: str) -> bool:
    """3段階DCFを使用するか判定"""
    profile = get_maturity_profile(ticker)
    return profile.get("type") == "three_stage"


def get_terminal_growth(ticker: str) -> float:
    """銘柄のターミナル成長率を取得"""
    profile = get_maturity_profile(ticker)
    return profile.get("terminal_growth", 0.03)


if __name__ == "__main__":
    print("=== Maturity Profile（JSON読み込み版）===\n")
    tickers = ["NVDA", "TSLA", "PLTR", "MSFT", "AMZN", "AMD", "APP", "CELH", "UNKNOWN"]
    for ticker in tickers:
        profile = get_maturity_profile(ticker)
        ptype = profile.get("type")
        if ptype == "three_stage":
            p1 = profile["phase1"]
            p2 = profile["phase2"]
            tg = profile["terminal_growth"]
            g1 = f"{p1['growth']:.0%}" if p1.get("growth") else "segment_weighted"
            print(f"{ticker:6}: three_stage  P1={p1['years']}yr@{g1}  P2={p2['years']}yr@{p2['growth']:.0%}  TV={tg:.1%}")
        else:
            print(f"{ticker:6}: two_stage (既存モデル)")
