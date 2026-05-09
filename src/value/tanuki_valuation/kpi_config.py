"""
TANUKI VALUATION - KPI Configuration
銘柄別KPI定義

責務:
  - 各銘柄のセグメント構成を定義（SEC EDGAR取得時のセグメント名マッピング）
  - 財務KPI（A案: SEC自動取得）の定義
  - 非財務KPI（B案: 将来手動設定）のスキーマ予約

設計方針:
  - segment_config.py（成長率・ウェイト設定）とは完全分離
  - kpi_fetcher.py がこの定義を参照してSEC EDGARから取得
  - latest.json の "kpi_data" フィールドに出力される

追加方法:
  1. KPI_DEFINITIONS に銘柄エントリを追加
  2. segments にSEC 10-K記載のセグメント名を列挙
  3. kpi_fetcher.py を実行して取得テストを行う
"""

from typing import Dict, Any, List, Optional


# ============================================================
# セグメント別KPI定義
# ============================================================
# segments: SEC 10-Kに記載されているセグメント名（XBRL検索キー）
# fiscal_year_end: 決算月（SEC XBRL取得時の年度確定に使用）
# revenue_unit: 売上高の単位（表示用）
#
# financial_kpis: A案で取得する財務KPI
#   - "segment_revenue": セグメント別売上高（必須）
#   - "segment_operating_income": セグメント別営業利益（可能な場合）
#
# operational_kpis: B案で追加する非財務KPI（現在は空リスト・将来拡張用）
#   各KPIは {"name": str, "unit": str, "source": str, "values": {}} の形式
# ============================================================

KPI_DEFINITIONS: Dict[str, Dict[str, Any]] = {

    # ── NVIDIA ──
    # XBRLセグメント構造（FY2025 10-K調査結果）:
    #   nvda:ComputeAndNetworkingSegmentMember → Compute and Networking
    #   nvda:GraphicsSegmentMember             → Graphics
    # ※ Data Center/Gaming等の細分類はXBRLタグなし（表形式のみ開示）
    "NVDA": {
        "fiscal_year_end": 1,       # 1月末決算
        "revenue_unit": "B USD",
        "segments": [
            "Compute and Networking",
            "Graphics",
        ],
        # XBRL Instance Document (_htm.xml) のMember名マッピング
        # FY2025/2026: SegmentMember（新形式）
        # FY2024以前:  Member（旧形式、"Segment"なし）
        "xbrl_members": {
            "nvda:ComputeAndNetworkingSegmentMember": "Compute and Networking",
            "nvda:GraphicsSegmentMember":             "Graphics",
            "nvda:ComputeAndNetworkingMember":        "Compute and Networking",
            "nvda:GraphicsMember":                    "Graphics",
        },
        "financial_kpis": [
            "segment_revenue",
            "segment_operating_income",
        ],
        "operational_kpis": [
            # B案: 将来追加予定
            # {"name": "Data Center GPU出荷数", "unit": "万基", "source": "manual"},
        ],
        "notes": "FY=翌年1月末。FY2025=2025年1月期。XBRLは2セグメント開示。",
    },

    # ── Tesla ──
    "TSLA": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [
            "Automotive",
            "Energy Generation and Storage",
            "Services and Other",
        ],
        "financial_kpis": [
            "segment_revenue",
            "segment_operating_income",
        ],
        "operational_kpis": [
            # {"name": "車両納車台数", "unit": "千台", "source": "manual"},
            # {"name": "エネルギー展開量", "unit": "GWh", "source": "manual"},
        ],
        "notes": "12月末決算。",
    },

    # ── Palantir ──
    "PLTR": {
        "fiscal_year_end": 12,
        "revenue_unit": "M USD",
        "segments": [
            "Government",
            "Commercial",
        ],
        "financial_kpis": [
            "segment_revenue",
            "segment_operating_income",
        ],
        "operational_kpis": [
            # {"name": "顧客数（商業）", "unit": "社", "source": "manual"},
            # {"name": "ARR（商業）", "unit": "M USD", "source": "manual"},
        ],
        "xbrl_members": {
            "pltr:GovernmentOperatingSegmentMember": "Government",
            "pltr:CommercialMember":                 "Commercial",
        },
        "notes": "12月末決算。US/International はXBRL別軸で開示。",
    },

    # ── Microsoft ──
    "MSFT": {
        "fiscal_year_end": 6,       # 6月末決算
        "revenue_unit": "B USD",
        "segments": [
            "Intelligent Cloud",
            "Productivity and Business Processes",
            "More Personal Computing",
        ],
        "financial_kpis": [
            "segment_revenue",
            "segment_operating_income",
        ],
        "operational_kpis": [
            # {"name": "Azure成長率（YoY）", "unit": "%", "source": "manual"},
            # {"name": "Microsoft 365 商業シート数", "unit": "M", "source": "manual"},
        ],
        "notes": "6月末決算。FY2025=2025年6月期。",
    },

    # ── Amazon ──
    "AMZN": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [
            "North America",
            "International",
            "AWS",
        ],
        "financial_kpis": [
            "segment_revenue",
            "segment_operating_income",
        ],
        "operational_kpis": [
            # {"name": "Primeメンバー数", "unit": "M", "source": "manual"},
            # {"name": "広告売上高", "unit": "B USD", "source": "manual"},
        ],
        "notes": "North America/International/AWS の3セグメント。",
    },

    # ── AMD ──
    "AMD": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [
            "Data Center",
            "Client",
            "Gaming",
            "Embedded",
            "Client and Gaming",  # FY2025: Client+GamingをXBRLで統合開示
            "All Other",
        ],
        "financial_kpis": [
            "segment_revenue",
            "segment_operating_income",
        ],
        "operational_kpis": [],
        "notes": "12月末決算。FY2025はClient/GamingがXBRLで統合。",
    },

    # ── AppLovin ──
    "APP": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [
            "Software Platform",
            "Apps",
        ],
        "financial_kpis": [
            "segment_revenue",
            "segment_operating_income",
        ],
        "operational_kpis": [],
        "notes": "2024年にAppsセグメントの一部を売却済み。",
    },

    # ── Celsius ──
    "CELH": {
        "fiscal_year_end": 12,
        "revenue_unit": "M USD",
        "segments": [
            "North America",
            "International",
        ],
        "financial_kpis": [
            "segment_revenue",
        ],
        "operational_kpis": [],
        "xbrl_members": {},  # 単一セグメントのため取得不可
        "notes": "12月末決算。地域別はXBRLタグなし・手動設定が必要。",
    },

    # ── SoFi ──
    "SOFI": {
        "fiscal_year_end": 12,
        "revenue_unit": "M USD",
        "segments": [
            "Lending",
            "Technology Platform",
            "Financial Services",
        ],
        "financial_kpis": [
            "segment_revenue",
            "segment_operating_income",
        ],
        "operational_kpis": [
            # {"name": "会員数", "unit": "万人", "source": "manual"},
            # {"name": "プロダクト数", "unit": "万件", "source": "manual"},
            # {"name": "調整後EBITDA", "unit": "M USD", "source": "manual"},
        ],
        "xbrl_members": {
            "sofi:LendingSegmentMember":            "Lending",
            "sofi:TechnologyPlatformSegmentMember": "Technology Platform",
            "sofi:FinancialServicesSegmentMember":  "Financial Services",
        },
        "notes": "12月末決算。金融業のため営業利益の定義に注意。",
    },

    # ── Rocket Lab ──
    "RKLB": {
        "fiscal_year_end": 12,
        "revenue_unit": "M USD",
        "segments": [
            "Launch Services",
            "Space Systems",
        ],
        "financial_kpis": [
            "segment_revenue",
        ],
        "operational_kpis": [
            # {"name": "打ち上げ回数", "unit": "回", "source": "manual"},
            # {"name": "受注残（バックログ）", "unit": "M USD", "source": "manual"},
        ],
        "notes": "セグメント別利益は未開示が多い。",
    },

    # ── SoundHound ──
    "SOUN": {
        "fiscal_year_end": 12,
        "revenue_unit": "M USD",
        "segments": [
            # セグメント開示なし（単一セグメント）
        ],
        "financial_kpis": [
            "segment_revenue",   # 全社売上のみ
        ],
        "operational_kpis": [
            # {"name": "ARR", "unit": "M USD", "source": "manual"},
        ],
        "notes": "単一セグメント。全社売上高のみ取得。",
    },
    # ── Ondas Holdings ──
    # 単一セグメント開示（XBRLタグなし）
    "ONDS": {
        "fiscal_year_end": 12,
        "revenue_unit": "M USD",
        "segments": [],
        "xbrl_members": {},  # 単一セグメントのため取得不可
        "financial_kpis": ["segment_revenue"],
        "operational_kpis": [],
        "notes": "12月末決算。単一セグメント開示。",
    },

    # ── CoreWeave ──
    "CRWV": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [],
        "xbrl_members": {},
    },
    "META": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [],
        "financial_kpis": ["segment_revenue"],
        "operational_kpis": [],
        "notes": "デフォルト設定。セグメント情報に基づいて更新してください。",
    },
    "APPL": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [],
        "financial_kpis": ["segment_revenue"],
        "operational_kpis": [],
        "notes": "デフォルト設定。セグメント情報に基づいて更新してください。",
    },
    "AAPL": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [],
        "financial_kpis": ["segment_revenue"],
        "operational_kpis": [],
        "notes": "デフォルト設定。セグメント情報に基づいて更新してください。",
    },
    "NOW": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [],
        "financial_kpis": ["segment_revenue"],
        "operational_kpis": [],
        "notes": "デフォルト設定。セグメント情報に基づいて更新してください。",
    },
    "RCAT": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [],
        "financial_kpis": ["segment_revenue"],
        "operational_kpis": [],
        "notes": "デフォルト設定。セグメント情報に基づいて更新してください。",
    },
    "VWAV": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [],
        "financial_kpis": ["segment_revenue"],
        "operational_kpis": [],
        "notes": "デフォルト設定。セグメント情報に基づいて更新してください。",
    },
    "AUR": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [],
        "financial_kpis": ["segment_revenue"],
        "operational_kpis": [],
        "notes": "デフォルト設定。セグメント情報に基づいて更新してください。",
    },
    "XNDU": {
        "fiscal_year_end": 12,
        "revenue_unit": "B USD",
        "segments": [],
        "financial_kpis": ["segment_revenue"],
        "operational_kpis": [],
        "notes": "デフォルト設定。セグメント情報に基づいて更新してください。",
    },
}


# ============================================================
# latest.json の "kpi_data" スキーマ（参照用）
# ============================================================
# kpi_fetcher.py がこの構造で出力する。
#
# "kpi_data": {
#   "fetched_at": "2026-04-25",
#   "source": "SEC EDGAR XBRL",
#   "segments": {
#     "Data Center": {
#       "revenue": {
#         "FY2023": 18400000000,
#         "FY2024": 47500000000,
#         "FY2025": 115200000000,
#         "FY2026_est": null,   # A案では null（B案で手動設定）
#         "FY2027_est": null,
#         "FY2028_est": null,
#       },
#       "operating_income": {
#         "FY2023": ...,
#         ...
#       },
#       "operating_margin": {   # revenue / operating_income から自動計算
#         "FY2023": 0.52,
#         ...
#       },
#       "yoy_growth": {         # 自動計算
#         "FY2024": 1.582,      # +158.2%
#         "FY2025": 1.426,      # +142.6%
#       }
#     },
#     ...
#   },
#   "total_revenue": {          # セグメント合計（検証用）
#     "FY2023": ...,
#     ...
#   },
#   "errors": []                # 取得失敗セグメントのログ
# }
# ============================================================


def get_kpi_definition(ticker: str) -> Optional[Dict[str, Any]]:
    """銘柄のKPI定義を取得"""
    return KPI_DEFINITIONS.get(ticker)


def get_segments(ticker: str) -> List[str]:
    """銘柄のセグメントリストを取得"""
    defn = KPI_DEFINITIONS.get(ticker)
    if not defn:
        return []
    return defn.get("segments", [])


def has_kpi_definition(ticker: str) -> bool:
    """KPI定義が存在するか"""
    return ticker in KPI_DEFINITIONS


if __name__ == "__main__":
    print("=== KPI定義確認 ===\n")
    for ticker, defn in KPI_DEFINITIONS.items():
        segs = defn.get("segments", [])
        kpis = defn.get("financial_kpis", [])
        op_kpis = defn.get("operational_kpis", [])
        print(f"{ticker:6}: セグメント{len(segs)}件  財務KPI={kpis}  非財務KPI予約={len(op_kpis)}件")
        for s in segs:
            print(f"         - {s}")
